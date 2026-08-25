---
name: spreadsheet-protocol
description: Use whenever you need the exact shape of an AdaptaBrasil data bundle — which sheets exist, their required/optional/dynamic columns, column name patterns, level semantics, the DI marker, legend/proportionality math, or the CSV format. Domain reference for anyone writing or reviewing a validation rule.
---

# The AdaptaBrasil spreadsheet protocol (v1.13)

A bundle is one folder containing up to 8 files, each `.csv` (separator `|`) or `.xlsx`. Sheet
base names are fixed (from `data_validate/helpers/tools/data_loader/common/config.py`):

| Sheet (base name) | Required | Header | Model |
|---|---|---|---|
| `descricao` | yes | single | `SpDescription` |
| `composicao` | yes | single | `SpComposition` |
| `valores` | yes | single | `SpValue` |
| `referencia_temporal` | yes | single | `SpTemporalReference` |
| `proporcionalidades` | no | **double** | `SpProportionality` |
| `cenarios` | no | single | `SpScenario` |
| `legenda` | no | single | `SpLegend` |
| `dicionario` | no | single | `SpDictionary` |

CSV separator is always `|` — a `|` inside a cell value or column name is itself a structural
error (`DataFrameProcessing.check_dataframe_vertical_bar`). File extensions accepted:
`.csv`, `.xlsx`, `.qml`.

## `descricao` — indicator metadata (one row per indicator)

Required columns: `codigo` (int, sequential from 1, unique — `SC`/`CO_UN` in `NamesEnum`),
`nivel` (int ≥ 1), `nome_simples` (str, ≤ 40 chars — `TITLES_N`), `nome_completo` (str),
`desc_simples` (str, ≤ 150 chars — `SIMP_DESC_N`), `desc_completa` (str), `fontes` (str),
`meta` (str). Dynamic columns (present only if the corresponding sheet is configured):
`cenario` (int ≥ -1, requires `cenarios` sheet), `legenda` (int ≥ 1, allows empty, requires
`legenda` sheet). Optional columns, filled with defaults if absent: `unidade` (str, default `""`),
`relacao` (int, default `1`), `ordem` (int). Plural variants `nomes_simples`/`nomes_completos`
exist for uniqueness checks across indicator groups (`UT`).

Name columns must be capitalized with acronyms preserved and no CR/LF or doubled spaces
(`INP`/`LB_DESC`); description columns must end with a period, name columns must not end with
punctuation (`MAND_PUNC_DESC`); no column may contain HTML tags (`HTML_DESC`); no required text
column may be empty (`EF`).

## `composicao` — parent/child hierarchy (tree/graph)

Required columns only: `codigo_pai` (int ≥ 1), `codigo_filho` (int ≥ 1). Every `codigo`/
`codigo_filho`/`codigo_pai` value must resolve to a `codigo` in `descricao`. The graph must be a
tree per root (no cycles, no disconnected nodes — `TH`), a child's `nivel` must be exactly one
greater than its parent's (`CHILD_LVL`), and leaf indicators must have data in `valores`
(`LEAF_NO_DATA`).

## `valores` — indicator values over time/scenario

Required: `id` (int). All other columns are **dynamic**, one per `CÓDIGO-ANO[-CENÁRIO]`
combination, matched against `codigo` in `descricao` × years in `referencia_temporal` ×
symbols in `cenarios` (if present). Column-name pattern (from
`CollectionsProcessing.categorize_strings_by_id_pattern_from_list`):

- No scenarios configured: `^\d{1,}-\d{4}$` (e.g. `12-2030`).
- Scenarios configured: `^\d{1,}-\d{4}-(?:<suffix1>|<suffix2>|...)$`, suffixes being the
  `cenarios.simbolo` values escaped for regex (e.g. `12-2030-SSP1`).

Cell values must be numeric with **at most 2 decimal places**, or the literal marker `DI`
(`ApplicationConfig.VALUE_DATA_UNAVAILABLE`) meaning "Dado indisponível" — never blank, never any
other non-numeric string (`UNAV_INV`/`VAL_COMB`).

## `referencia_temporal` — years/periods

Required: `nome` (int), `descricao` (str, must end with a period — `MAND_PUNC_TEMP`), `simbolo`
(int ≥ 0). If `cenarios` does not exist/is empty, the sheet must have **exactly one row**
(`YEARS_TEMP`); symbol values must be unique (`UVR_TEMP`).

## `cenarios` — scenario symbols (optional)

Required: `nome` (int), `descricao` (str, ends with a period — `MAND_PUNC_SCEN`), `simbolo` (int).
`simbolo` values must be unique (`UVR_SCEN`) — duplicates are a structural error raised in
`SpScenario.pre_processing`. When this sheet exists, `descricao.cenario` and the `-CENÁRIO` suffix
in `valores`/`proporcionalidades` column names become active.

