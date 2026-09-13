# 02 · Security & robustness

Threat model: the input is an **untrusted spreadsheet bundle** uploaded by sector teams to the Canoa
platform; the output is an HTML/PDF report opened in a browser by INPE staff, plus a JSON summary
parsed by the platform. The validator runs as a CLI on a shared server.

### SEC-001 · Stored XSS in the HTML/PDF report (Jinja2 without autoescape)
- Priority: P0 · Effort: M · Status: done
- Where: `controllers/report/file_report_generator.py` (was `:68`
  `Environment(loader=FileSystemLoader(output_folder))`, no `autoescape`; `:187-188,237,284-288`
  messages and CLI metadata concatenated as raw HTML — both gone).
- Problem (fixed): every validation message embedded raw cell content (`nome_simples`, labels,
  column names, values). A cell containing `<img src=x onerror=...>` or `<script>` rendered
  verbatim in the report and executed when opened in a browser; `--user/--sector/--protocol/--file`
  were also injected unescaped. The template loader pointed at the *output* directory, so a
  pre-existing `default.html` there could have been used as a template.
- Fix shipped (migration Phase 4, ADR-0007): `Environment(loader=PackageLoader("data_validate",
  "static/report"), autoescape=select_autoescape(["html"]))` — templates load only from the
  package's own `static/report/` directory, never the user-writable output folder, closing the
  template-planting hole. `report_template.html` loops over `ReportModel.sections`/
  `skipped_tests` itself (`{% for %}`); `_format_messages_as_html`, `_get_optional_field_text`,
  and the two `f"<strong>...` string-building blocks in `_build_template_variables` are deleted —
  `sector`/`protocol`/`user`/`file`/every message now flow into the template as plain Python
  values via `ReportModel` (ARC-016) and are escaped by `autoescape=True`; nothing is ever marked
  `|safe`. The hand-rolled regex template-variable validator (`_validate_html_template`) and its
  fallback constant (`ApplicationConfig.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS`) are both deleted —
  a missing/broken template now raises `jinja2.TemplateNotFound`/`TemplateError`, already caught
  by `build_report`'s existing `except (OSError, TemplateError)` (SEC-004), instead of silently
  falling back to a second template that could itself drift out of sync.
- Tests: `tests/unit/controllers/report/test_file_report_generator.py::TestXssEscaping` (a
  `<script>alert(1)</script>` message renders as `&lt;script&gt;alert(1)&lt;/script&gt;`, never a
  raw tag; `--user`/`--sector` CLI metadata and a skipped-test label are escaped the same way;
  the loader is asserted to be a `PackageLoader`), `TestBuildReportModel` (ARC-016's
  `ReportModel`/`ReportSection` carry plain values, not HTML), `TestBuildReportEndToEnd` (the
  real `__init__`→`build_report` path, writing an actual HTML file, exercised once end to end).
  New e2e fixture `data/input/data_errors_xss/` (a `data_ground_truth_01` copy with one
  `descricao` cell mutated to embed `<Script>Alert(1)</Script>`, tripping `DESC-004`'s
  capitalisation-mismatch warning) plus its golden, `tests/e2e/golden/data_errors_xss.json`
  (additive); `data_errors_01`'s golden gained one reviewed line change because escaping now
  *preserves* content a previous, non-escaping render had let the naive golden HTML-extractor
  mangle — see `tests/e2e/golden/CHANGELOG.md`'s 2026-09-13 entry for the full before/after.
- Related: ARC-016, SEC-002

### SEC-002 · PDF generation depends on wkhtmltopdf (archived upstream, old QtWebKit)
- Priority: P1 · Effort: M · Status: done
- Where: `controllers/report/file_report_generator.py` (was `:17,343-368`), `pyproject.toml`
  (`pdfkit` moved out of `[project].dependencies`), README installation section.
- Problem (fixed): wkhtmltopdf has been archived since 2023, ships an unpatched WebKit, and is a
  native binary that had to be installed system-wide (Windows/Linux instructions in README). Any
  HTML injection (SEC-001) became SSRF/local-file read inside the renderer.
