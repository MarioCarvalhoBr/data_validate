# Message catalog

## Current implementation

- Files: `data_validate/static/locales/{pt_BR,en_US}/messages.json`, shape
  `{"<key>": {"message": "<text with {placeholders}>"}}`.
- Loader: `helpers/tools/locale/language_manager.py::LanguageManager` — language decided by
  `<repo>/.config/store.locale` (BUG-004), `text(key, **kwargs)` does `str.format`; missing key
  returns `<'key' missing or invalid structure in 'lang'>`; missing placeholder prints a warning
  and returns the raw template.
- Consumers: `FileSystemUtils`, `FileStructureValidator`, `ApplicationConfig.get_verify_names`
  (35 `verification_name_*` titles), `ValidationReport.flatten` (`model_report_msg_*_omitted`).
- Everything else (models, validators, helpers, spell-check, report labels) uses hard-coded
  pt-BR f-strings (ARC-005).

### Inventory issues (BUG-016)

| Issue | Detail |
|---|---|
| Parity | en_US lacks `validator_structure_error_conflicting_files`, `validator_structure_error_files_not_in_folder`, `validator_structure_error_missing_file`, `validator_structure_error_unexpected_folder` |
| Junk | Both files contain calculator-demo keys (`welcome`, `menu_title`, `add_option`, `subtract_option`, …) |
| Naming | Mixed prefixes (`fs_utils_*`, `validator_structure_*`, `verification_name_*`, `model_report_*`) with no documented convention |
| Placeholders | Not documented per key; no test that both locales use the same placeholder set |

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

Last synced with code: 3dcfdb1