## `legenda` — classification ranges (optional)

Required: `codigo` (int, sequential — grouped so multiple legends can coexist by `codigo`),
`label` (str), `cor` (str, hex `#RRGGBB` — `LEG_REL`... color format check),
`minimo` (float, ≤ 2 decimals), `maximo` (float, ≤ 2 decimals), `ordem` (int, sequential per
group). Business rules (`LegendProcessing`, `NamesEnum.LEG_RANGE`/`LEG_OVER`/`LEG_REL`):

- Exactly one row per `codigo` group has `label == "Dado indisponível"`
  (`ApplicationConfig.LABEL_DATA_UNAVAILABLE`); that row's `minimo`/`maximo` must be **empty**.
  Zero or more-than-one such row is an error.
- All other rows: `minimo < maximo`, sorted ascending, and **continuous**: the next row's
  `minimo` must equal the previous row's `maximo + 0.01` exactly (`Decimal` comparison, not
  float) — this is the "+0.01 legend continuity" rule. A gap or overlap is an error.
- `minimo`/`maximo` with more than 2 decimal places abort the continuity checks for that group
  with a dedicated error instead of a misleading continuity error.
- Levels 1 and 2 indicators reference `legenda.codigo` via `descricao.legenda`; every referenced
  code must exist.

## `proporcionalidades` — influence weights (optional, **double header**)

Two header rows. Level-0 (top) header groups columns by `CÓDIGO-ANO[-CENÁRIO]` (same pattern as
`valores`); level-1 (second) header repeats `id` once and then one `CÓDIGO-ANO[-CENÁRIO]` sub-
column per child indicator contributing to that parent. Required column name (level-1): `id`
(int) — the child indicator's own code, repeated per row (`REP_IND_PROP` checks no unexpected
repeats within a parent group beyond what the tree in `composicao` implies).

Business rules (`ProportionalityProcessing`, `NamesEnum.SUM_PROP`/`IR_PROP`/`IND_VAL_PROP`):

- Every parent's child weights, for a given `CÓDIGO-ANO[-CENÁRIO]`, must be numeric with **at
  most 3 decimal places** (`PRECISION_DECIMAL_PLACE_TRUNCATE = 3`) or `DI`.
- Row sums (via `Decimal`, truncated to 3 places) must equal **1 exactly** for a clean pass; a sum
  within `[0.99, 1.01]` but not exactly `1` is a **warning**; outside that tolerance is an
  **error** ("A soma dos valores para o indicador pai {parent_id} é {sum}, e não 1.").
- A row summing to exactly `0` is only valid if the corresponding parent/year/scenario values in
  `valores` are also `0` or `DI` — otherwise it is an error.
- Every child referenced must exist in `composicao` as a child of that parent, and every
  `CÓDIGO-ANO[-CENÁRIO]` combination must exist in `valores` (`IR_PROP`/`IND_VAL_PROP`).
- Row indices in messages use `idx + 3` (two header rows, not one) — see
  `.claude/rules/dataframe-conventions.md`.

## `dicionario` — spell-check exception list (optional)

Required: `palavra` (str) — one word/acronym per row, added to the pt-BR/en-US dictionaries used
by `SpellCheckerValidator` (pyenchant/hunspell) so domain acronyms are not flagged as misspellings.
URLs and values in `fontes` columns are ignored by the spell checker.

## Cross-cutting conventions

- `DI` (exact string) = "Dado indisponível" (unavailable data) — always a valid alternative to a
  numeric value in `valores` and `proporcionalidades`; never valid in `legenda` `minimo`/`maximo`.
- Row-number in messages = DataFrame 0-based index + 2 for single-header sheets, + 3 for
  `proporcionalidades` (double header) — always via a single helper, never inline arithmetic
  scattered across validators (see `dataframe-conventions.md`).
- Report limit: at most `ApplicationConfig.REPORT_LIMIT_N_MESSAGES = 20` messages shown per
  validation type; the rest are counted, not dropped silently.
- Title length limit 40 chars (`nome_simples`), simple-description limit 150 chars
  (`desc_simples`) — `ApplicationConfig.TITLE_OVER_N_CHARS` / `SIMPLE_DESCRIPTIONS_OVER_N_CHARS`.
- Numeric precision: 2 decimal places for `valores`/`legenda`, 3 decimal places for
  `proporcionalidades`.

For the authoritative text behind any of these rules, consult `assets/protocolo-v-1.13.pdf` via
the `protocol-expert` agent, and cross-check `.specs/business-rules/<sheet>.md` for the current
rule-ID ↔ code ↔ test mapping.