- Fix shipped (migration Phase 4, ADR-0007): `pdfkit` is removed from `[project].dependencies`;
  `[project.optional-dependencies] pdf = ["weasyprint (>=70,<80)"]` is the supported PDF backend
  (pure Python + pango, no native daemon, actively maintained; `>=70` specifically to clear
  `PYSEC-2026-3940`, fixed in 70.0). `FileReportGenerator._save_pdf_file` tries WeasyPrint first
  (`from weasyprint import HTML`; both `ImportError` — not installed — and `OSError` — installed
  but its native pango/cairo/gdk-pixbuf libraries are missing — fall through to the next
  backend); then `pdfkit`/`wkhtmltopdf` only as a compatibility path for hosts that already have
  it (not a declared dependency any more); if neither is usable, PDF generation is skipped with
  `"PDF generation skipped: install canoa-data-validate[pdf] for PDF output."` on stderr and the
  run continues — HTML remains the always-produced primary artefact, exit code unaffected. A
  genuine conversion failure (either backend's own `OSError` from the actual render call, not the
  import) is still reported as an error, matching the pre-existing SEC-004 narrowing.
- Tests: `TestSavePdfFileExceptionHandling` (WeasyPrint success; WeasyPrint `OSError` at
  conversion time reported; WeasyPrint import raising `OSError` — native libs missing — or
  `ImportError` — not installed — both fall back to `pdfkit`; no backend available skips with the
  `[pdf]` install message; `pdfkit`'s own `OSError`/unexpected-exception handling unchanged),
  `TestLazyPdfImports` (importing the module alone imports neither `pdfkit` nor `weasyprint`,
  PERF-008). e2e: `pdf_backend_available()` (`tests/conftest.py`) probes WeasyPrint-importable
  OR `wkhtmltopdf`-on-`PATH` so `requires_pdf`/the golden harness's PDF assertion accept either
  backend, not only the legacy binary.
- Closed: `pip-audit`'s `pdfkit` finding (`PYSEC-2026-2860`/`GHSA-9g3x-6x24-vf9f`) is gone from
  the lock now that `pdfkit` is no longer a declared dependency; the `--ignore-vuln` escape hatch
  in `make security`/CI is removed (not silenced) — `make security` runs a plain `poetry run
  pip-audit` and stays clean.
- Related: TOOL-008, SEC-001

### SEC-003 · Unbounded input sizes (zip-bomb / memory exhaustion)
- Priority: P2 · Effort: M · Status: done
- Where: `readers/excel_reader.py:16`, `readers/csv_reader.py:23` (`low_memory=False`),
  `readers/qml_reader.py:13`
- Problem: no file-size, row or column limits; a 20 MB xlsx that expands to gigabytes takes the
  process down. `dtype=str` object columns multiply memory.
- Proposed fix: `MAX_FILE_BYTES`, `MAX_ROWS`, `MAX_COLUMNS` in config with clear issues; read with
  Arrow-backed string dtype; stream CSV in chunks for `valores`.
- Done: `ApplicationConfig` gained three DoS-guard constants (`MAX_INPUT_FILE_BYTES` = 100 MB,
  `MAX_SHEET_ROWS` = 1,000,000, `MAX_SHEET_COLUMNS` = 5,000 — generous limits, not business rules).
  `DataLoaderFacade.__init__` now takes an optional `translate: Callable[..., str] | None` and
  `limits: tuple[int, int, int] | None`; `SpreadsheetProcessor._read_data` passes
  `translate=self.language_manager.text` and `limits=(config.MAX_INPUT_FILE_BYTES,
  config.MAX_SHEET_ROWS, config.MAX_SHEET_COLUMNS)` from `self.context.config`, so the loading
  layer never imports `data_validate.config` directly (`.claude/rules/architecture-boundaries.md`)
  — it falls back to its own module-level constants (mirroring the same numbers) and to a
  `MessageCatalog("pt_BR", default_catalog_dir())` when constructed without either. `load_all` now
  checks `path.stat().st_size` before reading (an oversized file is never handed to the reader) and
  the resulting frame's `.shape` after reading (an oversized frame is discarded, same as an unread
  file); both violations append a translated message (`loader_error_file_too_large` /
  `loader_error_sheet_too_big`, added to both locale catalogs) to the FS error list, exactly like
  the pre-existing per-exception messages. New rule ID `STRUCT-015` registered in
  `.specs/business-rules/file-structure.md` and the `README.md` ID map. Arrow-backed dtypes and
  chunked CSV streaming (the rest of the original proposed fix) are not part of this slice — the
  size/shape guard alone is enough to stop the DoS class this item names; left as a follow-up if
  ever needed. Tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py::
  TestDataLoaderFacadeSizeLimits` (file-too-large, sheet-too-big by rows, sheet-too-big by columns,
  within-limits no-false-positive, explicit `translate` callable wiring, default `MessageCatalog`
  fallback, default limits matching `ApplicationConfig`); every pre-existing
  `TestDataLoaderFacade` test now runs under an autouse fixture patching `Path.stat()` to a small
  size, since those tests use real (non-existent) `Path` objects that would otherwise trip
  `FileNotFoundError` from `stat()` itself.
- Related: PERF-005

### SEC-004 · Broad `except Exception` masks failures as "valid" runs
- Priority: P1 · Effort: M · Status: in-progress
- Where (remaining, not yet ported — outside this slice's scope):
  `validators/spreadsheets/base/base_validator.py:296` (`except Exception as e:`),
  `helpers/tools/spellchecker/spellchecker.py:64` (`except Exception as e:`).
  (`helpers/common/validation/proportionality_processing.py`'s `except (ValueError, TypeError,
  Exception): pass` removed — see the note below.)
- Problem: programming errors are converted into user-facing Portuguese strings (or swallowed
  entirely), the process exits 0, and the platform records the run as successful.
- Proposed fix: catch only expected domain exceptions; unexpected ones abort with exit code 2 and a
  structured error; add `--strict`.
- Done (proportionality site, ARC-017 Phase 3 Port 7): `ProportionalityProcessing
  .find_zero_sum_violations` (formerly `validate_zero_sum_rows`) now catches
  `except (ValueError, TypeError): continue` — the redundant `Exception` member (a bare
  `except Exception` in disguise, since `Exception` already covers `ValueError`/`TypeError`) is
  gone; `float(str(val).replace(",", "."))` cannot raise anything else on this input shape.
- Done (loading/reporting slice): all six broad `except Exception` fallbacks in
  `helpers/base/file_system_utils.py` are gone — every method now catches only `OSError` (the
  family every `os.path.*`/`open()`/`os.remove()`/`os.makedirs()`/`os.listdir()` call can
  plausibly raise); a non-`OSError` failure propagates to `main()`'s boundary (exit 2). The two
  `except Exception` sites in `helpers/common/validation/dataframe_processing.py`
  (`check_dataframe_vertical_bar`, `check_dataframe_unnamed_columns`) are removed outright — there
  is no plausible failure mode in that pure-pandas code worth reporting as a data-quality error, so
  any failure now propagates. `helpers/tools/data_loader/api/facade.py`'s `load()` read loop keeps
  its specific `except` chain (`FileNotFoundError`, `UnicodeDecodeError`, `pd.errors.ParserError`,
  `ValueError`, `IOError`) and gains one more specific type, `python_calamine.CalamineError` (the
  base of `python-calamine`'s `ZipError`/`XmlError`/`PasswordError`, raised by pandas'
  `engine="calamine"` for a malformed/corrupt `.xlsx` — an expected failure mode of untrusted
  input, confirmed by the `data_errors_01` golden fixture, not a programming error); the final
  `except Exception` fallback (redundant with the specific chain) is gone, so a truly unexpected
  reader failure now propagates instead of being downgraded to a per-file message.
  `controllers/report/file_report_generator.py` narrows all three of its `except Exception` sites:
  `build_report` to `(OSError, jinja2.TemplateError)`, `_save_html_file` to `OSError`, and
  `_save_pdf_file` to `(ImportError, OSError)` (`pdfkit` raises a plain `IOError`, an `OSError`
  alias in Python 3, for every conversion failure it reports; `ImportError` covers the lazy
  `import pdfkit` when the optional dependency/its native `wkhtmltopdf` binary is missing).
  Every other site this item names when it was opened is done; the two remaining sites above
  belong to `validators/`/`spellchecker.py` and are tracked separately (parallel migration work).
- Final inventory (Phase 5 close, 2026-09-13 — `grep -rn "except Exception" data_validate/`, every
  survivor enumerated and judged):
  - `main.py`'s `main()` boundary — **sanctioned by design** (SEC-008): the one place an
    unexpected construction/pipeline failure is caught to print `Fatal error: <exc>` to stderr
    and return exit code 2, rather than a raw traceback; narrower catching here would defeat the
    exit-code contract this item and SEC-008 both rely on.
  - `rules/engine.py::Engine.run` — **sanctioned by design**, documented inline: isolates an
    unexpected failure in *any* rule (unknowable type in advance, since rules are
    plugin-shaped from the engine's point of view) into a `FAILED` `RuleOutcome` instead of
    crashing the whole run or being silently absorbed as a clean pass — this *is* SEC-004's own
    fix pattern (fail visibly, not silently), applied at the one seam that must stay generic.
  - `validators/spreadsheets/base/base_validator.py` — **confirmed gone**: `validators/` was
    deleted entirely by ARC-008/ARC-017 Phase 3 Port 8; this item's original site no longer
    exists.
  - `helpers/tools/spellchecker/dictionary_manager.py`'s `clean_temporary_files` — **fixed this
    slice**: the try/except wrapped two plain `self.x = None` assignments, which cannot raise;
    removed outright (no plausible failure mode), matching this item's own precedent for
    `dataframe_processing.py`'s two already-fixed sites. Regression test updated:
    `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py::
    test_clean_temporary_files_always_drops_references` (was
    `test_clean_temporary_files_dictionary_cleanup_error`, which asserted a scenario only a
    contrived `mocker.MagicMock` with a raising `__bool__` could trigger — not a real enchant
    failure mode).
  - `helpers/tools/spellchecker/dictionary_manager.py`'s `validate_dictionary`/
    `initialize_dictionary`/`_load_extra_words` (3 sites) — **newly discovered, not fixed this
    slice, flagged for follow-up**: each wraps a call into the `enchant` C-extension boundary
    (`Broker()`, `broker.dict_exists`, `broker.request_dict`) or file I/O reading
    `extra-words.dic`; unlike `clean_temporary_files`, these *do* have a plausible failure mode
    (a malformed/missing system dictionary, a native library error surfacing as an
    enchant-specific exception type this module does not import), so blindly narrowing to
    `OSError` risks silently stopping error reporting for a real enchant failure. Narrowing
    these correctly needs enumerating enchant's actual exception hierarchy first — real,
    scoped follow-up work, not a same-slice drive-by change.
  - `helpers/tools/spellchecker/spellchecker.py::check_spelling_text` — **newly discovered, not
    fixed this slice, flagged for follow-up**: dead code in production (only
    `check_spelling_text_structured` — a separate method with its own, already-sanctioned SPELL-005
    broad catch — is called by `rules/spell.py`), but its own test file
    (`tests/unit/helpers/tools/spellchecker/test_spellchecker.py`, 20 tests across 3 classes)
    exercises it directly, including three tests that set a **generic** `Exception("...")`
    `side_effect` and assert on the resulting fallback message. Narrowing the `except` clause
    would break those three tests' premise (a generic `Exception` would no longer be caught);
    deleting the dead method outright would require rewriting the entire test file. Either fix
    is real, scoped work, not a safe same-slice change given the size of the surrounding test
    suite — flagged, not silently ignored.
  - `helpers/tools/locale/language_manager.py`'s `_load_translations`/`text()` (2 sites) — **not
    named in this item's original scope, reviewed, left as-is**: both are the i18n subsystem's
    own last-resort fallback (a translation-file load failure or a template-formatting error
    must never crash the whole validation run just because one message couldn't be localised);
    narrowing further risks the i18n layer itself becoming a new crash source for every rule
    that calls `translate(...)`, which is a materially different risk profile from a validator
    silently downgrading a real bug into a fake "valid" result.
  - `helpers/tools/data_loader/api/facade.py` — its own docstring documents the "former final
    `except Exception`" as already removed (SEC-004, prior slice); grep-confirmed no `except
    Exception` remains in this file today.
  Tests: `tests/unit/helpers/base/test_file_system_utils.py` (six `*_unexpected_error_propagates`
  tests replacing the old `*_unexpected_error` assertions, plus new `OSError`-path regression tests
  for the three sites that previously had no dedicated `OSError` branch),
  `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
  (`test_check_vertical_bar_unexpected_error_propagates`,
  `test_check_unnamed_columns_unexpected_error_propagates`),
  `tests/unit/helpers/tools/data_loader/api/test_facade.py`
  (`test_load_with_general_exception_propagates`), `tests/unit/controllers/report/
  test_file_report_generator.py` (`TestBuildReportExceptionHandling`,
  `TestSaveHtmlFileExceptionHandling`, `TestSavePdfFileExceptionHandling` — new classes; this
  module had no prior test coverage of these three `except` sites at all). `make check` and the
  full `tests/e2e` golden harness (7/7) both verified green for this slice in isolation (a
  detached-HEAD worktree with only these four production + four test files applied on top of the
  last commit), since the shared working tree had unrelated, uncommitted, in-progress changes from
  a parallel migration effort (`models/`, `spreadsheet_processor.py`) at the time of this slice.
