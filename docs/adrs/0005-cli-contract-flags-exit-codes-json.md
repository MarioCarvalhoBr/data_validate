# ADR-0005: CLI contract: explicit flags, exit codes, JSON output; deprecate abbreviations and `.config/store.locale`

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`DataArgs._create_parser` (`helpers/base/data_args.py:246-259`) builds its `argparse.ArgumentParser`
with `allow_abbrev=self.allow_abbrev` where `allow_abbrev=True` is the constructor default
(`DataArgs.__init__`, line 228). Because every long flag (`--input_folder`, `--output_folder`,
`--no-spellchecker`, `--no-warning-titles-length`, `--no-time`, `--no-version`, `--sector`,
`--protocol`, `--user`, `--file`) is registered without a short alias except `--locale`/`-l`, `argparse`
silently accepts any unambiguous prefix — `--i` matches `--input_folder`, `--o` matches
`--output_folder` — which only works today because no two flags happen to share a prefix yet; the
CLI documented in `scripts/run_main_pipeline.bat` already relies on `--d` for `--debug` (ARC-011).
Locale resolution is worse: two unrelated pieces of code read/write two different files.
`Bootstrap._check_and_set_locale` (`middleware/bootstrap.py:41-42`) sets
`self.config_dir = os.path.expanduser(".config")` — since `".config"` has no leading `~`,
`expanduser` returns it unchanged, so this path is **relative to the current working directory**
— then persists the parsed `--locale` there (`bootstrap.py:66-67`). Independently,
`LanguageManager._congifure_language` (`helpers/tools/locale/language_manager.py:34`,
note the existing typo) reads/writes
`Path(__file__).resolve().parents[4] / ".config" / "store.locale"`, which resolves to the
**repository root** when running from source (or the parent of `site-packages` when installed) —
a different absolute path whenever CWD ≠ repo root. Worse, `main.py:12-16` constructs `DataArgs()`
*first*; `DataArgs.__init__` (`data_args.py:236`) builds `self.language_manager =
LanguageManager()` — which reads whatever `store.locale` already contains — **before**
`DataArgs.run()` even parses `--locale` from `sys.argv`. Only afterward does `main.py:16` construct
`Bootstrap(data_args)`, which persists the now-parsed `--locale` value to the *other* file. Net
effect (BUG-004): a first-time `--locale en_US` run never reaches the `LanguageManager` that
`DataArgs` already built with the stale default, and once CWD ≠ repo root, `canoa-data-validate`
scatters a stray `./.config/` directory wherever it's invoked from — a read/write inside a
directory the process may not control, breaking on read-only installs (TOOL-008). Separately,
`main.py:8` runs `print(f"{data_validate.__welcome__}\n")` at **import time** (before `main()` is
even called), mixing banner output with the machine-readable `<{...}>` JSON summary printed later
by `FileReportGenerator._print_json_summary` (`controllers/report/file_report_generator.py:
239-263`) on the same stdout stream; the process always exits 0, even on a crash inside
`FileReportGenerator.build_report`'s broad `except Exception` (line 150) — SEC-008.

## Decision

Replace `Bootstrap` and file-persisted locale entirely. Locale becomes an explicit constructor
argument threaded through `AppContext` (built once in `cli.main()`, per
`.specs/architecture/target-architecture.md`) — resolved once from `--locale`/`-l` with no
persistence step, no `.config/store.locale` read or write, and therefore no dependency on CWD. A
new `data_validate/cli.py` (argparse, `allow_abbrev=False`) defines explicit, unambiguous flags:
`-i/--input`, `-o/--output`, `-l/--locale`, plus new `--json PATH` (writes the structured summary;
fixes BUG-010's invalid-JSON `str(dict).replace()` by using `json.dumps(..., ensure_ascii=False)`),
`--format html,pdf,json`, `--fail-on warning|error`, `--version`, `--rules`, `--list-rules`. The
current spellings (`--input_folder`, `--output_folder`, `--no-spellchecker`, etc.) are kept as
deprecated aliases for one minor release, each printing a deprecation notice to stderr, then
removed. Exit codes are standardised and documented in `.specs/api/cli-contract.md`: `0` = no
errors, `1` = validation found errors, `2` = runtime failure (crash, bad arguments, unreadable
input) — replacing today's "always 0". stdout carries **only** the requested machine output
(`--json`, when given) unless `--verbose` is passed; the import-time banner print (`main.py:8`)
moves inside `cli.main()`, gated by verbosity, never printed on `import data_validate`.

## Consequences

### Positive
- `--locale en_US` behaves identically on every invocation, on every OS, from any working
  directory, and installed via pip with no writable package/CWD requirement — closing BUG-004 and
  the TOOL-008 "nothing written inside the package" goal simultaneously.
- No more ambiguous-abbreviation risk: `--n` cannot accidentally resolve to whichever of
  `--no-time`/`--no-version`/`--no-spellchecker` argparse picks first as new flags are added.
- The platform gets a documented, versioned exit-code and `--json` contract instead of having to
  scrape a semi-formatted string out of mixed stdout output (fixes SEC-008 and BUG-010 together).

### Negative
- Existing platform integrations invoking `--input_folder`/`--output_folder`/`--l` keep working
  only for one deprecated minor release; the platform team must update their invocation before the
  next major/minor bump removes the aliases — coordinated via `CHANGELOG.md` and
  `.specs/future/deprecations.md`.
- Users who relied on locale persisting across separate invocations (no `--locale` flag = "remember
  last choice") lose that convenience; if genuinely needed, `platformdirs.user_config_dir` is the
  documented follow-up (tracked, not implemented now) rather than the current unpredictable
  dual-file scheme.

## Alternatives considered

### Keep `allow_abbrev=True` for backward compatibility
Rejected: abbreviation matching is inherently order-/set-dependent — adding any new flag can
silently change what a previously-working abbreviated invocation resolves to, which is precisely
the ambiguity a stable machine-facing CLI contract cannot tolerate; explicit flags with documented
deprecated long-form aliases achieve the same backward compatibility without the ambiguity.

### Switch to Typer or Click instead of argparse
Rejected for now: argparse, once `allow_abbrev=False` and explicit flags are set, is sufficient for
this CLI's surface (a dozen flags, no subcommands); adopting a new dependency is not needed to fix
BUG-004/ARC-011/SEC-008, and is left as a `.specs/future/ideas.md` candidate if the CLI grows
subcommands later.

### Keep `Bootstrap` + `.config/store.locale` persistence but fix the path mismatch (use one path)
Rejected: even with a single consistent path, on-disk locale persistence means the tool's behaviour
for the *same* explicit `--locale` flag depends on prior runs' leftover state and on filesystem
permissions at an arbitrary location — the opposite of "explicit flags, deterministic behaviour"
that the CLI contract (and TOOL-008's "installed-package experience") both require; deleting
`Bootstrap` removes an entire class of environment-dependent bugs rather than patching one instance
of it.

## Links

- Backlog: `BUG-004`, `BUG-023` (`01-bugs.md`); `ARC-011`, `ARC-012` (`03-architecture.md`);
  `SEC-008` (`02-security.md`); `BUG-010` (`01-bugs.md`); `TOOL-008` (`06-tooling-ci.md`);
  `08-migration-roadmap.md` Phase 1 item 4
- Specs: `.specs/api/cli-contract.md`, `.specs/architecture/target-architecture.md`
  (`main.py` → `cli.py`, `middleware/bootstrap.py` → deleted)
- Related ADRs: ADR-0004 (JSON summary carries `Issue` data), ADR-0014 (locale/catalog)

---
Last synced with code: a4f76c7
