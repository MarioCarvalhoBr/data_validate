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

Sources: `config/spreadsheet_info.py::SpreadsheetInfo` (names, extensions, expected/optional),
`helpers/tools/data_loader/common/config.py::Config.file_specs` (required flag, header type,
separator; also lists `.qml`, which is scanned but unused — backlog BUG-015, ARC-003).

Loading facts (`helpers/tools/data_loader/**`):
- All cells are read as `str` (`dtype=str`); Excel via `calamine`, CSV via `pd.read_csv(sep="|")`.
- Double header CSV: level-0 labels are forward-filled over `Unnamed:*`/empty cells
  (`readers/csv_reader.py`), mirroring merged cells in Excel.
- When both `.csv` and `.xlsx` exist, the scanner keeps the `.csv` silently while STRUCT-006 reports
  the conflict as an error.
- A file that fails to load is represented as an empty frame with `is_read_successful=False`; the
  four required and four optional names always exist in the loaded map.

## Rules

### STRUCT-001 · Input directory must not be empty
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2 p.3 (single folder with the listed files)
- Statement: the input directory must contain at least one entry.
- Current message (pt-BR): catalog key `validator_structure_error_empty_directory` — `O diretório '{dir_path}' está vazio. Por favor, adicione os arquivos necessários.` (present in both locales)
- Target message key: `rule.STRUCT-001.error`
- Implemented by: `validators/structure/file_structure_validator.py::FileStructureValidator.check_empty_directory` (uses `FileSystemUtils.check_directory_is_empty`)
- Covered by tests: none — TST-001 (helper covered by `tests/unit/helpers/base/test_file_system_utils.py`)
- Notes / known defects: one of the few rules already using the i18n catalog.

### STRUCT-002 · Files must be in the root, not inside a single subfolder
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 ("entregues em uma única pasta")
- Statement: if the input directory contains exactly one entry and it is a directory, the bundle was zipped with an extra folder level; abort structural checks with this error.
- Current message (pt-BR): key `validator_structure_error_files_not_in_folder` — `Os arquivos não podem estar dentro de uma pasta. Eles devem ser zipados diretamente.` (pt_BR only)
- Target message key: `rule.STRUCT-002.error`
- Implemented by: `file_structure_validator.py::FileStructureValidator.check_not_expected_files_in_folder_root` (first branch)
- Covered by tests: none — TST-001
- Notes / known defects: key missing from `en_US` (BUG-016).

### STRUCT-003 · No unexpected folders in the root
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3
- Statement: every entry in the input directory must be a regular file; directories are reported.
- Current message (pt-BR): key `validator_structure_error_unexpected_folder` — `A pasta '{file_name}' não é esperada.` (pt_BR only)
- Target message key: `rule.STRUCT-003.error`
- Implemented by: `file_structure_validator.py::FileStructureValidator.check_not_expected_files_in_folder_root`
- Covered by tests: none — TST-001
- Notes / known defects: `.format()` is applied on the already-formatted catalog text; key missing from `en_US` (BUG-016).

### STRUCT-004 · No unexpected files in the root
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (file names are fixed, no accents)
- Statement: every file must be `<base>.<ext>` with `<base>` in the expected or optional set and `<ext>` in `{.csv, .xlsx}`; anything else (e.g. `Descricao.xlsx`, `legenda.qml`, `arquivo_aleatorio.xlsx`) is an error. Matching is case-sensitive.
- Current message (pt-BR): key `validator_structure_error_unexpected_file` — `O arquivo '{file_name}' não é esperado.` (present in both locales)
- Target message key: `rule.STRUCT-004.error`
- Implemented by: `file_structure_validator.py::FileStructureValidator.check_not_expected_files_in_folder_root`
- Covered by tests: none — TST-001
- Notes / known defects: the loader still scans `.qml` files (BUG-015).

### STRUCT-005 · Required files must exist
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (items 2.2, 2.3, 2.4, 2.6 are not marked optional)
- Statement: `descricao`, `composicao`, `valores`, `referencia_temporal` must each exist with one of the allowed extensions.
- Current message (pt-BR): key `validator_structure_error_missing_file` — `{file_base}: O arquivo esperado não foi encontrado. Use .csv ou .xlsx como extensões.` (pt_BR only)
- Target message key: `rule.STRUCT-005.error`
- Implemented by: `file_structure_validator.py::FileStructureValidator.check_expected_files_in_folder_root`
- Covered by tests: none — TST-001
- Notes / known defects: key missing from `en_US` (BUG-016).