- Related: ARC-011

### SEC-005 · Supply-chain and CI hygiene
- Priority: P2 · Effort: S · Status: done
- Where: `Makefile` (`security`/`security-offline` targets), `.github/workflows/ci.yml` (`security`
  job), `.github/workflows/codeql.yml`, `.github/dependabot.yml`, `pyproject.toml` (`[tool.bandit]`),
  `.claude/hooks/guard-bash.sh`, `.claude/settings.json`.
- Problem (historical): `poetry add ruff` mutated the lock in CI with `continue-on-error: true`, no
  `pip-audit`, no `bandit`, no CodeQL, no `dependabot.yml` for pip; known CVEs in pdfkit, pillow,
  click, idna, pygments, pytest, requests, setuptools, urllib3 were unaddressed; the Bash-tool guard
  hook used a small regex denylist that a wrapped/piped/subshelled command could slip past.
- Fix: lock committed and respected (`poetry install --sync`); `bandit -c pyproject.toml -r
  data_validate tools` and `pip-audit --strict` both run clean in `make security` and CI's
  `security` job; `pdfkit` (PYSEC-2026-2860 / GHSA-9g3x-6x24-vf9f, no fixed version) was
  explicitly `--ignore-vuln`'d with a comment pointing at SEC-002 (the WeasyPrint migration that
  removes it) — **superseded**: SEC-002 (migration Phase 4) removed `pdfkit` from
  `[project].dependencies` entirely, so this finding is gone from the lock and the
  `--ignore-vuln` flags are removed from `make security`, not just still-present-but-unused;
  `pillow`, `click`, `idna`, `pygments`, `pytest`, `requests`, `setuptools`, `urllib3`, `certifi`
  updated via `poetry update` (lockfile only, no `pyproject.toml` constraint changes needed);
  `.github/workflows/codeql.yml` added (Python, push/PR to `main` + weekly schedule); Dependabot
  already covered pip + actions; all actions pinned by full commit SHA with a version comment;
  every `actions/checkout` step across `ci.yml`/`release.yml`/`docs.yml`/`codeql.yml` sets
  `persist-credentials: false`; `.claude/hooks/guard-bash.sh` rewritten as a fail-closed Python
  decision engine (segments on `&&`/`||`/`;`/`|`/newlines, recurses into `bash -c`/`sh -c`/`eval`/
  `$(...)`/backticks/`xargs`, resolves `rm -r` targets against the repo root) with a 44-case
  `--self-test`; `.claude/settings.json` denies `git -C *`, `git remote *`,
  `git checkout -- .`/`git restore .`, `git branch -D *`, `find * -delete*`, `gh pr merge*`,
  `gh release*`, `curl * | *`, `wget *`, `chmod -R 777*`, and only allows `git add -- *` (never a
  bare `git add *`); `.gitignore` covers `.env*`, not just `.env`.
