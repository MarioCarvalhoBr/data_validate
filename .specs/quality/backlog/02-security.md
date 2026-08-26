# 02 · Security & robustness

Threat model: the input is an **untrusted spreadsheet bundle** uploaded by sector teams to the Canoa
platform; the output is an HTML/PDF report opened in a browser by INPE staff, plus a JSON summary
parsed by the platform. The validator runs as a CLI on a shared server.

### SEC-001 · Stored XSS in the HTML/PDF report (Jinja2 without autoescape)
- Priority: P0 · Effort: M · Status: open
- Where: `controllers/report/file_report_generator.py:68` (`Environment(loader=FileSystemLoader(output_folder))`,
  no `autoescape`), `:187-188,237,284-288` (messages and CLI metadata concatenated as raw HTML).
- Problem: every validation message embeds raw cell content (`nome_simples`, labels, column names,
  values). A cell containing `<img src=x onerror=...>` or `<script>` is rendered verbatim in the
  report and executed when opened in a browser; `--user/--sector/--protocol/--file` are also
  injected unescaped. The template loader points at the *output* directory, so a pre-existing
  `default.html` there could be used as a template.
- Proposed fix: `Environment(autoescape=select_autoescape(["html"]), loader=PackageLoader(...))`;
  render message lists from the template (`{% for %}`) instead of building HTML strings in Python;
  escape everything with `markupsafe.escape`; only whitelist HTML entities produced by the
  template itself.
- Tests: golden test with a cell `<script>alert(1)</script>` asserting the report contains
  `&lt;script&gt;`.
- Related: ARC-016

### SEC-002 · PDF generation depends on wkhtmltopdf (archived upstream, old QtWebKit)
- Priority: P1 · Effort: M · Status: open
- Where: `controllers/report/file_report_generator.py:17,343-368`, `pyproject.toml` (`pdfkit`),
  README installation section.
- Problem: wkhtmltopdf has been archived since 2023, ships an unpatched WebKit, and is a native
  binary that must be installed system-wide (Windows/Linux instructions in README). Any HTML injection
  (SEC-001) becomes SSRF/local-file read inside the renderer.
- Proposed fix: make PDF optional (`--pdf`), render with WeasyPrint (pure Python + pango) or a
  headless Chromium via Playwright in CI only; keep HTML as the primary artefact.
- Interim: `pip-audit`'s only remaining finding, `pdfkit` PYSEC-2026-2860 (alias
  GHSA-9g3x-6x24-vf9f, no fixed version exists), is explicitly `--ignore-vuln`'d in
  `make security` and CI (comment points back here) so the gate stays honest instead of either
  failing forever or silently suppressing the whole tool — closing this item removes the ignore.
- Related: TOOL-008

### SEC-003 · Unbounded input sizes (zip-bomb / memory exhaustion)
- Priority: P2 · Effort: M · Status: open
- Where: `readers/excel_reader.py:16`, `readers/csv_reader.py:23` (`low_memory=False`),
  `readers/qml_reader.py:13`
- Problem: no file-size, row or column limits; a 20 MB xlsx that expands to gigabytes takes the
  process down. `dtype=str` object columns multiply memory.
- Proposed fix: `MAX_FILE_BYTES`, `MAX_ROWS`, `MAX_COLUMNS` in config with clear issues; read with
  Arrow-backed string dtype; stream CSV in chunks for `valores`.
- Related: PERF-005

### SEC-004 · Broad `except Exception` masks failures as "valid" runs
- Priority: P1 · Effort: M · Status: open
- Where: `validators/spreadsheets/base/base_validator.py:290-295`,
  `helpers/tools/spellchecker/spellchecker.py:64-65`, `helpers/base/file_system_utils.py:75,116,143,171,194,217`,
  `helpers/common/validation/dataframe_processing.py:68,131`, `helpers/common/validation/proportionality_processing.py:242-243`
  (`except (ValueError, TypeError, Exception): pass`), `controllers/report/file_report_generator.py:150-153`,
  `helpers/tools/data_loader/api/facade.py:126`.
- Problem: programming errors are converted into user-facing Portuguese strings (or swallowed
  entirely), the process exits 0, and the platform records the run as successful.
- Proposed fix: catch only expected domain exceptions; unexpected ones abort with exit code 2 and a
  structured error; add `--strict`.
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
  `security` job; `pdfkit` (PYSEC-2026-2860 / GHSA-9g3x-6x24-vf9f, no fixed version) is explicitly
  `--ignore-vuln`'d with a comment pointing at SEC-002 (the WeasyPrint migration that removes it);
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
- Priority: P2 · Effort: S · Status: open
- Where: `helpers/tools/spellchecker/dictionary_manager.py:41,139-147`
- Problem: `ENCHANT_CONFIG_DIR` set for the whole process; personal word lists written to a
  predictable path inside the package; deleted in `__del__`.
- Proposed fix: session-scoped `tempfile.TemporaryDirectory()` per run; `add_to_session`.
- Related: BUG-022

### SEC-008 · Exit code and stdout contract
- Priority: P1 · Effort: S · Status: open
- Where: `main.py`, `controllers/report/file_report_generator.py:239-263`
- Problem: process exits 0 even when validation fails or crashes; machine contract is a `<{...}>`
  fragment on stdout mixed with progress prints (`main.py:8` prints at *import*).
- Proposed fix: exit 0 = no errors, 1 = validation errors, 2 = runtime failure; `--json <path>`
  writes the summary; nothing else on stdout unless `--verbose`.
- Related: ARC-011, BUG-010

### SEC-009 · Sensitive artefacts tracked in git
- Priority: P3 · Effort: S · Status: open
- Where: `data/output/**/*_report.{html,pdf}`, `docs/**/*.html`, `assets/coverage/*.svg`
- Problem: generated reports (which embed dataset content and machine metadata such as OS/version)
  are committed; history grows with binaries.
- Proposed fix: move reports to CI artefacts / golden JSON; docs to GitHub Pages; badges from Codecov.
- Related: TOOL-006

### SEC-010 · Path handling for `--input_folder` / `--output_folder`
- Priority: P3 · Effort: S · Status: open
- Where: `helpers/base/data_args.py:85-89`, `controllers/report/file_report_generator.py:119,140`
- Problem: no normalisation (`Path.resolve()`), output path built by string concatenation, report
  name derived from the last directory component of the input.
- Proposed fix: `pathlib` end-to-end; refuse to write outside the resolved output directory.
