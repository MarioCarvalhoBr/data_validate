# File structure, loading and generic structural rules

Scope: the input folder as a whole, file discovery/loading, and the structural checks applied to
every sheet before business rules run. Protocol §2 (p.3).

## Expected bundle

| Base name | Required | Extensions | Header layout | CSV separator | Model |
|---|---|---|---|---|---|
| `descricao` | yes | `.xlsx`, `.csv` | single | `\|` | `SpDescription` |
| `composicao` | yes | `.xlsx`, `.csv` | single | `\|` | `SpComposition` |
| `valores` | yes | `.xlsx`, `.csv` | single | `\|` | `SpValue` |
| `referencia_temporal` | yes | `.xlsx`, `.csv` | single | `\|` | `SpTemporalReference` |
| `proporcionalidades` | no | `.xlsx`, `.csv` | **double** (rows 1–2) | `\|` | `SpProportionality` |
| `cenarios` | no | `.xlsx`, `.csv` | single | `\|` | `SpScenario` |
| `legenda` | no | `.xlsx`, `.csv` | single | `\|` | `SpLegend` |
| `dicionario` | no | `.xlsx`, `.csv` | single | `\|` | `SpDictionary` |

Sources: `config/spreadsheet_info.py::SpreadsheetInfo` (names, extensions, expected/optional) and
`data_validate/specs/sheet_specs.py::SHEET_SPECS` (required flag, header type, separator — the
loader's actual source since BUG-018/ARC-003; the former second source,
`helpers/tools/data_loader/common/config.py::Config`, including its stray `.qml` entry, is
deleted).

Loading facts (`helpers/tools/data_loader/**`):
- All cells are read as `str` (`dtype=str`); Excel via `calamine`, CSV via `pd.read_csv(sep="|")`
  (the separator is `SHEET_SPECS[name].csv_separator`, passed explicitly to `CSVReader`, not
  guessed from the file stem — BUG-018).
- Double header CSV: level-0 labels are forward-filled over `Unnamed:*`/empty cells
  (`readers/csv_reader.py`), mirroring merged cells in Excel.
- When both `.csv` and `.xlsx` exist, `FileScanner.scan()` keeps the `.csv` and records the losing
  path in its `ignored` result (not silently dropped, though nothing downstream consumes it yet)
  while STRUCT-006 independently reports the conflict as an error.
- A file that fails to load is represented as an empty frame with `is_read_successful=False`; the
  four required and four optional names always exist in the loaded map.
- SEC-003: a file above `ApplicationConfig.MAX_INPUT_FILE_BYTES` (100 MB) is never read; a sheet
  that reads successfully but exceeds `MAX_SHEET_ROWS` (1,000,000) or `MAX_SHEET_COLUMNS` (5,000)
  is discarded and treated as unread — both a generous denial-of-service guard, not a business
  limit. See STRUCT-015.

## Rules

### STRUCT-001 · Input directory must not be empty
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2 p.3 (single folder with the listed files)
- Statement: the input directory must contain at least one entry.
- Current message (pt-BR): catalog key `validator_structure_error_empty_directory` — `O diretório '{dir_path}' está vazio. Por favor, adicione os arquivos necessários.` (present in both locales)
- Target message key: `rule.STRUCT-001.error`
- Implemented by: `rules/structure.py::check_input_directory_not_empty` (ARC-017 Phase 3b port; the
  deleted `validators/structure/file_structure_validator.py::FileStructureValidator.
  check_empty_directory` is the legacy predecessor)
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckInputDirectoryNotEmpty` (helper
  it used to call, `FileSystemUtils.check_directory_is_empty`, is unused by the port and remains
  covered by `tests/unit/helpers/base/test_file_system_utils.py`)
- Notes / known defects: one of the few rules already using the i18n catalog.

### STRUCT-002 · Files must be in the root, not inside a single subfolder
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 ("entregues em uma única pasta")
- Statement: if the input directory contains exactly one entry and it is a directory, the bundle was zipped with an extra folder level; abort structural checks with this error.
- Current message (pt-BR): key `validator_structure_error_files_not_in_folder` — `Os arquivos não podem estar dentro de uma pasta. Eles devem ser zipados diretamente.` (present in both locales)
- Target message key: `rule.STRUCT-002.error`
- Implemented by: `rules/structure.py::check_files_not_zipped_inside_a_folder` (ARC-017 Phase 3b
  port of the deleted `FileStructureValidator.check_not_expected_files_in_folder_root`'s first
  branch); `rules/structure.py::_is_zipped_with_extra_folder` is the shared gate STRUCT-003/
  STRUCT-004 also consult so the single subfolder entry is reported once, not three times
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckFilesNotZippedInsideAFolder`
- Notes / known defects: the "missing from `en_US`" note (BUG-016) was stale — both locales already
  carry this key.

