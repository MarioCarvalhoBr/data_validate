# Ideas (not scheduled)

| Idea | Value | Prerequisites | Notes |
|---|---|---|---|
| Polars backend behind `SheetFrame` | 5–10× faster on very large `valores`; lower memory | Rules written against a narrow frame Protocol (Phase 3) | Keep pandas as default; opt-in `--engine polars` |
| Validation service (HTTP API) | Platform calls an endpoint instead of spawning a process; concurrency control | Python API (Phase 1), input limits (Phase 2) | FastAPI + job queue; report served from object storage |
| Incremental validation | Re-run only rules affected by changed sheets | Rule `requires` metadata (Phase 3), content hashes | Useful for large sectors iterating on one sheet |
| Sector-specific rule packs | Extra rules per sector without forking | Rule registry with entry points | `canoa_rules_<sector>` packages discovered via `importlib.metadata.entry_points` |
| Web UI for analysts | Upload, see report inline, download fixes checklist | Service API | Out of scope for the CLI project |
| QML legend import | Read QGIS `.qml` styles to derive legends automatically | Decision in `open-questions.md` | Reader exists but is unused |
| Auto-fix suggestions | Propose corrected cells (capitalisation, punctuation, trailing CR/LF) in the report | Structured issues with `expected` params | Never writes to the input |
| Diff between two runs | Show what changed since the last submission | JSON report stored per run | Platform feature |
| Localised protocol PDF ↔ rule cross-reference | Link each report message to the protocol section | `protocol_section` in business-rules tables | Rendered as tooltip/footnote |
| Schema export | Emit JSON Schema / CSV template for each sheet from `SheetSpec` | `specs/sheets.py` (Phase 1) | Helps analysts start from a valid template |

Last synced with code: 3dcfdb1