- Related: TOOL-001

### SEC-006 · Pre-commit hooks run the pipeline and `git add .`
- Priority: P2 · Effort: S · Status: done
- Where: `.pre-commit-config.yaml`, `scripts/generate_logs_coverage_badge.sh:27,36`,
  `scripts/prepare_metadata.sh:33`, `scripts/prepare_pyproject.sh:42`
- Problem: hooks stage **every** file in the working tree (local data, credentials, scratch files)
  and rewrite source files (`serial`, version) on each commit.
- Evidence: on 2026-08-25 a docs-only commit (9 new files under `.specs/`) came out with 22 files —
  the hooks bumped `serial` 732→733, regenerated 7 PDF reports, both badges, `README.md` and
  `docs/`; the commit had to be redone with `--no-verify`. Until this item is fixed, commit with
  `--no-verify` or run `pre-commit uninstall`.
- Proposed fix: replace with standard hooks (ruff, ruff-format, mypy, bandit, check-yaml,
  detect-private-key, `poetry check`); never `git add` inside hooks; version bump only in release
  workflow.
- Done: hooks replaced; `pre-commit uninstall` executed on 2026-08-25
- Related: TOOL-002

### SEC-007 · Global environment mutation and predictable temp files
- Priority: P2 · Effort: S · Status: done
- Where: `helpers/tools/spellchecker/dictionary_manager.py`
- Problem (fixed): `ENCHANT_CONFIG_DIR` set for the whole process; personal word lists written to a
  predictable path inside the package; deleted in `__del__`.