### STRUCT-003 · No unexpected folders in the root
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3
- Statement: every entry in the input directory must be a regular file; directories are reported.
- Current message (pt-BR): key `validator_structure_error_unexpected_folder` — `A pasta '{file_name}' não é esperada.` (present in both locales)
- Target message key: `rule.STRUCT-003.error`
- Implemented by: `rules/structure.py::check_no_unexpected_folders` (ARC-017 Phase 3b port of the
  deleted `FileStructureValidator.check_not_expected_files_in_folder_root`)
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckNoUnexpectedFolders`
- Notes / known defects: the legacy `.format()`-on-an-unformatted-template call is gone — the port
  renders through a single `ctx.translate(message_key, **params)` call, byte-identical output
  (verified by the e2e golden harness); the "missing from `en_US`" note (BUG-016) was stale — both
  locales already carry this key.

### STRUCT-004 · No unexpected files in the root
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (file names are fixed, no accents)
- Statement: every file must be `<base>.<ext>` with `<base>` in the expected or optional set and `<ext>` in `{.csv, .xlsx}`; anything else (e.g. `Descricao.xlsx`, `legenda.qml`, `arquivo_aleatorio.xlsx`) is an error. Matching is case-sensitive. **Exception (PROTO-013)**: an exact-name match against `EXTRA_INPUT_FILES` (`spd_data.json`, the optional territory registry — `.specs/business-rules/territories.md`) is accepted too, even though it is not a declared sheet and does not follow the `<base>.<ext>` shape.
- Current message (pt-BR): key `validator_structure_error_unexpected_file` — `O arquivo '{file_name}' não é esperado.` (present in both locales)
- Target message key: `rule.STRUCT-004.error`
- Implemented by: `rules/structure.py::check_no_unexpected_files` (ARC-017 Phase 3b port of the
  deleted `FileStructureValidator.check_not_expected_files_in_folder_root`; the expected/optional
  stem set now comes from `data_validate.specs.sheet_specs.SHEET_SPECS`/`ALLOWED_EXTENSIONS`, not
  `SpreadsheetInfo.EXPECTED_FILES`/`OPTIONAL_FILES` — both sources agree today, see ADR-0003).
  PROTO-013 (Phase 6 round N3): the `spd_data.json` exception checks
  `data_validate.specs.sheet_specs.EXTRA_INPUT_FILES` by exact file name, ahead of the
  `<base>.<ext>`/`SHEET_SPECS` check.
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckNoUnexpectedFiles` (incl. the
  `spd_data.json` whitelist cases)
- Notes / known defects: none — the loader no longer scans `.qml` files at all (BUG-015 done); a
  `.qml` file in the input folder is simply not picked up by `FileScanner`, and this rule still
  reports it as an unexpected file via the directory listing.

