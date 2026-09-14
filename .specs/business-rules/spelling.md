# Spell-check and `dicionario`

Purpose: every textual field is spell-checked in Portuguese (or English with `--locale en_US`),
except data sources (protocol §2 p.3). `dicionario.xlsx` lists words to ignore (§2.8, p.14–15).
Skippable with `--no-spellchecker` (listed as "not executed" in the report).

**ARC-017 Phase 3 Port 8 (the migration's last validator port):** `validators/spell/
spellchecker_validator.py::SpellCheckerValidator` is deleted; `data_validate/validators/` no
longer exists as a package (ARC-008). Every rule below is now `data_validate/rules/spell.py`'s
`SPELL_REGISTRY` (`SPELL-001`…`SPELL-005`), run by `SpreadsheetProcessor._run_rule_registries(
[SPELL_REGISTRY], ctx)`. Design notes specific to this port:

- One `RuleSpec` per checked model (`check_dictionary_backend` for the backend/dictionary,
  `check_spelling_description`/`_temporal_reference`/`_scenario` for the three checked sheets),
  not one per behaviour — each model's own sheet gates its own `requires`, matching the legacy
  per-model `if self._dataframe.empty: return` guard. Every model-`RuleSpec` can still tag an
  `Issue` with *any* of `SPELL-002`/`003`/`004`/`005` (whichever behaviour actually fired), never
  only the id the `RuleSpec` itself is registered under — the same "one method, several
  `Issue`-level ids" shape `rules/proportionality.py`'s `PROP-007` already established.
- `check_dictionary_backend` (`SPELL-001`) is never gated on `--no-spellchecker`; the other three
  rules skip everything (including the missing-column check) when `--no-spellchecker` is set —
  reproducing exactly which parts of the legacy `SpellCheckerValidator.__init__`/`run()` ran
  unconditionally vs. conditionally (BUG-027).
- The legacy `errors.extend(sorted(errors_spellchecker))`/`warnings.extend(sorted(
  warnings_spellchecker))` step (sorting already-rendered Portuguese strings, which reorders
  same-day multi-digit line numbers lexicographically) is reproduced by `_sort_by_rendered_text`:
  it calls `ctx.translate(issue.message_key, **issue.params)` purely to derive a sort key (never
  to build displayed text), then returns the original `Issue`s in that order — a stable sort, so
  ties keep their row/signal order.
- The backend (`helpers/tools/spellchecker/**`) exposes the structured surface the rule actually
  calls: `SpellChecker.check_spelling_text_structured` (returns `tuple[SpellingFinding, ...]` + an
  optional error string, never a pre-formatted sentence), `SpellCheckerController.
  build_quality_findings`, `DataFrameProcessor.find_quality_findings`. The original,
  string-returning compatibility wrappers this structured surface was layered alongside
  (`SpellCheckerController.format_quality_warnings`/`check_text_quality`, `DataFrameProcessor.
  process_dataframe`/`validate_columns`) had zero production callers once every SPELL rule moved
  onto the structured path, and were removed as dead code. `SpellChecker.
  check_spelling_text_structured`'s `except Exception` is a
  **deliberate**, documented broad catch (SPELL-005's own business rule — "any exception … is
  caught and reported as one error", the same justified shape as `rules/engine.py::
  Engine._run_one`'s crash isolation), not an unreviewed bare except (`.claude/rules/security.md`).

## Inputs

| Sheet | Columns checked | Source in code |
|---|---|---|
| `descricao` | `nome_simples`, `nome_completo`, `desc_simples`, `desc_completa` | `validators/spell/spellchecker_validator.py::SpellCheckerValidator.model_columns_map` |
| `referencia_temporal` | `descricao` | same |
| `cenarios` (only when scenarios exist) | `nome`, `descricao` | same |
| `dicionario` | `palavra` — first column, one word per row, `#`-prefixed lines ignored | `models/sp_dictionary.py::SpDictionary.pre_processing` |

Dictionary stack (`helpers/tools/spellchecker/**`): pyenchant `Broker` reading the bundled hunspell
`pt_BR`/`en_US` `.dic/.aff` files (`static/dictionaries/hunspell`), plus `extra-words.dic` (project
words such as `AdaptaBrasil`, `multiescalar/B`) and the user words from `dicionario`. Since
`Broker.set_param` is a no-op with Enchant C library >= 2.0 (fixed SEC-007/BUG-022,
`dictionary_manager.py::DictionaryManager`), `ENCHANT_CONFIG_DIR` is the only way to point Enchant
at the bundled dictionaries; it is scoped to a per-manager `tempfile.TemporaryDirectory()`
(symlinking the real `hunspell/` folder into it) via `DictionaryManager._enchant_config_dir_scope()`,
which restores the previous env value (or its absence) in a `finally` block after each
`validate_dictionary`/`initialize_dictionary` call — the variable is never left mutated for the rest
of the process. Extra/user words are added with `dictionary.add_to_session()`, not `dictionary.add()`,
so nothing is ever persisted to a `.dic`/`.exc` personal-word-list file — not under the package
directory, not even under the ephemeral temp directory once `clean_temporary_files()` discards it.
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
- Target message key: `rule.SPELL-001.backend_error` — a documented, intentional passthrough
  (`{message}`-only template, identical in both locales): `DictionaryManager`/`SpellChecker`
  errors arrive pre-formed, hardcoded-Portuguese strings regardless of `--locale` (a pre-existing
  gap, not fixed by this port, see Gaps below); this key renders exactly that string rather than
  inventing a "translation" of text this port has no authority to retranslate.
- Implemented by: `helpers/tools/spellchecker/dictionary_manager.py::DictionaryManager.validate_dictionary`, `initialize_dictionary`, `_load_extra_words`; collected in `SpellChecker.errors_dictionary`; surfaced as an `Issue` by `rules/spell.py::check_dictionary_backend` (`SPELL-001`), which reads `ctx.options["spell_backend"].errors_dictionary`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py`, `test_spellchecker.py`, `tests/unit/rules/test_spell.py::TestCheckDictionaryBackend`
- Notes / known defects: fixed (BUG-027, done) — `rules/spell.py::check_dictionary_backend` is never gated on `--no-spellchecker`, exactly like `SpellCheckerValidator.__init__`'s own unconditional `_prepare_statement()` call before `run()` used to be; a missing dictionary or `extra-words.dic` failure is visible under the SPELL/Ortografia title regardless of the flag.

### SPELL-002 · Columns to check must exist
- Severity: warning
- NamesEnum: SPELL
- Protocol: —
- Statement: each configured column must exist in the sheet; missing ones are warned and the remaining ones are checked.
- Current message (pt-BR): `{filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente.`
- Target message key: `rule.spelling.missing_required_column`
- Implemented by: `rules/spell.py::_spelling_issues_for_model` (shared by `check_spelling_description`/`_temporal_reference`/`_scenario`), `_missing_column_issue`
- Covered by tests: `tests/unit/rules/test_spell.py::TestCheckSpellingDescription`/`TestCheckSpellingTemporalReference`/`TestCheckSpellingScenario`
- Notes / known defects: `rules/spell.py` checks column presence directly against `ctx.sheet(...)`, matching every other port's precedent. `DataFrameProcessor.validate_columns` (the legacy method that used to produce a second, discarded message variant here) had zero production callers and was removed as dead code.

### SPELL-003 · No two or more consecutive spaces
- Severity: warning
- NamesEnum: SPELL
- Protocol: not in protocol — implemented behaviour
- Statement: raw text (before sanitisation) must not match `[ \t\f\v]{2,}`.
- Current message (pt-BR): `{sheet_name}, linha {row_index + 2}: Há dois ou mais espaços seguidos na coluna {column}.`
- Target message key: `rule.SPELL-003.warning`
- Implemented by: `helpers/tools/spellchecker/spellchecker_controller.py::SpellCheckerController.build_quality_findings` → `TextProcessor.has_multiple_spaces`; rendered as an `Issue` by `rules/spell.py::_finding_to_issue`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_spellchecker_controller.py`, `test_text_processor.py`, `tests/unit/rules/test_spell.py`
- Notes / known defects: overlaps DESC-004's `(EXTRA_SPACE)` report for name columns.

### SPELL-004 · Words must be in the dictionary
- Severity: warning
- NamesEnum: SPELL
- Protocol: §2 p.3 ("Todas as informações textuais entregues serão objeto de verificação ortográfica em português")
- Statement: after sanitisation, every token (except acronyms) must pass `dictionary.check`; unknown words are listed per cell. Results are sorted per sheet.
- Current message (pt-BR): `{sheet_name}, linha {row_index + 2}: Palavras com possíveis erros ortográficos na coluna {column}: ['w1', 'w2'].`
- Target message key: `rule.SPELL-004.warning`
- Implemented by: `spellchecker_controller.py::SpellCheckerController.find_spelling_errors`, driven by `dataframe_processor.py::DataFrameProcessor.find_quality_findings`; `SpellChecker.check_spelling_text_structured` wraps the result as `SpellingFinding`s for `rules/spell.py::_finding_to_issue`
- Covered by tests: `tests/unit/helpers/tools/spellchecker/*.py` (with mocked enchant), `tests/unit/rules/test_spell.py` (with a `FakeSpellBackend` test double, no `enchant` dependency)
- Notes / known defects: per-cell enchant calls without cache (PERF-006); the `#palavra#` escape from protocol v1.7 is not honoured (gap G-25); `fontes` is correctly excluded, but `unidade`, `meta`, `referencia_temporal.nome`, `legenda.label` are not checked although the protocol says "todas as informações textuais" (gap G-26). The legacy `sorted(warnings_spellchecker)` step (over already-rendered text) is reproduced by `rules/spell.py::_sort_by_rendered_text`, sorting `Issue`s by their own rendered text rather than building text in rule code.

### SPELL-005 · Processing failures are reported, not raised
- Severity: error
- NamesEnum: SPELL
- Protocol: —
- Statement: any exception while checking a sheet is caught and reported as one error for the file.
- Current message (pt-BR): `Erro ao processar o arquivo {file_name}: {e}`
- Target message key: `rule.SPELL-005.error`
- Implemented by: `helpers/tools/spellchecker/spellchecker.py::SpellChecker.check_spelling_text_structured` (the structured counterpart `rules/spell.py` calls; the original `check_spelling_text` is kept unchanged for backward compatibility)
- Covered by tests: `tests/unit/helpers/tools/spellchecker/test_spellchecker.py`, `tests/unit/rules/test_spell.py::test_a_processing_failure_is_reported_as_spell_005_with_no_other_issues`
- Notes / known defects: broad `except` (SEC-004) — **kept, deliberately**, not narrowed to a specific exception list: this rule's whole point is "any exception … is caught", the same justified shape as `rules/engine.py::Engine._run_one`'s crash isolation; the broad catch is now explicitly documented in `check_spelling_text_structured`'s docstring instead of being an unreviewed bare except. This is how a missing dictionary surfaces today.

## Gaps (protocol ↔ code)

- **G-25 `#…#` ignore delimiter** (v1.7): not implemented; `#` is stripped as punctuation so the word is still checked.
- **G-26 coverage of textual columns**: only 7 columns across 3 sheets are checked.
- **G-27 case-sensitive dictionary words**: protocol says dictionary words match exactly, case-sensitively; enchant's `add()` behaviour for capitalised forms is not verified by tests.

Last synced with code: ARC-017 Phase 3 Port 8 (SPELL-001…005 ported to `rules/spell.py`; legacy
`SpellCheckerValidator` deleted; `data_validate/validators/` deleted entirely)
