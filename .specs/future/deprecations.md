# Deprecations

| What | Why | Replaced by | Warning from | Removed in | Phase | Backlog |
|---|---|---|---|---|---|---|
| `middleware/bootstrap.py` (`Bootstrap`) | Locale persistence via CWD-relative file; thread pool for one task | `Options.locale` passed through `AppContext` | — (internal) | 0.8.0 | 1 | BUG-004, BUG-008 |
| `.config/store.locale` (repo root and CWD) | Global mutable state, breaks installed usage, first-run mismatch | `--locale` per invocation | 0.8.0 (file ignored, stderr note if present) | 0.8.0 | 1 | BUG-004 |
| `pdfkit` + `wkhtmltopdf` | Upstream archived, old WebKit, native binary | `weasyprint` under extra `[pdf]`; PDF opt-in via `--format` | 0.9.0 | 1.0.0 | 4 | SEC-002 |
| `scripts/*.sh`, `scripts/*.bat` (`run_main_pipeline`, `generate_*`, `prepare_*`) | Shell-only, `git add .` inside hooks, hand-bumped version | `tools/harness/run_fixtures.py`, CI workflows, release workflow | Phase 0 (moved to `tools/legacy/`) | Phase 5 | 0/5 | SEC-006, TOOL-009 |
| Legacy `.pre-commit-config.yaml` hooks | Run the full pipeline and stage everything | Standard ruff/mypy/bandit hooks | Phase 0 | Phase 0 | 0 | TOOL-002 |
| Flag prefix abbreviations `--i`, `--o`, `--l`, `--d` | Rely on `allow_abbrev`; fragile | Explicit `-i/--input`, `-o/--output`, `-l/--locale`, `--debug` | 0.8.0 | 1.0.0 | 1 | ARC-011 |
| `--input_folder`, `--output_folder` spellings | Non-idiomatic | `--input`, `--output` | 0.8.0 | 1.0.0 | 1 | ARC-011 |
| Import-time banner and "Tempo total de execução" on stdout | Pollutes machine output | stderr logging with `--verbose` | 0.8.0 | 0.8.0 | 1 | ARC-012 |
| `str(dict).replace("'", '"')` JSON fragment | Invalid JSON risk | `json.dumps`; same keys kept | 0.8.0 | — (format kept) | 1 | BUG-010 |
| README generated from `static/templates/README.TEMPLATE.md` + `helpers/tools/readme/generate_readme.py` | Build tooling inside the runtime package; stale badges | Hand-written README (ADR-0009) | Phase 0 | Phase 0 | 0 | ARC-010 |
| `helpers/tools/spellchecker/main.py` demo | Dead code in package | — | Phase 5 | Phase 5 | 5 | ARC-010 |
| `helpers/tools/data_loader/readers/qml_reader.py` and `.qml` scanning | Unused output (`data["qmls"]`), not in allowed extensions | Decision pending (`open-questions.md`) | Phase 2 | Phase 2 | 2 | BUG-015 |
| Class-level `RequiredColumn` Series mutated with data | Global state | Instance-level typed frames | — | Phase 2 | 2 | BUG-002 |
| `ConstantBase` | Ad-hoc immutability | `@dataclass(frozen=True)` | — | Phase 5 | 5 | ARC-013 |
| `MetadataInfo.serial` and `prepare_metadata.sh` | Hand-maintained pre-release serial | `importlib.metadata.version` from `pyproject.toml` | Phase 0 | Phase 1 | 1 | TOOL-005 |
| Committed `docs/**/*.html`, `data/output/**` reports, `assets/coverage/*.svg` | Generated artefacts in git | Pages workflow, goldens, Codecov badge | Phase 0 | Phase 0/5 | 0 | TOOL-006 |
| Module names with typos (`compostion_graph_validator.py`, `_congifure_language`) | Naming | Renamed during migration with import shims for one minor | 0.8.0 | 1.0.0 | 3 | BUG-024 |

Every removal is announced in `CHANGELOG.md` under *Deprecated* first and *Removed* later.

Last synced with code: 09279f4