### STRUCT-005 · Required files must exist
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (items 2.2, 2.3, 2.4, 2.6 are not marked optional)
- Statement: `descricao`, `composicao`, `valores`, `referencia_temporal` must each exist with one of the allowed extensions.
- Current message (pt-BR): key `validator_structure_error_missing_file` — `{file_base}: O arquivo esperado não foi encontrado. Use .csv ou .xlsx como extensões.` (present in both locales)
- Target message key: `rule.STRUCT-005.error`
- Implemented by: `rules/structure.py::check_required_files_present` (ARC-017 Phase 3b port of the
  deleted `FileStructureValidator.check_expected_files_in_folder_root`; iterates
  `data_validate.specs.sheet_specs.SHEET_SPECS`, filtered to `required`, in the same
  descricao/composicao/valores/referencia_temporal declaration order as the legacy
  `SpreadsheetInfo.EXPECTED_FILES` dict)
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckRequiredFilesPresent`
- Notes / known defects: the "missing from `en_US`" note (BUG-016) was stale — both locales already
  carry this key.

### STRUCT-006 · A sheet must not be delivered in both CSV and XLSX
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour
- Statement: for every base name, at most one of `.csv`/`.xlsx` may exist.
- Current message (pt-BR): key `validator_structure_error_conflicting_files` — `{file_base}: Existe um arquivo .csv e um arquivo .xlsx com o mesmo nome. Será considerado o arquivo .csv.` (present in both locales)
- Target message key: `rule.STRUCT-006.error`
- Implemented by: `rules/structure.py::check_no_csv_xlsx_conflict` (ARC-017 Phase 3b port of the
  deleted `FileStructureValidator.check_ignored_files_in_folder_root`)
- Covered by tests: `tests/unit/rules/test_structure.py::TestCheckNoCsvXlsxConflict`
- Notes / known defects: the message itself states the CSV is used, consistent with
  `FileScanner`'s documented CSV-over-XLSX preference (BUG-015 done — the policy is now explicit
  in `engine/scanner.py`'s docstring and the losing path is returned as `ignored`, not silently
  dropped); the "missing from `en_US`" note (BUG-016) was stale — both locales already carry this
  key.

### STRUCT-007 · Files must be readable
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (UTF-8), §6 p.18 ("O arquivo XXX está no formato YYY, deveria ser UTF-8")
- Statement: each discovered file must be parsed by pandas; failures are reported per exception type (not found, encoding, parser/merged cells, value/type, I/O, unexpected) and the sheet is treated as empty and unread.
- Current message (pt-BR): `{path.name}: Arquivo não encontrado no diretório. Detalhes: {e} ({type(e)})` · `{path.name}: Erro de codificação do arquivo. Verifique se está em UTF-8. Detalhes: …` · `{path.name}: Erro na estrutura da planilha. Verifique se há células mescladas ou formato inválido. Detalhes: …` · `{path.name}: Erro nos valores da planilha. Verifique se os tipos de dados estão corretos. Detalhes: …` · `{path.name}: Erro de entrada/saída ao ler o arquivo. Verifique se ele não está aberto em outro programa. Detalhes: …` · `{path.name}: Erro inesperado ao processar o arquivo. Detalhes: …`
- Target message key: `rule.STRUCT-007.error` (one key per cause: `.not_found`, `.encoding`, `.parser`, `.value`, `.io`, `.unexpected`)
- Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()` (the
  deprecated `load_all` property wraps the same logic for one release, ARC-009)