- Fix shipped: `enchant.Broker.set_param` is a documented no-op with the Enchant C library >= 2.0
  (this project links 2.3.3), and every `Broker`/`Dict` call re-reads `ENCHANT_CONFIG_DIR` from the
  process environment at call time rather than caching it — so a per-broker parameter is not
  available and the environment variable is the only lever. `DictionaryManager` now creates one
  `tempfile.TemporaryDirectory()` per manager instance (lazily, on first
  `validate_dictionary`/`initialize_dictionary` call), symlinks the bundled `static/dictionaries/
  hunspell` folder into it, and only ever points `ENCHANT_CONFIG_DIR` at that throwaway directory —
  never at the package directory. The mutation is scoped by
  `DictionaryManager._enchant_config_dir_scope()`, a context manager that snapshots the previous
  value (or its absence) and restores it in a `finally` block around each broker/dict call, so the
  process environment is left exactly as it was found once the call returns. `clean_temporary_files`
  discards the whole temporary directory (`TemporaryDirectory.cleanup()`) instead of deleting
  predictable `.dic`/`.exc` files by name. `__del__` was removed — there is no on-disk personal
  dictionary left to clean up if a caller forgets to call `clean_temporary_files` (the OS/CPython's
  own `tempfile` finalizer reclaims the directory regardless). Regression tests:
  `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py` —
  `test_initialization_does_not_mutate_environment`,
  `test_enchant_config_dir_scope_restores_previous_value`,
  `test_enchant_config_dir_scope_restores_absence` (mocked Broker, no real enchant needed), and
  `TestDictionaryManagerRealEnchant` (`test_environment_is_unchanged_after_full_lifecycle`,
  `test_no_file_created_under_package_dictionaries_directory`,
  `test_two_managers_do_not_interfere`), skipped cleanly when the native libenchant/hunspell backend
  is unavailable.