### STRUCT-006 · A sheet must not be delivered in both CSV and XLSX
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour
- Statement: for every base name, at most one of `.csv`/`.xlsx` may exist.
- Current message (pt-BR): key `validator_structure_error_conflicting_files` — `{file_base}: Existe um arquivo .csv e um arquivo .xlsx com o mesmo nome. Será considerado o arquivo .csv.` (pt_BR only)
- Target message key: `rule.STRUCT-006.error`
- Implemented by: `file_structure_validator.py::FileStructureValidator.check_ignored_files_in_folder_root`
- Covered by tests: none — TST-001
- Notes / known defects: the message itself states the CSV is used, consistent with the scanner's silent preference (BUG-015); key missing from `en_US` (BUG-016).

### STRUCT-007 · Files must be readable
- Severity: error
- NamesEnum: FS
- Protocol: §2 p.3 (UTF-8), §6 p.18 ("O arquivo XXX está no formato YYY, deveria ser UTF-8")
- Statement: each discovered file must be parsed by pandas; failures are reported per exception type (not found, encoding, parser/merged cells, value/type, I/O, unexpected) and the sheet is treated as empty and unread.
- Current message (pt-BR): `{path.name}: Arquivo não encontrado no diretório. Detalhes: {e} ({type(e)})` · `{path.name}: Erro de codificação do arquivo. Verifique se está em UTF-8. Detalhes: …` · `{path.name}: Erro na estrutura da planilha. Verifique se há células mescladas ou formato inválido. Detalhes: …` · `{path.name}: Erro nos valores da planilha. Verifique se os tipos de dados estão corretos. Detalhes: …` · `{path.name}: Erro de entrada/saída ao ler o arquivo. Verifique se ele não está aberto em outro programa. Detalhes: …` · `{path.name}: Erro inesperado ao processar o arquivo. Detalhes: …`
- Target message key: `rule.STRUCT-007.error` (one key per cause: `.not_found`, `.encoding`, `.parser`, `.value`, `.io`, `.unexpected`)
- Implemented by: `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load_all`
- Covered by tests: `tests/unit/helpers/tools/data_loader/api/test_facade.py`
- Notes / known defects: raw exception text is leaked to the user; encoding is never proactively detected (`FileSystemUtils.detect_encoding` unused) — gap G-01.

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
- Current message (pt-BR): `{file_name}: A coluna '{column_name}' não pode conter o caractere '|'.` · `{file_name}: O nome da coluna de nível 0 '{col}' não pode conter o caracter '|'.` · `{file_name}: O nome da subcoluna de nível 1 '{col1}' do pai '{col0}' de nível 0 não pode conter o caracter '|'.` · `{file_name}, linha {row_idx + 2}: A coluna '{col_display_name}' não pode conter o caracter '|'.` · on exception `{file_name}: Erro ao processar a checagem de barra vertical: {e}`
- Target message key: `rule.STRUCT-009.error`
- Implemented by: `helpers/common/validation/dataframe_processing.py::DataFrameProcessing.check_dataframe_vertical_bar`, called from `SpModelABC.initialize`
- Covered by tests: `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: converts the whole frame to `str` (PERF-002); for CSV a `|` in data cannot survive parsing, so the check is effective for XLSX only; double-header row offset is still `+2` (should be `+3`).

### STRUCT-010 · A row may not have more values than named columns
- Severity: error
- NamesEnum: FS
- Protocol: not in protocol — implemented behaviour (detects data under unnamed/blank headers)
- Statement: count columns whose name (level 1 for double headers) starts with `unnamed`; any row whose number of non-null cells exceeds the number of named columns is an error.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: A linha possui {n} valores, mas a tabela possui apenas {valid_columns_count} coluna(s) válida(s).`
- Target message key: `rule.STRUCT-010.error`
- Implemented by: `dataframe_processing.py::DataFrameProcessing.check_dataframe_unnamed_columns`, called from `SpModelABC.initialize`
- Covered by tests: `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: on exception `{file_name}: Erro ao processar a checagem de colunas sem nome: {e}`.

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
- Notes / known defects: for `descricao`, `relacao`/`unidade` are injected before this check (BUG-003), so they never appear as extra.

## Gaps (protocol ↔ code)

- **G-01 UTF-8 encoding**: the protocol requires UTF-8 and the FAQ names a dedicated message; the code only reacts to `UnicodeDecodeError` (STRUCT-007). Proposal: STRUCT-013 encoding detection via `chardet` before parsing.
- **G-02 `|` in CSV**: impossible to detect after `pd.read_csv(sep="|")`; would need a pre-parse scan of raw text.
- **G-03 decimal comma**: the protocol mandates comma as decimal separator in CSV; code accepts both `,` and `.` everywhere (lenient, undocumented).
- **G-04 `.qml`**: still scanned (`Config.extensions`) though removed from the protocol in v1.11.

Last synced with code: 3dcfdb1
