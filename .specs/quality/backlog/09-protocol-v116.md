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
- Priority: P1 · Effort: S · Status: open
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

### PROTO-002 · Stop injecting/expecting the removed `relacao` column
- Priority: P1 · Effort: S · Status: open
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

### PROTO-003 · STRUCT-014: each `.xlsx` must contain exactly one worksheet
- Priority: P1 · Effort: M · Status: open
- Protocol: §2 p.3 (since v1.14).
- Where: `helpers/tools/data_loader/readers/excel_reader.py` (calamine reads the first sheet
  silently), new rule STRUCT-014, message keys in both catalogs.
- Proposed fix: list worksheets via `python_calamine.CalamineWorkbook.sheet_names`; >1 sheet →
  error naming the file and the extra sheets; register STRUCT-014 under `FS`.
- Tests: unit with a 2-sheet xlsx fixture built via openpyxl in tmp_path; golden case in a
  data_errors fixture (new fixture folder or extend an existing one — reviewed re-baseline).

### PROTO-004 · DESC-013: require `categoria` and validate its domain
- Priority: P1 · Effort: M · Status: open
- Protocol: §2.3 p.8 (since v1.13): one of `social`, `economico`, `ambiental`, `climatico`.
- Where: `models/sp_description.py` (unknown column today → unexpected-column warning),
  `specs/sheet_specs.py`, new rule DESC-013.
- Proposed fix (staged to protect current sectors): step 1 — accept the column, validate the
  domain when present (errors on invalid values), emit a **warning** when the column is absent;
  step 2 (Phase 4 re-baseline) — absence becomes an error. Record the staging in
  `description.md`.
- Tests: table-driven domain cases incl. accented variants rejected; goldens: current fixtures
  lack `categoria` → the new absence-warning changes goldens — reviewed re-baseline required.

### PROTO-005 · Flip DESC-006 for `desc_simples`: forbid the trailing period (G-07)
- Priority: P2 · Effort: S · Status: open
- Protocol: §2.3 p.7 (v1.13 and v1.16 agree): "Toda descrição simples não pode terminar com um
  caractere especial como o ponto." The code requires the period.
- Proposed fix: `desc_simples` moves from `columns_must_end_with_dot` to
  `columns_dont_punctuation` in `SpDescriptionValidator.validate_punctuation`; message text stays
  the catalog-consistent "não deve terminar com pontuação".
- Tests: unit; goldens change wherever fixtures end `desc_simples` with "." — reviewed
  re-baseline with the protocol quote in the golden CHANGELOG.

### PROTO-006 · SCEN-005: scenario symbol is one character, letters/digits only (G-17)
- Priority: P2 · Effort: S · Status: open
- Protocol: §2.1 p.4: "Um único caractere … apenas letras e números".
- Proposed fix: new rule in the scenario validator (`len == 1` and `isalnum()`); register under
  `MAND_PUNC_SCEN` or a new title (decide with the rule-authoring skill).
- Tests: unit table (multi-char, space, punctuation, accents); golden case.

### PROTO-007 · STRUCT-013: proactive UTF-8 check with the FAQ message (G-01)
- Priority: P2 · Effort: M · Status: open
- Protocol: §2 p.3 + FAQ "O arquivo XXX está no formato YYY, deveria ser UTF-8."
- Proposed fix: on CSV load, detect encoding (`FileSystemUtils.detect_encoding`, currently unused)
  and emit exactly the FAQ message shape as an error; xlsx exempt (zip container).
- Tests: latin-1 fixture file; golden case.

### PROTO-008 · DESC-014: codes ordered by hierarchy level (G-06)
- Priority: P2 · Effort: M · Status: open
- Protocol: §2.3 p.6: codes sequential AND grouped from level 1 downwards; "Não inserir um codigo
  de menor nível entre codigos de níveis superiores."
- Proposed fix: after cleaning, assert `nivel` is non-decreasing along ascending `codigo`.
- Tests: unit; golden case.

### PROTO-009 · DESC-015: `cenario` ∈ {0,1} plus hierarchy propagation (G-09)
- Priority: P2 · Effort: M · Status: open
- Protocol: §2.3 p.8: values 0/1; scenario membership propagates up and down the composition.
- Where: `models/sp_description.py::data_cleaning` currently cleans `cenario` with
  `min_value=-1` (accepts −1).
- Proposed fix: domain {0,1}; propagation check joins description with the composition tree.
- Tests: unit (−1 rejected; parent with scenario whose child lacks it → error); golden case.

### PROTO-010 · DESC-017/DESC-019: `ordem` sibling sequence and `nome_completo` length (G-10)
- Priority: P2 · Effort: M · Status: open
- Protocol: §2.3 pp.7–8: `ordem` integers 1..n per parent (`#202`); `nome_completo` at least as
  long as `nome_simples`. (`DESC-016` for `relacao` is retired unimplemented — column removed;
  `DESC-018` `meta` format stays parked until owners specify it formally.)
- Tests: unit per rule; golden cases.

### PROTO-011 · Legend tightening: six-hex colours, ≤ 11 slices (G-19, G-21 → LEG-016)
- Priority: P2 · Effort: S · Status: open
- Protocol: §2.5 pp.10–11: `cor` = "#" + six hex digits; up to 11 intervals (5–7 advised); grey
  reserved for "Dado indisponível".
- Proposed fix: tighten LEG-008's regex to 6-hex only; new LEG-016 warning for >11 slices; grey
  advisory left as documentation.
- Tests: unit (`#abc` now invalid); goldens: check fixtures for 3-hex colours before deciding on
  re-baseline.

### PROTO-012 · Empty `legenda` cell means default legend, not an error (G-20)
- Priority: P2 · Effort: M · Status: open
- Protocol: §2.3 p.8: "Quando esta coluna for usada, todos os valores vazios serão associados à
  legenda default."
- Where: `validators/spreadsheets/legend/legend_validator.py` LEG-014 errors for levels ≥3 without
  a legend reference.
- Proposed fix: empty cell → default legend [0,1]; LEG-014's error narrows to dangling references
  (non-empty values that match no legend code).
- Tests: unit; goldens change for fixtures that trigger today's LEG-014 — reviewed re-baseline.

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
- Priority: P2 · Effort: S · Status: open
- Protocol: §2.6 p.11 ("identificador único"); gap G-13 (uniqueness half).
- Proposed fix: duplicate values in `valores.id` → error listing the duplicated ids; no registry
  needed. Register VAL-006 under `FS` or `UNAV_INV` (decide via the rule-authoring skill).
- Tests: unit + golden case.

### PROTO-014 · TEMP-004/TEMP-005: four-digit symbols and single observed time (G-15, G-16)
- Priority: P3 · Effort: S · Status: open
- Protocol: §2.2 p.5: `simbolo` four numeric characters; only one observed (non-future) reference
  supported by the platform (footnote).
- Tests: unit; golden case.

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