- Related: BUG-022

### SEC-008 · Exit code and stdout contract
- Priority: P1 · Effort: S · Status: done
- Where: `main.py`, `helpers/base/data_args.py`, `controllers/report/file_report_generator.py:239-263`
- Problem (fixed): process exited 0 even when validation failed or crashed; machine contract was a
  `<{...}>` fragment on stdout mixed with progress prints (`main.py:8` printed at *import*).
- Fix shipped: `main()` returns an `int`, `main.py` ends with `sys.exit(main())`; exit `0` = no
  issue at/above `--fail-on`, `1` = an issue at/above `--fail-on` (default `error`; `--fail-on
  never` restores the old always-0), `2` = an unexpected runtime failure — one broad
  `except Exception` around `DataArgs`/`GeneralContext`/`SpreadsheetProcessor` construction prints
  `Fatal error: <exc>` to stderr and returns 2. `--json PATH` writes the same summary object as the
  stdout fragment. The import-time banner (`main.py:8`) moved into `main()`, on stderr (ARC-012).
- Not in scope for this fix at the time (later narrowed by SEC-004): `FileReportGenerator
  .build_report`'s own broad `except Exception` around HTML/PDF generation used to swallow every
  report-rendering failure and print to stderr instead of propagating it into the exit-code-2 path;
  SEC-004 narrowed it to `(OSError, jinja2.TemplateError)`, so any other failure now does propagate
  into `main()`'s broad catch and returns 2, same as any other unexpected construction failure. A
  `--verbose` flag to further quiet stdout/stderr is still not implemented (see ARC-011's "still
  open" list).
- Related: ARC-011, ARC-012, BUG-010

### SEC-009 · Sensitive artefacts tracked in git
- Priority: P3 · Effort: S · Status: done
- Where: `data/output/**/*_report.{html,pdf}`, `docs/**/*.html`, `assets/coverage/*.svg`
- Problem (fixed): generated reports (which embed dataset content and machine metadata such as
  OS/version) were committed; history grew with binaries.
- Fix shipped: `docs/**/*.html` (pdoc output) was already removed in a prior slice (`docs.yml`
  publishes to GitHub Pages instead). This slice removes the rest: `git rm -r data/output`
  (14 committed HTML/PDF reports across 7 fixtures — the e2e golden harness under
  `tests/e2e/golden/*.json` is the regression net now, not a committed rendered report) and
  `git rm -r assets/coverage` (2 generated SVG badges — `README.md` already showed the Codecov
  and CI-status badges, not these local ones). `.gitignore` gained `data/output/` (replacing the
  narrower `data/output/logs/` entry) and `assets/coverage/` so neither path is re-added by a
  local `make run`/`make coverage` invocation. `assets/protocolo-*.pdf` (the protocol
  specification documents) are untouched — intentional, versioned reference material, not
  generated output.
- Related: TOOL-006

### SEC-010 · Path handling for `--input_folder` / `--output_folder`
- Priority: P3 · Effort: S · Status: done
- Where: `helpers/base/data_args.py::DataFile._validate_arguments`,
  `controllers/report/file_report_generator.py::FileReportGenerator._resolve_report_path`
- Problem (fixed): no normalisation (`Path.resolve()`), output path built by string
  concatenation, report name derived from the last directory component of the input.
- Fix shipped: `DataFile._validate_arguments` resolves both `input_folder` and `output_folder`
  to absolute, normalized paths via `Path.resolve()` once, at validation time, and stores the
  resolved `str` back onto the attributes (every downstream consumer keeps reading a plain
  `str`, no ripple). `FileReportGenerator._resolve_report_path` builds the report path with
  `pathlib` (`output_dir / f"{file_name}{html_output_file}"`) and raises `ValueError` when the
  resolved report path is not `is_relative_to()` the resolved output directory — defence in
  depth, since `file_name` (`Path(input_folder).name`) cannot itself contain a path separator
  once `input_folder` is already resolved.
- Related: BUG-009, SEC-001
