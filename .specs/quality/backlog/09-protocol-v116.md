# 09 · Protocol v1.16 alignment

> **Scheduling (user instruction 2026-09-12):** every item in this file runs **after** the
> pre-existing backlog (files 01–07) is cleared. Priorities below rank importance *within* this
> file — the TERR/registry items (PROTO-013) stay **P1 in importance but are sequenced last**,
> behind everything in 01–07. `/backlog next` must not select PROTO-* while any 01–07 item is
> still open or in-progress.

The user announced on 2026-09-12 that Protocol **v1.16 (2026-08-21)** is the authoritative
specification (`assets/protocolo-v-1.16.pdf`), superseding v1.13. The full extraction lives in
`.specs/_drafts/protocol-rules-v116.md`; the normative delta is in
`.specs/business-rules/protocol-changelog.md`. Items below are the code changes v1.16 requires,
plus v1.13-era gaps the new version confirms. Every item that changes a rendered message ends with
a **reviewed** golden re-baseline (`make harness-update` + entry in
`tests/e2e/golden/CHANGELOG.md`) — never silent.

### PROTO-001 · Stop requiring the removed `fontes` column in `descricao`
- Priority: P1 · Effort: S · Status: done
- Protocol: v1.16 history ("Removendo fonte da descricao dos indicadores, pois não é usada"); §2.3
  no longer lists `fontes`.
- Where: `models/sp_description.py::RequiredColumn` (COLUMN_SOURCES), `specs/sheet_specs.py`
  (descricao ColumnSpec), `.specs/business-rules/description.md` DESC-011.
- Problem: `fontes` is a **required** column today; a v1.16-compliant bundle fails with
  "Coluna 'fontes' esperada mas não foi encontrada" — breaking for new sectors.
- Proposed fix: move `fontes` out of the required set; accept it silently when present (deprecated
  known column — no extra-column warning, documented) so current fixtures keep byte-identical
  goldens; drop it from any spell-check exception notes.
- Tests: unit (bundle without `fontes` → no missing-column error; with `fontes` → no warning);
  goldens unchanged.
- Related: PROTO-002, BUG-003
- Done: `fontes` is `ColumnKind.DEPRECATED` in `specs/sheet_specs.py` and
  `SpDescription.DeprecatedColumn` (`models/sp_description.py`); `pre_processing` only adds it to
  `EXPECTED_COLUMNS` when present, no default injection. Tests:
  `tests/unit/models/test_sp_description.py`, `tests/unit/specs/test_sheet_specs.py`. Goldens
  byte-identical (`make test-e2e` green). Spec: `.specs/business-rules/description.md`,
  `.specs/business-rules/protocol-changelog.md`.

### PROTO-002 · Stop injecting/expecting the removed `relacao` column
- Priority: P1 · Effort: S · Status: done
- Protocol: v1.15 history ("relacao em descrição é um parâmetro desnecessário…").
- Where: `models/sp_description.py::pre_processing` (injects `relacao=1` into raw_data — also
  BUG-003), `OptionalColumn.COLUMN_RELATION`, `validators/spreadsheets/composition/
  composition_tree_validator.py::_prepare_statement` (lists `relacao` among required description
  columns), `specs/sheet_specs.py`.
- Proposed fix: remove the injection and the requirement; accept `relacao` silently when present
  (deprecated known column); composition tree no longer lists it.
