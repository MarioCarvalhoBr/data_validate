# Spell-check and `dicionario`

Purpose: every textual field is spell-checked in Portuguese (or English with `--locale en_US`),
except data sources (protocol §2 p.3). `dicionario.xlsx` lists words to ignore (§2.8, p.14–15).
Skippable with `--no-spellchecker` (listed as "not executed" in the report).

## Inputs

| Sheet | Columns checked | Source in code |
|---|---|---|
| `descricao` | `nome_simples`, `nome_completo`, `desc_simples`, `desc_completa` | `validators/spell/spellchecker_validator.py::SpellCheckerValidator.model_columns_map` |
| `referencia_temporal` | `descricao` | same |
| `cenarios` (only when scenarios exist) | `nome`, `descricao` | same |
| `dicionario` | `palavra` — first column, one word per row, `#`-prefixed lines ignored | `models/sp_dictionary.py::SpDictionary.pre_processing` |

Dictionary stack (`helpers/tools/spellchecker/**`): pyenchant `Broker` with
`ENCHANT_CONFIG_DIR = data_validate/static/dictionaries` (hunspell `pt_BR`/`en_US` `.dic/.aff`),
plus `extra-words.dic` (project words such as `AdaptaBrasil`, `multiescalar/B`) and the user words
from `dicionario`, all added through `dictionary.add()` (persisted personal word list — BUG-022).
Language = `--locale` value (BUG-023).

Text sanitisation before checking (`text_processor.py::TextProcessor.sanitize_text`), in order:
cut everything from `Fontes:`/`Fonte:`; strip HTML tags; remove e-mails; remove URLs; remove
parenthesised text, punctuation and digits; collapse whitespace. Tokens that are all-uppercase with
length > 1 are treated as acronyms and skipped.

## Rules

### SPELL-001 · The language dictionary must be available
- Severity: error (intended)
- NamesEnum: SPELL (`verification_name_spelling`)
- Protocol: not in protocol — implemented behaviour
- Statement: the enchant dictionary for the locale must exist and initialise; `extra-words.dic` must be present.
- Current message (pt-BR): `Dicionário {lang} não encontrado` · `Erro ao verificar dicionário: {e}` · `Erro ao inicializar dicionário {lang}: {e}` · `Arquivo extra-words.dic não encontrado. Reporte o erro ao administrador do sistema.` · `Aviso: Não foi possível carregar palavras extras: {e}`
- Target message key: `rule.SPELL-001.error`
- Implemented by: `helpers/tools/spellchecker/dictionary_manager.py::DictionaryManager.validate_dictionary`, `initialize_dictionary`, `_load_extra_words`; collected in `SpellChecker.errors_dictionary`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py`, `test_spellchecker.py`
- Notes / known defects: **never reported** — `SpellCheckerValidator._prepare_statement` (which copies `errors_dictionary` into the report) is defined but never called from `__init__` (unlike every other validator). With a missing dictionary every `dictionary.check` raises inside SPELL-005 instead. New backlog candidate.

### SPELL-002 · Columns to check must exist
- Severity: warning
- NamesEnum: SPELL
- Protocol: —
- Statement: each configured column must exist in the sheet; missing ones are warned and the remaining ones are checked.
- Current message (pt-BR): `{filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente.`
- Target message key: `rule.SPELL-002.warning`
- Implemented by: `spellchecker_validator.py::SpellCheckerValidator.validate_spellchecker` (`_column_exists`)
- Covered by tests: none — TST-001
- Notes / known defects: `DataFrameProcessor.validate_columns` produces a second variant (`{file_name}: A verificação de ortografia foi abortada para as colunas: [..].`) that is discarded (`# warnings.extend(column_warnings)` in `spellchecker.py`).

### SPELL-003 · No two or more consecutive spaces
- Severity: warning
- NamesEnum: SPELL
- Protocol: not in protocol — implemented behaviour
- Statement: raw text (before sanitisation) must not match `[ \t\f\v]{2,}`.
- Current message (pt-BR): `{sheet_name}, linha {row_index + 2}: Há dois ou mais espaços seguidos na coluna {column}.`
- Target message key: `rule.SPELL-003.warning`
- Implemented by: `helpers/tools/spellchecker/spellchecker_controller.py::SpellCheckerController.check_text_quality` → `TextProcessor.has_multiple_spaces`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_spellchecker_controller.py`, `test_text_processor.py`
- Notes / known defects: overlaps DESC-004's `(EXTRA_SPACE)` report for name columns.

### SPELL-004 · Words must be in the dictionary
- Severity: warning
- NamesEnum: SPELL
- Protocol: §2 p.3 ("Todas as informações textuais entregues serão objeto de verificação ortográfica em português")
- Statement: after sanitisation, every token (except acronyms) must pass `dictionary.check`; unknown words are listed per cell. Results are sorted per sheet.
- Current message (pt-BR): `{sheet_name}, linha {row_index + 2}: Palavras com possíveis erros ortográficos na coluna {column}: ['w1', 'w2'].`
- Target message key: `rule.SPELL-004.warning`
- Implemented by: `spellchecker_controller.py::SpellCheckerController.find_spelling_errors`, driven by `dataframe_processor.py::DataFrameProcessor.process_dataframe`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/*.py` (with mocked enchant)
- Notes / known defects: per-cell enchant calls without cache (PERF-006); the `#palavra#` escape from protocol v1.7 is not honoured (gap G-25); `fontes` is correctly excluded, but `unidade`, `meta`, `referencia_temporal.nome`, `legenda.label` are not checked although the protocol says "todas as informações textuais" (gap G-26).

### SPELL-005 · Processing failures are reported, not raised
- Severity: error
- NamesEnum: SPELL
- Protocol: —
- Statement: any exception while checking a sheet is caught and reported as one error for the file.
- Current message (pt-BR): `Erro ao processar o arquivo {file_name}: {e}`
- Target message key: `rule.SPELL-005.error`
- Implemented by: `helpers/tools/spellchecker/spellchecker.py::SpellChecker.check_spelling_text`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_spellchecker.py`
- Notes / known defects: broad `except` (SEC-004); this is how a missing dictionary surfaces today.

## Gaps (protocol ↔ code)

- **G-25 `#…#` ignore delimiter** (v1.7): not implemented; `#` is stripped as punctuation so the word is still checked.
- **G-26 coverage of textual columns**: only 7 columns across 3 sheets are checked.
- **G-27 case-sensitive dictionary words**: protocol says dictionary words match exactly, case-sensitively; enchant's `add()` behaviour for capitalised forms is not verified by tests.
- SPELL-001 errors are silently dropped (see rule notes).

Last synced with code: 3dcfdb1
