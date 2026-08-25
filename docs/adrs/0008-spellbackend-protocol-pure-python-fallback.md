# ADR-0008: Spell-check behind a `SpellBackend` protocol with a pure-Python fallback

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`DictionaryManager` (`helpers/tools/spellchecker/dictionary_manager.py`) couples spell checking
tightly to `pyenchant` and to package-relative filesystem state. `_setup_paths`
(lines 36-41) computes `self.path_dictionary = Path(__file__).resolve().parents[3] / "static" /
"dictionaries"` (line 32) and then, at line 41, sets `os.environ["ENCHANT_CONFIG_DIR"] =
str(enchant_config_dir)` — a **global, process-wide** environment mutation pointed at a directory
*inside the installed package*, not a per-run temporary location (SEC-007, ARC-002). Fully
initializing a dictionary (`initialize_dictionary`, lines 58-85) adds user-supplied words with
`self.dictionary.add(word)` for each word (line 81) and extra words from a bundled file
(`_load_extra_words`, lines 87-107, `self.dictionary.add(word)` at line 101) — Enchant persists
`.add()`ed words to on-disk personal-dictionary files (`<lang>.dic`/`.exc`) under that same
package-relative `path_dictionary`, meaning **a package directory is written to at spell-check
time** (violating the "nothing written inside the package" pillar in `CLAUDE.md` §1 and TOOL-008).
Cleanup is attempted in `clean_temporary_files` (lines 117-149) and in `__del__` (lines 109-115,
itself wrapped in a bare `except Exception: pass`), which unlinks
`self.path_dictionary / f"{self.lang_dict_spell}.dic"` and `.exc` (lines 140-142) — but destructor
timing in CPython is not guaranteed, so a crash, a `kill -9`, or simply two runs overlapping on a
shared server (this tool runs as a CLI on a shared server, per the security threat model in
`02-security.md`) can leave stale files behind, or let one run's leftover custom words leak into
another concurrently running validation of a *different* spreadsheet bundle — a correctness and
tenant-isolation bug, not just an environment-hygiene one. `validate_dictionary`
(lines 43-56) also swallows every failure into a broad `except Exception as e:` (line 53),
consistent with the SEC-004 pattern found across the codebase. Separately, BUG-023 notes the spell
dictionary language comes from the CLI argument while the UI/message language comes from the
`store.locale` file (`language_manager.py`) — two independent sources of "what language are we in"
that can disagree.

## Decision

Introduce a `SpellBackend` Protocol, as specified in `.specs/architecture/target-architecture.md`:
```python
class SpellBackend(Protocol):
    language: str
    def check(self, word: str) -> bool: ...
    def add_session_words(self, words: Iterable[str]) -> None: ...
```
`EnchantBackend` implements it using `dictionary.add_to_session()` (session-scoped, in-memory,
never persisted to disk) instead of `dictionary.add()`; if `ENCHANT_CONFIG_DIR` must still be set
for Enchant to find hunspell dictionaries, it points at a per-run
`tempfile.TemporaryDirectory()` created and torn down inside a context manager for the duration of
one validation run — never a package-relative path, never a bare `os.environ[...] = ...` left
mutated for the rest of the process. A `PurePythonBackend` (built on `symspellpy` or
`pyspellchecker`, loading the bundled `.dic` wordlists) satisfies the same protocol and is selected
automatically when `pyenchant`/system hunspell is unavailable, or explicitly via a `[spell]` extra
policy — closing ARC-015's "tests need the library installed, Windows requires manual DLLs" gap for
environments that can't or don't want the C-extension dependency. Word-level results are cached
(`functools.lru_cache` or an explicit dict keyed by `(language, word)`) to avoid re-checking
duplicate tokens across a large sheet (PERF-006). The spell-check language and the UI/message
locale are unified into the single `Locale` value carried by `AppContext` (ADR-0005), removing the
BUG-023 dual-source problem.

## Consequences

### Positive
- No package files are written or deleted at spell-check time; a read-only install (a common
  packaging expectation, TOOL-008) works without special-casing.
- Concurrent runs on the shared validation server can no longer leak custom words between
  unrelated spreadsheet bundles, since session words never touch shared on-disk state.
- Environments without system hunspell/Enchant (e.g. minimal CI containers, some Windows setups)
  get a working pure-Python fallback instead of failing to import or requiring manual DLL setup.

### Negative
- The pure-Python fallback's dictionary coverage and accuracy for pt-BR are unlikely to match
  hunspell's mature linguistic data exactly; this is accepted as a deliberate quality/availability
  trade-off for environments lacking Enchant, not a silent regression — `EnchantBackend` remains
  the default when available.
- `add_to_session()` semantics must be re-verified against the current `.add()` behaviour (does a
  session word affect only the current `Dict` instance, as intended, with no cross-run leakage) as
  part of the Phase 5 migration, with a regression test asserting isolation between two
  same-process `SpellBackend` instances.

## Alternatives considered

### Keep `pyenchant` only, fix cleanup with `atexit`/a context manager instead of `__del__`
Rejected: this still leaves a package-relative write for every custom word (Enchant's own on-disk
persistence for `.add()`), still requires system hunspell + Windows DLLs for every contributor and
CI runner, and does not solve the global `os.environ["ENCHANT_CONFIG_DIR"]` mutation — the
`add_to_session()` + protocol-behind-an-abstraction approach removes the root causes rather than
tightening cleanup timing around them.

### Switch to a cloud/API-based spell-checking service
Rejected outright: the threat model (`02-security.md`) explicitly treats spreadsheet content as
**untrusted, sector-uploaded data**; sending cell text to an external API would be a data-exfiltration
risk this project cannot accept, and it would add a network dependency and latency to what is
otherwise an offline CLI tool.

### Drop `pyenchant`/hunspell entirely, ship only the pure-Python backend
Rejected: hunspell's pt-BR/en-US dictionaries are materially more complete than what
`symspellpy`/`pyspellchecker` ship out of the box, and this is a currently-working feature (spelling
validation is one of the ~35 protocol checks); removing the higher-quality backend to simplify
packaging would be a real accuracy regression for INPE staff reviewing reports, not just a
technical simplification — hence "protocol with two implementations, best available chosen
automatically" rather than a single fallback-only implementation.

## Links

- Backlog: `ARC-015` (`03-architecture.md`); `BUG-022`, `BUG-023` (`01-bugs.md`);
  `SEC-007` (`02-security.md`); `PERF-006` (`05-performance.md`);
  `08-migration-roadmap.md` Phase 5 item 1
- Specs: `.specs/architecture/target-architecture.md` (`SpellBackend` protocol)
- Related ADRs: ADR-0005 (unified `Locale` in `AppContext`)

---
Last synced with code: a4f76c7
