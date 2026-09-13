# Territories — optional server registry `spd_data.json`

Source: **maintainer decisions, 2026-09-12** (authoritative), example file
`local_data/ULTIMA_IMPLEMENTACAO/spd_data.json`. The Canoa **server** generates this file and may
pass it alongside the bundle. Three decisions define the semantics:

1. **Own verification category** — the territory check is a first-class verification with its own
   report title (a new `NamesEnum`-style member, working name `TERR` /
   `verification_name_territory_registry`) and its own title + message keys in **both** locale
   catalogs. It is never folded into an existing category.
2. **Triggered only when `spd_data.json` is present** in the input folder. When the file is
   absent, the verification appears in the report as **skipped / not executed** — never as an
   error, never silently missing (skipped-with-reason in the target engine, ADR-0006).
3. **Findings are always errors** (`Severity.ERROR`), never warnings: a `valores` or
   `proporcionalidades` id that does not exist in the registry is an error.

Protocol basis: v1.16 §2.6 (p.11) requires the `id` column of `valores` to reference the spatial
representation ("deverão ter todos os objetos descritos no shapefile ou, no caso de dados para
todo o Brasil, todos os municípios brasileiros"); §3.2 delivers the spatial data itself to the
platform administrator and §3 states those deliverables are not used in validation. The registry
JSON artefact is therefore **not specified in the protocol PDF** — it is the server-side bridge
the maintainer defined so Canoa can enforce the §2.6 relationship. Note the direction: the TERR
rules below check the spreadsheets' ids are a **subset** of the registry; full **completeness**
(every registry id present in `valores`) remains an open owner decision (gap G-13).

## Artefact

| Property | Value |
|---|---|
| File name | `spd_data.json` (input folder, alongside the sheets) |
| Required | no — optional, server-generated |
| Format | JSON, UTF-8: `{"values": [{"id": int, "name": str, "region": str}, …]}` (extra keys per entry tolerated) |
| Loading | through the loading layer only (never parsed ad hoc); untrusted input — size-limited (`MAX_INPUT_FILE_BYTES`, SEC-003), stdlib `json`, specific exceptions (`OSError`, `json.JSONDecodeError`, `UnicodeDecodeError`, and a `ValueError` for a well-formed-JSON-but-wrong-shape payload) |
| File-structure impact | whitelisted so STRUCT-004 does not flag it as "arquivo não esperado" |

Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade._load_territory_registry`
(returns a `TerritoryRegistry` frozen dataclass — `ids: frozenset[int]`, `loaded: bool`,
`error: str | None` — on the new `LoadResult.territory_registry` field); the whitelist is
`specs/sheet_specs.py::EXTRA_INPUT_FILES` (`("spd_data.json",)`), consumed by
`rules/structure.py::check_no_unexpected_files` (STRUCT-004) via an exact-name match, independent
of the `<base>.<ext>`/`SHEET_SPECS` shape every declared sheet otherwise follows. Covered by
tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py::
TestDataLoaderFacadeTerritoryRegistry`, `tests/unit/rules/test_structure.py::
TestCheckNoUnexpectedFiles` (whitelist cases).

## Rules

### TERR-001 · Every `valores.id` exists in the territory registry
- Severity: error (maintainer decision — never a warning)
- NamesEnum: new dedicated member `TERR` (`verification_name_territory_registry`) — own report
  category, title registered in both catalogs
- Protocol: v1.16 §2.6 p.11 (relationship); artefact by maintainer decision 2026-09-12
- Statement: when `spd_data.json` is present, every value in the `id` column of `valores` must
  equal the `id` of some entry in the registry's `values` list. Unknown ids are reported per id
  with the row number. When the file is absent, the whole `TERR` verification is reported as
  skipped / not executed.
- Current message (pt-BR): `rule.TERR-001.error` — "{filename}, linha {row}: O identificador
  '{value}' da coluna 'id' não foi encontrado no cadastro de territórios (spd_data.json)."
- Implemented by: `rules/territories.py::check_values_ids_in_registry` (`TERRITORY_REGISTRY_RULES`,
  `RuleSpec.requires_options=("territory_registry_present",)` — an absent/malformed registry
  engine-skips this rule with `SkipReason.DISABLED_BY_OPTION`, `rules/engine.py`)
- Covered by tests: `tests/unit/rules/test_territories.py::TestCheckValuesIdsInRegistry`,
  `::TestTerritoryRegistryEngineGating`; golden fixtures `data_ground_truth_02_registry`
  (present, valid, zero errors) and `data_errors_16_registry` (present, unknown ids)

### TERR-002 · Every `proporcionalidades.id` exists in the territory registry
- Severity: error (maintainer decision — never a warning)
- NamesEnum: same dedicated `TERR` category as TERR-001
- Protocol: v1.16 §2.7 pp.12–13 (the first columns carry the spatial representation); artefact by
  maintainer decision 2026-09-12
- Statement: when `spd_data.json` is present, every value in the `id` column (level-2 header) of
  `proporcionalidades` must exist among the registry ids; skipped when the file or the sheet is
  absent.
- Current message (pt-BR): `rule.TERR-002.error` — same wording as TERR-001, naming
  `proporcionalidades.xlsx` and the row (double-header offset, `idx + 3`).
- Implemented by: `rules/territories.py::check_proportionality_ids_in_registry`. Note: a real
  bundle's `proporcionalidades.id` column is `("Unnamed: 0_level_0", "id")` under pandas'
  `header=[0, 1]` read (the top header cell above `id` is blank), never `("id", "id")` — this rule
  locates the column by level 1 (`_proportionality_id_column`), the same problem
  `rules/proportionality.py::_proportionality_missing_id` solves for every `PROP-*` rule; a naive
  `"id" in frame.columns`/`frame[("id", "id")]` lookup silently finds nothing against real data.
- Covered by tests: `tests/unit/rules/test_territories.py::TestCheckProportionalityIdsInRegistry`
  (incl. a regression case reproducing the real, blank-top-header column shape); golden fixtures
  `data_ground_truth_02_registry`/`data_errors_16_registry` (the latter's registry omits an id
  referenced by both `valores` and `proporcionalidades`, exercising TERR-001 and TERR-002 together)

## Registry integrity (pre-checks before the rules run)

Malformed registry — invalid JSON, a non-`dict` root, a missing/non-list `values`, or an entry
whose `id` is not an `int` (a `bool` is rejected too — `isinstance(True, int)` is `True` in
Python, but a boolean is not a territory id) — is reported as a loading error for `spd_data.json`
(FS category, `loader_error_registry_invalid`) and both TERR rules are engine-skipped
(`SkipReason.DISABLED_BY_OPTION`) — never a crash.

**Resolved ambiguity (2026-09-13, PROTO-013 implementation)**: duplicate registry ids are *not*
part of the malformed/fatal case above — they are a registry defect (server-side), reported as a
**warning** (`loader_warning_registry_duplicate_ids`, FS category), and the registry still loads
successfully (deduplicated: `TerritoryRegistry.loaded is True`, `.ids` is the unique set) — both
TERR rules run normally against it.

Last synced with code: PROTO-013/PROTO-018 implementation (Phase 6 round N3, 2026-09-13)

## JSON summary flag: `spatial_data_validated`

Maintainer requirement (2026-09-12): the machine-readable stdout summary
(`<{"data_validate": {...}}>`) gains a boolean field named `spatial_data_validated`
(the English name chosen for "dados_espaciais_validados"):

- `true` — `spd_data.json` was provided, loaded successfully, the TERR verification ran
  and produced **zero errors** (every `valores.id` and `proporcionalidades.id` found in
  the registry).
- `false` — every other case: file absent, file malformed/unreadable, or TERR errors found.

Interpretation note: "passado e validado" is read as "provided AND validation passed";
if the maintainer instead means merely "provided and the check executed", flip the
malformed/errors cases — confirm before implementing PROTO-018. The field sits inside
the `data_validate` object next to `report` (`{"data_validate": {"version": ...,
"spatial_data_validated": false, "report": {...}}}`) and is ALWAYS present so the
platform can rely on its shape. The `--json` file output carries the same field.

**Implemented** (PROTO-018, Phase 6 round N3, 2026-09-13): "passado e validado" was resolved as
"provided AND validation passed" (the first reading above), matching the maintainer's original
statement. `GeneralContext.spatial_data_validated` (`controllers/context/general_context.py`) is
computed by `SpreadsheetProcessor._finalize_territory_registry_status`
(`controllers/spreadsheet_processor.py`), once `TERRITORY_REGISTRY_RULES` has run, as
`territory_registry.loaded and not terr_report.has_errors()`; `FileReportGenerator.
_print_json_summary` (stdout) and `main.py::_build_json_summary` (`--json PATH`) both read it, so
the two outputs never disagree. Mirrored in `.specs/api/cli-contract.md`'s JSON schema. Covered by
tests: `tests/unit/controllers/test_spreadsheet_processor.py::TestFinalizeTerritoryRegistryStatus`,
`tests/unit/controllers/report/test_file_report_generator.py::TestPrintJsonSummary`,
`tests/unit/test_main.py::TestMainJsonOutput`; golden fixtures `data_ground_truth_02_registry`
(`true`) and `data_errors_16_registry` (`false`, TERR errors present).