- Covered by tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py`
- Notes / known defects: raw exception text is leaked to the user; encoding is never proactively detected (`FileSystemUtils.detect_encoding` unused) — gap G-01. SEC-004: the "unexpected" cause is
  now specifically `python_calamine.CalamineError` (the base of `python-calamine`'s
  `ZipError`/`XmlError`/`PasswordError`, raised by pandas' `engine="calamine"` for a
  malformed/corrupt `.xlsx`) rather than a catch-all `except Exception` — a reader failure that
  isn't one of these six documented causes now propagates out of `load()` and reaches `main()`'s
  boundary as a fatal error (exit code 2) instead of being silently downgraded to a per-file
  message.

### STRUCT-008 · A delivered file must not be empty
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour
- Statement: a file that loads successfully but yields zero rows/columns is an error.
- Current message (pt-BR): `{filename}: O arquivo enviado está vazio.`
- Target message key: `rule.STRUCT-008.error`
- Implemented by: `models/sp_model_abc.py::SpModelABC.initialize`
- Covered by tests: none — TST-001
- Notes / known defects: runs for every model including absent optional files (guarded by `is_read_successful`).

### STRUCT-009 · The vertical bar `|` is forbidden in headers and data
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 ("O caractere barra vertical (|) é reservado para uso interno da ferramenta e não poderá existir nos arquivos entregues")
- Statement: no column name (any header level) and no cell may contain `|`. One message per offending header and per offending cell.
- Current message (pt-BR): `{file_name}: A coluna '{column_name}' não pode conter o caractere '|'.` · `{file_name}: O nome da coluna de nível 0 '{col}' não pode conter o caracter '|'.` · `{file_name}: O nome da subcoluna de nível 1 '{col1}' do pai '{col0}' de nível 0 não pode conter o caracter '|'.` · `{file_name}, linha {row_idx + 2}: A coluna '{col_display_name}' não pode conter o caracter '|'.`
- Target message key: `rule.STRUCT-009.error`
- Implemented by: `helpers/common/validation/dataframe_processing.py::DataFrameProcessing.check_dataframe_vertical_bar`, called from `SpModelABC.initialize`
- Covered by tests: `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: converts the whole frame to `str` (PERF-002); for CSV a `|` in data cannot survive parsing, so the check is effective for XLSX only; double-header row offset is still `+2` (should be `+3`). SEC-004: the function no longer wraps its pure-pandas logic in a broad
  `except Exception` (the dead "on exception" message is gone) — there is no plausible failure in
  this code path, so a genuine programming error now propagates instead of being reported as a
  data-quality issue.

### STRUCT-010 · A row may not have more values than named columns
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour (detects data under unnamed/blank headers)
- Statement: count columns whose name (level 1 for double headers) starts with `unnamed`; any row whose number of non-null cells exceeds the number of named columns is an error.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: A linha possui {n} valores, mas a tabela possui apenas {valid_columns_count} coluna(s) válida(s).`
- Target message key: `rule.STRUCT-010.error`
- Implemented by: `dataframe_processing.py::DataFrameProcessing.check_dataframe_unnamed_columns`, called from `SpModelABC.initialize`
- Covered by tests: `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: SEC-004: the function no longer wraps its pure-pandas logic in a broad
  `except Exception` (the dead "on exception" message, `{file_name}: Erro ao processar a checagem
  de colunas sem nome: {e}`, is gone) — a genuine programming error now propagates instead of
  being reported as a data-quality issue.

### STRUCT-011 · Expected columns must be present
- Severity: error
- NamesEnum: FS
- Protocol: §2.1–2.8 column lists
- Statement: every column in the model's expected list must exist (exact, case-sensitive name, no accents). Expected lists: see each sheet file. `valores`/`proporcionalidades` apply pattern-based variants (VAL-001, PROP-002).
- Current message (pt-BR): `{file_name}: Coluna '{col}' esperada mas não foi encontrada.`
- Target message key: `rule.STRUCT-011.error`
- Implemented by: `helpers/common/formatting/message_formatting_processing.py::MessageFormattingProcessing.format_text_to_missing_and_expected_columns` fed by `dataframe_processing.py::DataFrameProcessing.check_dataframe_column_names`, called from each model's `expected_structure_columns`
- Covered by tests: `tests/unit/helpers/common/formatting/test_message_formatting_processing.py`, `tests/unit/helpers/common/validation/test_column_validation.py`
- Notes / known defects: —

