# Message catalog

## Current implementation

- Files: `data_validate/static/locales/{pt_BR,en_US}/messages.json`, shape
  `{"<key>": {"message": "<text with {placeholders}>"}}`. As of this sync each locale file has
  **137 keys**, byte-parity confirmed (`grep -c` over both files agrees; `tests/unit/i18n/
  test_catalog_parity.py` guards key-set/placeholder/shape parity in CI).
- Loader: `helpers/tools/locale/language_manager.py::LanguageManager` — takes an explicit `locale`
  constructor argument (no more `.config/store.locale` file I/O, BUG-004); `text(key, **kwargs)`
  does `str.format`; missing key returns `<'key' missing or invalid structure in 'lang'>`; missing
  placeholder logs a warning (`logging`, not `print` — ARC-012) and returns the raw template.
- Consumers today: every one of the nine `rules/*.py` registries (structure, description,
  composition, temporal reference, value, scenario, legend, proportionality, spell — ARC-017
  Phase 3, all ports complete) renders through `ctx.translate(message_key, **params)` against the
  `rule.<RULE-ID>.<kind>` keys below; `ApplicationConfig.get_verify_names` (34
  `verification_name_*` titles), `ValidationReport.flatten` (`model_report_msg_*_omitted`),
  `FileSystemUtils`/loader size-limit errors (`loader_error_file_too_large`,
  `loader_error_sheet_too_big` — SEC-003), and `LanguageManager`'s own `invalid_language`/
  `lang_load_error` keys are unchanged legacy consumers.
- Not yet catalog-backed (ARC-005, in-progress): ~15 hardcoded pt-BR f-strings inside
  `models/sp_*.py`'s structural/data-cleaning checks (`SpModelABC.initialize`,
  `pre_processing`/`data_cleaning` across the eight models) and the report labels/section titles
  in `controllers/report/file_report_generator.py`'s Jinja template — both a deliberately deferred
  follow-up per ARC-016/ADR-0007's "Implementation note", not an oversight.

### Key inventory by prefix (DOC-003 — closed; grep-verified 2026-09-13)

| Prefix | Count (each locale) | Status |
|---|---|---|
| `rule.*` | **77** | Target convention (`rule.<RULE-ID>.<kind>` / `rule.<area>.<slug>` for shared abort-case keys), live for every ported validation rule — DESC/COMP/TEMP/SCEN/VAL/LEG/PROP/SPELL/STRUCT all render through it (ARC-005/ARC-017 Phase 3) |
| `verification_name_*` | 34 | Legacy — the `NamesEnum`-keyed category titles shown in the report's section headings; kept by design, not a rule-ID key (one per verification category, not per rule) |
| `fs_utils_*` | 14 | Legacy — `FileSystemUtils`/loader size-limit and filesystem error strings; kept by design (utility-layer errors, not business rules) |
| `validator_structure_*` | 6 | Legacy naming surviving on `STRUCT-*` keys' shared abort message (structure rules were the first port, before the `rule.` convention existed); functionally equivalent to a `rule.structure.*` key, renamed only if a future slice touches `rules/structure.py`'s message keys — not scheduled |
| `model_report_*` | 2 | Legacy — `ValidationReport.flatten`'s per-category/per-severity omitted-count notices |
| `loader_error_*` | 2 | Legacy — `SheetLoader`/reader size-limit errors (SEC-003); named `loader_error_*` rather than `fs_utils_*`, a second legacy prefix this sync found and is recording here for the first time |
| `invalid_language`, `lang_load_error` | 2 | Legacy — `LanguageManager`'s own bootstrap errors (kept intentionally per BUG-016's note; used before a locale is even resolved, so a `rule.`/`load.` key would be circular) |
| **Total** | **137** | — |

The mixed-prefix legacy keys (`fs_utils_*`, `validator_structure_*`, `verification_name_*`,
`model_report_*`, `loader_error_*`, plus the two `LanguageManager` bootstrap keys) remain **by
design**: they are titles (`verification_name_*`), utility/loader-layer errors
(`fs_utils_*`/`loader_error_*`), or bootstrap-time strings that predate rule-ID keys, not business
rules with a `RULE-ID` to key on. Migrating them to the `<area>.<identifier>.<kind>` convention
below is optional polish, not a blocking gap — DOC-003 is closed on the strength of "every rule ID
has a catalog key in both locales", not "every string is `rule.`-prefixed".

## Target

### Key convention

`<area>.<identifier>.<kind>` — lowercase, dots as separators, identifier stable.

| Area | Identifier | Kind | Example |
|---|---|---|---|
| `rule` | rule ID | `error`, `warning`, `title` (short description) | `rule.DESC-004.warning` |
| `category` | NamesEnum-compatible category key | `title` | `category.sequential_codes.title` |
| `engine` | skip/crash reasons | `reason` | `engine.skipped.missing_column.reason` |
| `report` | report labels and notices | `label`, `notice` | `report.label.errors_count`, `report.omitted.errors.notice` |
| `cli` | CLI help/usage strings | `help`, `error` | `cli.input.help` |
| `load` | loader errors | `error` | `load.encoding.error` |

### Placeholders

Named, documented next to the key in `business-rules/` tables, identical across locales:
`{sheet}`, `{row}`, `{column}`, `{value}`, `{expected}`, `{found}`, `{count}`, `{codes}`,
`{parent}`, `{child}`, `{level}`, `{min}`, `{max}`, `{legend}`, `{year}`. Lists are formatted by
the renderer (`, `-joined, sorted) before substitution; numbers by babel per locale.

### Rendering

`MessageCatalog.render(issue, locale) -> str` builds the conventional prefix
(`{sheet}, linha {row}: ` / `{sheet}, line {row}: `) from `Issue.sheet/row` and appends the
key's text. Missing key in the requested locale → fallback to pt_BR **and** a test failure in
CI (never silently in production: the fallback logs once).

### File layout

`data_validate/i18n/locales/pt_BR.json`, `en_US.json` — flat JSON, sorted keys, UTF-8, one
message per key (no nested `message` object). A migration script converts the current files.

### Parity process

`tools/i18n_check.py` (CI job `lint`, command `/i18n-check`):
1. Same key set in every locale.
2. Same placeholder set per key.
3. No key unused by code (`grep` of `rule.<ID>` / literal keys) and no literal user-facing
   f-string in `data_validate/rules/**`, `reporting/**` (heuristic: Portuguese diacritics inside
   f-strings).
4. Every rule ID in `business-rules/` has `rule.<ID>.<severity>` in both locales.

### Translation workflow

pt_BR is authored first (protocol language); en_US must be complete before a release. Reviewers
for en_US listed in `CODEOWNERS` for `i18n/locales/en_US.json`.

Last synced with code: 1325b48