- Tests: unit (bundle without `relacao` passes the tree validator's column check); goldens
  unchanged (fixtures may still carry the column — silently accepted).
- Related: G-10 (the `relacao ∈ {1,−1}` sub-gap dies with the column), G-28
- Done: `relacao` is `ColumnKind.DEPRECATED`; the `relacao=1` injection is deleted from
  `SpDescription.pre_processing`; `rules/composition.py::_tree_required_column_issues`
  (COMP-007/008/009) no longer requires it. Tests: `tests/unit/models/test_sp_description.py`,
  `tests/unit/models/test_model_isolation.py`, `tests/unit/rules/test_composition.py`. Goldens
  byte-identical (`make test-e2e` green). Spec: `.specs/business-rules/description.md`,
  `.specs/business-rules/composition.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-003 · STRUCT-014: each `.xlsx` must contain exactly one worksheet
- Priority: P1 · Effort: M · Status: done
- Protocol: §2 p.3 (since v1.14).
- Where: `helpers/tools/data_loader/readers/excel_reader.py` (calamine reads the first sheet
  silently), new rule STRUCT-014, message keys in both catalogs.
- Proposed fix: list worksheets via `python_calamine.CalamineWorkbook.sheet_names`; >1 sheet →
  error naming the file and the extra sheets; register STRUCT-014 under `FS`.
- Tests: unit with a 2-sheet xlsx fixture built via openpyxl in tmp_path; golden case in a
  data_errors fixture (new fixture folder or extend an existing one — reviewed re-baseline).
- Done: implemented in `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()`
  (module-level `_worksheet_names`, using `python_calamine.CalamineWorkbook.from_path(...)`
  directly — not `excel_reader.py`, which stays a thin pandas wrapper); a loader-level error
  (like STRUCT-015's size-limit checks), not a `RuleSpec`. No `.xlsx`-writing library is
  available in this project (`openpyxl`/`xlsxwriter` are not dependencies), so the unit test
  hand-builds a minimal OOXML zip via the stdlib `zipfile` instead. Tests:
  `tests/unit/helpers/tools/data_loader/api/test_facade.py::TestDataLoaderFacadeStructuralChecks`.
  No fixture under `data/input/` has more than one worksheet (verified), so no fixture's golden
  changes for this item beyond the two new always-empty report sections shared with PROTO-006/
  PROTO-017 (see the golden CHANGELOG). Spec: `.specs/business-rules/file-structure.md`,
  `.specs/business-rules/protocol-changelog.md`.

### PROTO-004 · DESC-013: require `categoria` and validate its domain
- Priority: P1 · Effort: M · Status: done (step 1 — see Done note; step 2, absence → error, stays open for a future re-baseline)
- Protocol: §2.3 p.8 (since v1.13): one of `social`, `economico`, `ambiental`, `climatico`.
- Where: `models/sp_description.py` (unknown column today → unexpected-column warning),
  `specs/sheet_specs.py`, new rule DESC-013.
- Proposed fix (staged to protect current sectors): step 1 — accept the column, validate the
  domain when present (errors on invalid values), emit a **warning** when the column is absent;
  step 2 (Phase 4 re-baseline) — absence becomes an error. Record the staging in
  `description.md`.
- Tests: table-driven domain cases incl. accented variants rejected; goldens: current fixtures
  lack `categoria` → the new absence-warning changes goldens — reviewed re-baseline required.
- Done: `specs/sheet_specs.py` gains `categoria` as `ColumnKind.OPTIONAL`;
  `SpDescription.OptionalColumn.COLUMN_CATEGORY`; new rule `rules/description.py::
  check_category_domain` (DESC-013), new category `NamesEnum.CATEG_DESC`
  (`verification_name_indicator_category`, both locales). Tests:
  `tests/unit/rules/test_description.py::TestCheckCategoryDomain`,
  `tests/unit/specs/test_sheet_specs.py`. Goldens re-baselined (all 8 fixtures gain the
  "Categoria do indicador" section with one absence warning each; `tests` 34→35) — reviewed
  diff and quote in `tests/e2e/golden/CHANGELOG.md`'s "PROTO-004" entry. Spec:
  `.specs/business-rules/description.md`, `.specs/business-rules/README.md`,
  `.specs/business-rules/protocol-changelog.md`, `.specs/00-overview.md`.

### PROTO-005 · Flip DESC-006 for `desc_simples`: forbid the trailing period (G-07)
- Priority: P2 · Effort: S · Status: done
- Protocol: §2.3 p.7 (v1.13 and v1.16 agree): "Toda descrição simples não pode terminar com um
  caractere especial como o ponto." The code requires the period.
- Proposed fix: `desc_simples` moves from `columns_must_end_with_dot` to
  `columns_dont_punctuation` in `SpDescriptionValidator.validate_punctuation`; message text stays
  the catalog-consistent "não deve terminar com pontuação".
- Tests: unit; goldens change wherever fixtures end `desc_simples` with "." — reviewed
  re-baseline with the protocol quote in the golden CHANGELOG.
- Done: `rules/description.py` moves `desc_simples` from `_MUST_END_WITH_DOT_COLUMNS` to
  `_NO_PUNCTUATION_COLUMNS` (message key unchanged: `rule.DESC-006.no_punctuation`); factory
  default (`tests/factories.py::make_description_frame`) no longer ends `desc_simples` with a
  period. Tests: `tests/unit/rules/test_description.py::TestCheckPunctuation`,
  `tests/unit/test_factories.py`. Goldens re-baselined (all 8 fixtures — every fixture's
  `descricao.desc_simples` cells ended with `.` under the old rule); reviewed diff and quote in
  `tests/e2e/golden/CHANGELOG.md`'s "PROTO-005" entry. Spec:
  `.specs/business-rules/description.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-006 · SCEN-005: scenario symbol is one character, letters/digits only (G-17)
- Priority: P2 · Effort: S · Status: done
- Protocol: §2.1 p.4: "Um único caractere … apenas letras e números".
- Proposed fix: new rule in the scenario validator (`len == 1` and `isalnum()`); register under
  `MAND_PUNC_SCEN` or a new title (decide with the rule-authoring skill).
- Tests: unit table (multi-char, space, punctuation, accents); golden case.
- Done: `rules/scenario.py::check_symbol_charset` (new category `NamesEnum.SYMB_SCEN`,
  `verification_name_scenario_symbol_charset`, both locales) — reusing `MAND_PUNC_SCEN`/
  `UVR_SCEN` was rejected (symbols are neither punctuation nor a uniqueness check; a dedicated
  title keeps each category's meaning unambiguous, matching the PROTO-004/`CATEG_DESC`
  precedent). Pattern `^[A-Za-z0-9]$` (ASCII only — an accented letter is not "letras" in the
  protocol's own unaccented-alphabet sense). Tests:
  `tests/unit/rules/test_scenario.py::TestCheckSymbolCharset` (table-driven: two chars, trailing
  space, punctuation, accented, empty, blank). Every fixture's `cenarios.simbolo` is already a
  single ASCII letter, so no fixture's error/warning content changes; goldens gain only the new,
  always-empty section (see the golden CHANGELOG). Spec: `.specs/business-rules/scenarios.md`,
  `.specs/business-rules/README.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-007 · STRUCT-013: proactive UTF-8 check with the FAQ message (G-01)
- Priority: P2 · Effort: M · Status: done
- Protocol: §2 p.3 + FAQ "O arquivo XXX está no formato YYY, deveria ser UTF-8."
- Proposed fix: on CSV load, detect encoding (`FileSystemUtils.detect_encoding`, currently unused)
  and emit exactly the FAQ message shape as an error; xlsx exempt (zip container).
- Tests: latin-1 fixture file; golden case.
- Done: implemented in `helpers/tools/data_loader/api/facade.py::DataLoaderFacade.load()`
  (module-level `_detect_non_utf8_encoding`), calling `chardet` directly rather than reusing
  `FileSystemUtils.detect_encoding` — that class depends on `LanguageManager`, which the loading
  layer must not pull in (`.claude/rules/architecture-boundaries.md`: loading depends only on
  `specs`/`util`). A sample that round-trips through `bytes.decode("utf-8")` is trusted as UTF-8
  outright, before `chardet` ever runs — `chardet` alone mis-detects short accented-character
  samples as `ISO-8859-1` with confidence above the 0.7 threshold, a real false-positive this
  project must not surface. Does not block the subsequent read attempt (informational, additive
  to STRUCT-007's own reactive error). Tests:
  `tests/unit/helpers/tools/data_loader/api/test_facade.py::TestDataLoaderFacadeStructuralChecks`
  (a real latin-1 file and a real UTF-8-with-accents file in `tmp_path`, no mocked reader). The
  bundle's one `.csv` fixture (`data_errors_xss/descricao.csv`) is genuinely UTF-8 with high
  `chardet` confidence, so no fixture's error/warning content changes. Spec:
  `.specs/business-rules/file-structure.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-008 · DESC-014: codes ordered by hierarchy level (G-06)
- Priority: P2 · Effort: M · Status: done
- Protocol: §2.3 p.6: codes sequential AND grouped from level 1 downwards; "Não inserir um codigo
  de menor nível entre codigos de níveis superiores."
- Proposed fix: after cleaning, assert `nivel` is non-decreasing along ascending `codigo`.
- Tests: unit; golden case.
- Done: `rules/description.py::check_codes_ordered_by_level` (category `IL`), vectorised
  `.sort_values()` + `.shift()`. Tests:
  `tests/unit/rules/test_description.py::TestCheckCodesOrderedByLevel`. Goldens re-baselined:
  `data_errors_09`/`data_errors_11` each gain one new error (pre-existing level-ordering
  defects); no other fixture affected — reviewed diff in `tests/e2e/golden/CHANGELOG.md`'s
  PROTO-008/009/010 entry. Spec: `.specs/business-rules/description.md`,
  `.specs/business-rules/protocol-changelog.md`.

### PROTO-009 · DESC-015: `cenario` ∈ {0,1} plus hierarchy propagation (G-09)
- Priority: P2 · Effort: M · Status: done
- Protocol: §2.3 p.8: values 0/1; scenario membership propagates up and down the composition.
- Where: `models/sp_description.py::data_cleaning` currently cleans `cenario` with
  `min_value=-1` (accepts −1).
- Proposed fix: domain {0,1}; propagation check joins description with the composition tree.
- Tests: unit (−1 rejected; parent with scenario whose child lacks it → error); golden case.
- Done: `rules/description.py::check_scenario_domain_and_propagation` (category `TH`); domain
  check flags cleaned `cenario` values outside {0,1} as an **error** (`CLEAN-002` itself stays
  permissive at ≥ −1); propagation check is directional, scoped to direct `composicao` edges
  (parent `cenario=1` requires child `=1`; the reverse is not flagged) — matches this item's own
  worked example exactly, not a full transitive ancestor/descendant closure. Tests:
  `tests/unit/rules/test_description.py::TestCheckScenarioDomainAndPropagation`. Goldens
  re-baselined: **every** fixture gains two new **warnings** (a level-2 indicator with
  `cenario=1` whose two direct children lack it). **Staged same day (orchestrator decision)**:
  the propagation half first shipped as an error, which flipped `data_ground_truth_01`'s
  `exit_code` from `0` → `1` for the first time — an unacceptable regression risk for
  production bundles; before that reached a commit, it was staged down to `Severity.WARNING`
  (message text unchanged, `rule.DESC-015.propagation_error` → `rule.DESC-015.propagation_warning`),
  matching the PROTO-004 staging precedent, so `data_ground_truth_01`'s `exit_code` stays `0`;
  the domain half is unaffected and stays an error; promoting the propagation half back to an
  error is a future owner decision. See `tests/e2e/golden/CHANGELOG.md`'s PROTO-008/009/010
  entry (and its same-day amendment) and `.specs/business-rules/protocol-changelog.md`'s
  "PROTO-009/DESC-015 maintainer note". Spec: `.specs/business-rules/description.md`.

### PROTO-010 · DESC-017/DESC-019: `ordem` sibling sequence and `nome_completo` length (G-10)
- Priority: P2 · Effort: M · Status: done
- Protocol: §2.3 pp.7–8: `ordem` integers 1..n per parent (`#202`); `nome_completo` at least as
  long as `nome_simples`. (`DESC-016` for `relacao` is retired unimplemented — column removed;
  `DESC-018` `meta` format stays parked until owners specify it formally.)
- Tests: unit per rule; golden cases.
- Done: `rules/description.py::check_order_sibling_sequence` (DESC-017, category `CHILD_LVL`) and
  `::check_complete_name_length` (DESC-019, category `INP`). Tests:
  `tests/unit/rules/test_description.py::TestCheckOrderSiblingSequence`/
  `TestCheckCompleteNameLength`. Goldens: DESC-017 fires in none of the eight fixtures (every
  `ordem` sequence is already valid); DESC-019 adds one new warning to `data_errors_xss` only
  (its known `<Script>` payload lengthens `nome_simples` past `nome_completo`) — reviewed diff in
  `tests/e2e/golden/CHANGELOG.md`'s PROTO-008/009/010 entry. Spec:
  `.specs/business-rules/description.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-011 · Legend tightening: six-hex colours, ≤ 11 slices (G-19, G-21 → LEG-016)
- Priority: P2 · Effort: S · Status: done
- Protocol: §2.5 pp.10–11: `cor` = "#" + six hex digits; up to 11 intervals (5–7 advised); grey
  reserved for "Dado indisponível".
- Proposed fix: tighten LEG-008's regex to 6-hex only; new LEG-016 warning for >11 slices; grey
  advisory left as documentation.
- Tests: unit (`#abc` now invalid); goldens: check fixtures for 3-hex colours before deciding on
  re-baseline.
- Done: `helpers/common/validation/legend_processing.py::LegendProcessing.validate_color_format`'s
  regex tightened to `^#[A-Fa-f0-9]{6}$`; new `::validate_legend_slice_count` (LEG-016), called
  from `models/sp_legend.py::SpLegend.data_cleaning` in the same "LEG-002…006 passed cleanly"
  block as LEG-007…011, appending to `data_cleaning_warnings` — category stays `FC`
  (`verification_name_file_cleaning`), matching every other LEG-001…011 model-level check's
  bucket (`SpreadsheetProcessor` reports every model's `data_cleaning_warnings` under `FC`
  regardless of which check populated it), not a new dedicated category. Grey-for-DI stays
  documentation only (not validated). Tests:
  `tests/unit/helpers/common/validation/test_legend_processing.py::TestValidateColorFormat`
  (3-digit cases flipped to invalid) and `::TestValidateLegendSliceCount`. Both fixtures with a
  `legenda` file use six-hex colours and 5 non-DI slices per code (checked before implementing),
  so no fixture's content changes for this item. Spec: `.specs/business-rules/legend.md`,
  `.specs/business-rules/README.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-012 · Empty `legenda` cell means default legend, not an error (G-20)
- Priority: P2 · Effort: M · Status: done
- Protocol: §2.3 p.8: "Quando esta coluna for usada, todos os valores vazios serão associados à
  legenda default."
- Where: `validators/spreadsheets/legend/legend_validator.py` LEG-014 errors for levels ≥3 without
  a legend reference.
- Proposed fix: empty cell → default legend [0,1]; LEG-014's error narrows to dangling references
  (non-empty values that match no legend code).
- Tests: unit; goldens change for fixtures that trigger today's LEG-014 — reviewed re-baseline.
- Done: `rules/legend.py::check_other_levels_must_reference_legend` (LEG-014) is retired to a
  permanent `return []` — the underlying `_analyze_relation_indicators` no longer computes the
  "other levels missing legend" finding at all (dead code removed, not merely unreached). The
  rule ID stays registered (traceability) rather than being deleted from the registry, so a
  future report/spec never has to explain a vanished ID. Dangling non-empty references are
  unaffected — that was always `LEG-012`'s "missing codes" finding. Tests:
  `tests/unit/rules/test_legend.py::TestCheckOtherLevelsMustReferenceLegend` (every case,
  including a level-3 row with an empty `legenda` cell, now asserts `== []`). `rule.LEG-014.error`
  never appeared in any golden before this change (grep-verified across all eight fixtures), so
  the retirement has **no observable fixture impact**. Spec:
  `.specs/business-rules/legend.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-013 · Territory registry `spd_data.json`: loader + TERR-001/TERR-002 + whitelist
- Priority: P1 (importance) · **Sequenced last — after all 01–07 items, per the scheduling note
  above** · Effort: L · Status: open
- Source: **maintainer decisions 2026-09-12** (authoritative): `spd_data.json` is an OPTIONAL
  input generated by the Canoa server and passed alongside the bundle. Semantics: (1) the check is
  a **verification of its own** — new dedicated report category (`TERR` /
  `verification_name_territory_registry`) with title and message keys in BOTH locales, never
  folded into an existing category; (2) it triggers **only when the file is present** — absent →
  the category is reported as skipped/not executed, never an error; (3) findings are **always
  errors** (`Severity.ERROR`), never warnings: every `id` in `valores` (TERR-001) and in
  `proporcionalidades` (TERR-002) must exist among the registry ids
  (`{"values": [{"id": int, "name": str, "region": str}, …]}` — example at
  `local_data/ULTIMA_IMPLEMENTACAO/spd_data.json`).
  Protocol basis: v1.16 §2.6 p.11 (spatial relationship); the artefact itself is not in the PDF.
  Full spec: `.specs/business-rules/territories.md`.
- Proposed fix (one slice, in order):
  1. Loading layer support: optional `spd_data.json` read through the loader (stdlib `json`,
     size-limited, specific exceptions — untrusted input per `.claude/rules/security.md`);
     malformed registry → loading error, TERR rules skipped, never a crash.
  2. File-structure whitelist: STRUCT-004 must accept `spd_data.json` instead of flagging
     "arquivo não esperado" (code change in `FileStructureValidator` +
     `specs/sheet_specs.py`/`SpreadsheetInfo`).
  3. Rules TERR-001 (valores ids ⊆ registry) and TERR-002 (proporcionalidades ids ⊆ registry),
     severity error, per-id messages with row numbers; new verification title + message keys in
     BOTH catalogs (`rule.TERR-001.error`, `rule.TERR-002.error` and the title key).
  4. Tests: unit (present-and-valid, present-with-unknown-ids, absent → skipped, malformed →
     loading error) using `tests/factories.py`; golden fixtures BOTH ways — copy
     `data_ground_truth_01` + a registry covering its ids (green) and a variant with unknown ids
     (errors); reviewed re-baseline entries in `tests/e2e/golden/CHANGELOG.md`.
- Related: G-13 (full completeness — every registry id present in `valores` — remains an open
  owner decision, NOT part of this item), territories.md

### PROTO-017 · VAL-006: duplicate `id` rows in `valores`
- Priority: P2 · Effort: S · Status: done
- Protocol: §2.6 p.11 ("identificador único"); gap G-13 (uniqueness half).
- Proposed fix: duplicate values in `valores.id` → error listing the duplicated ids; no registry
  needed. Register VAL-006 under `FS` or `UNAV_INV` (decide via the rule-authoring skill).
- Tests: unit + golden case.
- Done: `rules/value.py::check_id_uniqueness`, new category `NamesEnum.UNIQ_VAL`
  (`verification_name_value_id_uniqueness`, both locales) — neither `FS` (structural, not this
  rule's concern) nor `UNAV_INV` (value-content validity, a different property than identifier
  uniqueness) fit; a dedicated title keeps this finding unambiguous in the report, matching the
  PROTO-006/`SYMB_SCEN` precedent. Tests: `tests/unit/rules/test_value.py::
  TestCheckIdUniqueness`. No fixture's `valores.id` has a duplicate, so no fixture's error/warning
  content changes; goldens gain only the new, always-empty section (see the golden CHANGELOG).
  Spec: `.specs/business-rules/values.md`, `.specs/business-rules/README.md`,
  `.specs/business-rules/protocol-changelog.md`.

### PROTO-014 · TEMP-004/TEMP-005: four-digit symbols and single observed time (G-15, G-16)
- Priority: P3 · Effort: S · Status: done
- Protocol: §2.2 p.5: `simbolo` four numeric characters; only one observed (non-future) reference
  supported by the platform (footnote).
- Tests: unit; golden case.
- Done: `rules/temporal_reference.py::check_symbol_is_four_digits` (TEMP-004, error, raw
  `^\d{4}$` format check, independent of `CLEAN-005`'s looser "parses as an integer ≥ 0"
  cleaning) and `::check_single_observed_reference` (TEMP-005, **warning**, conservative
  severity — the footnote states a platform limitation, not a hard protocol rule, matching the
  PROTO-004/PROTO-009 staging precedent for a footnote-based/platform-limitation finding).
  TEMP-005 counts every `simbolo` `<= ctx.clock().year` including the present-time row (unlike
  `TEMP-002`, which excludes it) and fires only when more than one such value exists. Both
  registered under the existing `YEARS_TEMP` category (no new title — both are still about years
  in `referencia_temporal`). Tests: `tests/unit/rules/test_temporal_reference.py::
  TestCheckSymbolIsFourDigits`/`TestCheckSingleObservedReference`. Goldens: `data_errors_01`
  gains one new TEMP-004 error (`simbolo="2050B"`, a known pre-existing defect, previously
  undetected); no other fixture's `simbolo` values fail either check — reviewed re-baseline, see
  `tests/e2e/golden/CHANGELOG.md`'s "Phase 6 round N2" entry. Spec:
  `.specs/business-rules/temporal-reference.md`, `.specs/business-rules/protocol-changelog.md`.

### PROTO-015 · Proportionality sum ≠ 1 severity when data is not normalised
- Priority: P3 · Effort: S · Status: open
- Protocol: §2.7 p.13: "Em geral … a soma … deve ser um, **mas podem existir exceções quando os
  dados não estão normalizados**."
- Where: `PROP-010` treats sums outside [0.99, 1.01] as errors unconditionally.
- Proposed fix: owner decision — either keep as error (Canoa stricter than protocol, documented)
  or downgrade to warning when the indicator has a non-default legend (proxy for
  "not normalised"). Record the decision here and in `proportionality.md`.

### PROTO-016 · Report gap G-28 to the protocol owners
- Priority: P3 · Effort: S · Status: open
- Problem: v1.16 §2.6 still explains value orientation through the `relacao` column that v1.15
  removed from §2.3; the version history says the information now lives in the legend.
- Proposed fix: e-mail/issue to the protocol authors; when v1.17 lands, update the delta table.
  No code change.

### PROTO-018 · Add `spatial_data_validated` boolean to the JSON summary
- Priority: P1 (sequenced in Phase 6, immediately after PROTO-013) · Effort: S · Status: open
- Source: maintainer instruction 2026-09-12 (platform contract change).
- Statement: the stdout summary fragment and the `--json` file gain a mandatory boolean
  `spatial_data_validated` inside the `data_validate` object: `true` only when
  `spd_data.json` was provided, loaded and TERR-001/TERR-002 produced zero errors;
  `false` in every other case (absent, malformed, or errors). Field always present.
- Where: `controllers/report/file_report_generator.py::_print_json_summary` (and the
  `--json` writer), `.specs/api/cli-contract.md` JSON schema, `tests/e2e/test_golden.py`
  summary parser, goldens (reviewed re-baseline: summaries gain the new field).
- Tests: unit tests for all three states; golden fixtures with registry present-valid,
  present-invalid, absent.
- Related: PROTO-013, TERR-001, TERR-002, SEC-008