### STRUCT-012 · Unexpected columns are ignored with a warning
- Severity: warning
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour
- Statement: columns not in the expected list (excluding names starting with `unnamed`) are reported and ignored.
- Current message (pt-BR): `{file_name}: Coluna '{col}' será ignorada pois não está na especificação.`
- Target message key: `rule.STRUCT-012.warning`
- Implemented by: same as STRUCT-011
- Covered by tests: same as STRUCT-011
- Notes / known defects: for `descricao`, `relacao`/`unidade` are injected onto `SpDescription.frame` before this check (BUG-003, fixed — the injection target moved off the shared `raw_data`, behaviour unchanged), so they never appear as extra.

### STRUCT-015 · Oversized files and sheets are rejected (SEC-003)
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour (denial-of-service guard against zip-bomb-style
  or accidental huge input)
- Statement: a delivered file above `ApplicationConfig.MAX_INPUT_FILE_BYTES` (100 MB, checked via
  `Path.stat()` before the file is read) is never read; a sheet that reads successfully but exceeds
  `MAX_SHEET_ROWS` (1,000,000) or `MAX_SHEET_COLUMNS` (5,000) is discarded (treated the same as an
  unread file) rather than held in memory. Both limits are generous DoS guards, not business rules.
- Current message (pt-BR): catalog key `loader_error_file_too_large` — `{filename}: O arquivo
  excede o tamanho máximo permitido ({size_mb} MB > {limit_mb} MB) e não será lido.` · catalog key
  `loader_error_sheet_too_big` — `{filename}: A planilha excede o tamanho máximo permitido ({rows}
  linhas x {columns} colunas > {max_rows} linhas x {max_columns} colunas) e não será lida.`
  (present in both locales)
- Target message key: `rule.STRUCT-015.error` (`.file_too_large`, `.sheet_too_big`)
- Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()` — limits are
  injected through the constructor (`limits` tuple) by `controllers/spreadsheet_processor.py::
  SpreadsheetProcessor._read_data`, which reads the canonical values off
  `config/application_config.py::ApplicationConfig`; the loading layer never imports `config`
  directly (`.claude/rules/architecture-boundaries.md`)
- Covered by tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py::TestDataLoaderFacadeSizeLimits`
- Notes / known defects: unlike `load_all`'s pre-existing per-exception messages (STRUCT-007, still
  hardcoded pt-BR strings), this rule's two messages go through an injected `translate` callable
  (defaulting to a `pt_BR` `MessageCatalog` when the facade is built without a `GeneralContext`),
  per `.claude/rules/i18n.md` — migrating STRUCT-007 to the same pattern is left to BUG-015/ARC-003.

### STRUCT-013 · Proactive UTF-8 encoding check (FAQ message shape)
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2 p.3 (UTF-8 requirement) + FAQ "O arquivo XXX está no formato YYY, deveria ser UTF-8."
- Statement: on load, every `.csv` file (never `.xlsx` — a zip container, exempt) has a sample of
  its raw bytes read; when the sample fails to decode as UTF-8 and `chardet`'s own guess over the
  same sample is confident (`>= 0.7`) and names an encoding other than UTF-8/ASCII, report the
  FAQ's exact message shape. A low-confidence guess is not reported (avoids a false positive on a
  genuinely UTF-8 file with only a couple of accented characters, which `chardet` alone can
  mis-detect as `ISO-8859-1`). Does not block the subsequent read attempt — a genuinely
  undecodable file still also raises STRUCT-007's own, more specific error.
- Current message (pt-BR): catalog key `rule.STRUCT-013.error` — `O arquivo {filename} está no
  formato {encoding}, deveria ser UTF-8.` (present in both locales)
- Target message key: `rule.STRUCT-013.error`
- Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()` (module-level
  `_detect_non_utf8_encoding`), a loader-level check (not a `RuleSpec`) appended straight to
  `LoadResult.errors`, the same shape STRUCT-015's size-limit errors use
- Covered by tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py::
  TestDataLoaderFacadeStructuralChecks`
- Notes / known defects: resolves gap G-01 (PROTO-007). The bundle's own `.csv` fixture
  (`data_errors_xss/descricao.csv`) is genuinely UTF-8 with high `chardet` confidence, so this
  rule never fires against a shipped fixture — verified before the golden re-baseline.

### STRUCT-014 · Each `.xlsx` must contain exactly one worksheet
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2 p.3 (since v1.14)
- Statement: on load, every `.xlsx` file's worksheet names are read via
  `python_calamine.CalamineWorkbook.from_path(...).sheet_names`; more than one worksheet is an
  error naming the file, the first (still-used) sheet, and every extra sheet. Does not block the
  subsequent read — the first sheet is still parsed and validated, matching calamine's own
  "reads the first sheet" behaviour, now surfaced instead of silent. A file this check cannot even
  open (corrupt zip, vanished path) is silently skipped by this check alone; the real read
  attempt right after still reports its own STRUCT-007 error with its own message.
- Current message (pt-BR): catalog key `rule.STRUCT-014.error` — `{filename}: O arquivo Excel
  possui mais de uma planilha; apenas a primeira ('{first_sheet}') será considerada. Planilhas
  extras: {extra_sheets}.` (present in both locales)
- Target message key: `rule.STRUCT-014.error`
- Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()` (module-level
  `_worksheet_names`), a loader-level check (not a `RuleSpec`) appended straight to
  `LoadResult.errors`
- Covered by tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py::
  TestDataLoaderFacadeStructuralChecks` (a real, hand-built two/three-sheet `.xlsx` under
  `tmp_path` — no `.xlsx`-writing dependency is available in this project, see the test helper's
  docstring)
- Notes / known defects: resolves gap "calamine reads the first sheet silently" (PROTO-003). No
  fixture under `data/input/` has more than one worksheet (verified against every fixture before
  the golden re-baseline), so this rule never fires against a shipped fixture.

## Gaps (protocol ↔ code)

- **G-01 UTF-8 encoding** (resolved, PROTO-007): STRUCT-013 now detects a confidently non-UTF-8
  CSV proactively via `chardet`, with the FAQ's exact message shape.
- **G-02 `|` in CSV**: impossible to detect after `pd.read_csv(sep="|")`; would need a pre-parse scan of raw text.
- **G-03 decimal comma**: the protocol mandates comma as decimal separator in CSV; code accepts both `,` and `.` everywhere (lenient, undocumented).
- **G-04 `.qml`** (resolved, BUG-015/ADR-0003): was still scanned (`Config.extensions`) though
  removed from the protocol in v1.11; `.qml` scanning, `QMLReader` and the `Config` singleton are
  now deleted — a `.qml` file is no longer read at all, only ever reported as unexpected (STRUCT-004).

## Protocol v1.16 update (2026-09-12)

- **Single-worksheet xlsx** (v1.14, resolved PROTO-003): each `.xlsx` must contain exactly one
  worksheet; STRUCT-014 now reports the extra sheets instead of the calamine reader silently
  loading only the first.
- **Optional `spd_data.json`** (maintainer decision 2026-09-12, see
  [territories.md](territories.md); **resolved, PROTO-013, Phase 6 round N3**): the
  server-generated territory registry may accompany the bundle; STRUCT-004 whitelists it
  (`EXTRA_INPUT_FILES`) instead of reporting "arquivo não esperado".
- UTF-8 proactive check (G-01, resolved PROTO-007): STRUCT-013 implements the v1.16 FAQ's exact
  expected message.

Last synced with code: Phase 6 round N3, 2026-09-13 (PROTO-013: STRUCT-004 whitelists
`spd_data.json`; `DataLoaderFacade` also loads the optional territory registry directly)
