# Golden harness changelog

Every regeneration of `tests/e2e/golden/*.json` is recorded here: date, fixture(s), reason, and
the commit/PR it shipped with. See `.claude/skills/golden-harness/SKILL.md` for the update
process — regenerate only via `make harness-update`, with the diff reviewed.

## 2026-09-13 (Phase 6 round N3: PROTO-013/PROTO-018 — territory registry, `spatial_data_validated`)

- **Fixtures re-baselined (reviewed, additive only)**: all eight pre-existing fixtures
  (`data_errors_01`, `data_errors_09`, `data_errors_11`, `data_errors_13`, `data_errors_14`,
  `data_errors_15`, `data_errors_xss`, `data_ground_truth_01`) — none of them ships a
  `spd_data.json`, so the diff is identical in shape across all eight:
  - A new, always-empty report section/title, `"Cadastro de territórios (spd_data.json)"`
    (`NamesEnum.TERR`), appears at the end of `section_order`/`sections` — the registry is
    absent, so TERR-001/TERR-002 never run (`SkipReason.DISABLED_BY_OPTION`); the title is
    pre-registered by `_prepare_statement` like every other category and additionally listed in
    the report's "skipped verifications" (not part of the golden's normalised `sections`/
    `section_order`, which only capture rendered error/warning spans).
  - `json_summary.data_validate.report.tests`: `37` → `38` (one more `NamesEnum` category, same
    precedent as PROTO-004/PROTO-006/PROTO-017's own `tests` bumps).
  - `json_summary.data_validate.spatial_data_validated`: new field, `false` for every one of
    these eight fixtures (no registry provided).
  - No other section/message content changed in any of the eight — verified programmatically
    (`set(actual["sections"]) - set(expected["sections"]) == {"Cadastro de territórios
    (spd_data.json)"}`, `set(expected) - set(actual) == set()`, and every shared section's
    `errors`/`warnings` list unchanged) before regenerating.
- **Fixtures added (additive, new goldens)**:
  - `data_ground_truth_02_registry` — a copy of `data_ground_truth_01`'s bundle plus a hand-built
    `spd_data.json` covering exactly its 19 `valores.id`/4 `proporcionalidades.id` values (all of
    which are already a subset of `valores`'s). Green: `exit_code: 0`,
    `spatial_data_validated: true`, TERR section empty.
  - `data_errors_16_registry` — the same bundle, but `spd_data.json` omits two ids present in
    `valores` (`1100015`, also referenced by `proporcionalidades`; `1100338`, `valores`-only).
    `exit_code: 1`, `spatial_data_validated: false`, TERR section carries three errors: two
    TERR-001 (`valores.xlsx`, both missing ids) and one TERR-002 (`proporcionalidades.xlsx`, the
    shared missing id) — confirming both rules fire independently against the same registry.
- **Reason**: `.specs/quality/backlog/09-protocol-v116.md`'s PROTO-013 (territory registry
  `spd_data.json`: loader + TERR-001/TERR-002 + STRUCT-004 whitelist, new dedicated `TERR`
  category) and PROTO-018 (the `spatial_data_validated` JSON summary flag, sequenced immediately
  after). `.specs/business-rules/territories.md`.
- **Bug found and fixed during this same slice (not a golden concern, a code fix)**: a real
  `proporcionalidades.xlsx`'s `id` column is `("Unnamed: 0_level_0", "id")` under pandas'
  `header=[0, 1]` read (a blank top header cell), never `("id", "id")` — only
  `tests/factories.py::make_proportionality_frame`'s own synthetic shape uses `"id"` at level 0.
  TERR-002 initially used a naive `frame[("id", "id")]` lookup (silently producing zero findings
  against `data_ground_truth_02_registry`'s deliberately-broken variant during manual smoke
  testing, before any golden was written) and was fixed to locate the `id` column by level 1
  (`rules/territories.py::_proportionality_id_column`), matching `rules/proportionality.py`'s own
  `_proportionality_missing_id` precedent — verified with a dedicated regression unit test
  reproducing the real column shape before this golden was generated.

## 2026-09-13 (Phase 6 round N2: PROTO-003/006/007/011/012/014/017)

- **Fixtures re-baselined**: all eight (`data_errors_01`, `data_errors_09`, `data_errors_11`,
  `data_errors_13`, `data_errors_14`, `data_errors_15`, `data_errors_xss`, `data_ground_truth_01`)
  gain the two new report sections (see below); only `data_errors_01` gains an additional
  content change (a new TEMP-004 error).
- **Reason**: `.specs/quality/backlog/09-protocol-v116.md`'s PROTO-003 (STRUCT-014, one worksheet
  per `.xlsx`), PROTO-006 (SCEN-005, scenario symbol charset), PROTO-007 (STRUCT-013, proactive
  UTF-8 check), PROTO-011 (LEG-008 six-hex tightening + LEG-016 slice-count warning), PROTO-012
  (LEG-014 empty-cell narrowing), PROTO-014 (TEMP-004/TEMP-005), and PROTO-017 (VAL-006 `id`
  uniqueness).
- **Content diff (every fixture, reviewed line-by-line)**:
  - Two new, always-empty-today report sections/titles appear at the end of `section_order`
    (new `NamesEnum` members, so `get_verify_names()`/the report always lists them, findings or
    not — matching every prior new-category precedent, e.g. `CATEG_DESC`): **"Conjunto de
    caracteres do símbolo de cenário"** (SCEN-005/`SYMB_SCEN`) and **"Unicidade do identificador
    em valores"** (VAL-006/`UNIQ_VAL`). `json_summary.data_validate.report.tests` moves
    35 → 37 in every fixture accordingly.
  - **TEMP-004** (`data_errors_01` only): one new error in "Anos em referência temporal" —
    `referencia_temporal.xlsx`'s `simbolo="2050B"` is not exactly four numeric characters (a
    known, pre-existing defect in that fixture, previously undetected by `CLEAN-005`'s looser
    "parses as a non-negative integer" check). No other fixture's `simbolo` values fail the
    four-digit format.
  - **STRUCT-014** (none): no fixture's `.xlsx` files have more than one worksheet (verified via
    `python_calamine.CalamineWorkbook.from_path(...).sheet_names` over every `data/input/**/*.xlsx`
    file) — the new check never fires against a real fixture.
  - **STRUCT-013** (none): the bundle's one `.csv` fixture (`data_errors_xss/descricao.csv`) is
    genuinely UTF-8 with high `chardet` confidence; every other fixture delivers `.xlsx` only
    (exempt).
  - **SCEN-005** (none): every fixture's `cenarios.simbolo` values are already single ASCII
    letters (`"O"`/`"P"`).
  - **LEG-008 tightening** (none): the two fixtures that carry a `legenda` file
    (`data_ground_truth_01`, `data_errors_xss`) use six-hex colours only, never the 3-digit
    shorthand.
  - **LEG-016** (none): both legend-bearing fixtures' legend codes have 5 non-DI slices each,
    under the new 11-slice warning threshold.
  - **PROTO-012/LEG-014 narrowing** (none): `rule.LEG-014.error` never appeared in any golden
    before this change (grep confirmed) — the two legend-bearing fixtures' level≥3 `descricao`
    rows already carry a non-empty `legenda` reference, so the now-retired empty-cell branch was
    already silent for both; the narrowing is a code/spec change with no observable fixture
    impact.
  - **VAL-006** (none): no fixture's `valores.id` column has a duplicate value.
- Reviewed and applied via `make harness-update`; diff limited to exactly the items above
  (`python3 -c "..."` diffed `sections`/`section_order` key-by-key against the prior golden for
  every fixture before regenerating).

## 2026-09-13 (PROTO-008/PROTO-009/PROTO-010: DESC-014/DESC-015/DESC-017/DESC-019)

- **Fixtures re-baselined**: `data_errors_01`, `data_errors_09`, `data_errors_11`,
  `data_errors_13`, `data_errors_14`, `data_errors_15`, `data_errors_xss`, `data_ground_truth_01`
  (`data_errors_09`/`data_errors_11` change for DESC-014 too; every fixture changes for DESC-015
  because every current `descricao` sheet has a level-1 indicator with `cenario=1` whose direct
  children lack it — see the "IMPORTANT" note below; `data_errors_xss` changes for DESC-019 too;
  DESC-017 fires in none of the eight fixtures — every fixture's `ordem` values already form a
  valid `1..n` sequence per parent).
- **Reason**: PROTO-008 (`.specs/quality/backlog/09-protocol-v116.md`) implements DESC-014,
  protocol §2.3 p.6: "Não inserir um codigo de menor nível entre codigos de níveis superiores."
  PROTO-009 implements DESC-015, protocol §2.3 p.8: `cenario` ∈ {0, 1} plus "se um índice possui
  cenário, todos os índices construídos a partir deste também deverão" (hierarchy propagation).
  PROTO-010 implements DESC-017 (`ordem` sibling sequence, protocol §2.3 pp.7-8 / `#202`) and
  DESC-019 (`nome_completo` ≥ `nome_simples` length, protocol p.7).
- **Content diff (every fixture, reviewed line-by-line)**:
  - New section **"Categoria do indicador"** is NOT part of this entry (already added by the
    PROTO-004 entry above); the diff below is additional to that one.
  - **DESC-014** (`data_errors_09`, `data_errors_11` only): one new error each in "Níveis de
    indicadores" — `data_errors_09`'s `codigo=6` has `nivel=2` right after `codigo=5`'s `nivel=3`
    (a known, pre-existing defect in that fixture, previously undetected); `data_errors_11`'s
    `codigo=9` has `nivel=1` right after `codigo=8`'s `nivel=5` (same kind of defect). No other
    fixture's `codigo`/`nivel` pairs violate non-decreasing order.
  - **DESC-015** (every fixture): every fixture's `descricao` has `codigo=2` (`nivel=2`) with
    `cenario=1`, and its two direct `composicao` children (`codigo=3`/`codigo=4` in the clean
    fixtures; different codes in the error fixtures with a scrambled tree) both have `cenario=0`
    — each such edge gains one new **warning** in "Hierarquia como árvore": `"…: O indicador pai
    {N} (cenario 1) e o indicador filho {M} (cenario 0) devem compartilhar o mesmo valor de
    'cenario'."` (`rule.DESC-015.propagation_warning`). The check is **directional** (parent
    `cenario=1` → child must be `1` too; the reverse, a child with `cenario=1` whose parent lacks
    it, is NOT flagged — see `rules/description.py::check_scenario_domain_and_propagation`'s
    docstring), matching the backlog's own worked example; a fully bidirectional/
    transitive-closure reading would report even more (rejected as out of scope for this slice,
    documented in `.specs/business-rules/description.md`). The domain half (`cenario` outside
    `{0, 1}`, `rule.DESC-015.domain_error`) is unaffected and stays an **error** — none of the
    eight fixtures currently trigger it.
  - **Amendment, same day (orchestrator staging decision)**: this entry originally shipped with
    the propagation half as an **error**, which flipped `data_ground_truth_01`'s `exit_code` from
    `0` to `1` (`errors` `0` → `2`) — the first time the canonical "clean"/"everything passes"
    fixture (`CLAUDE.md`'s `make run FIXTURE=data_ground_truth_01`) reported a failure. Before
    that change reached a commit, it was staged down to a **warning** (matching the PROTO-004
    staging precedent for `categoria`): the message text is unchanged, only the severity and
    message key (`rule.DESC-015.propagation_error` → `rule.DESC-015.propagation_warning`) moved.
    `data_ground_truth_01`'s `exit_code` is back to `0` (`errors` unchanged at `0`, `warnings`
    `+2`); every other fixture keeps the same `errors` count it had before DESC-015 existed, with
    the two propagation lines counted as `warnings` instead. See
    `.specs/business-rules/protocol-changelog.md`'s PROTO-009/DESC-015 maintainer note for the
    full staging record — promoting the propagation half back to an error is left to a future
    owner decision.
  - **DESC-019** (`data_errors_xss` only): one new warning in "Padrão para nomes dos
    indicadores" — this fixture's known mutation (an `<Script>Alert(1)</Script>` payload
    appended to row 1's `nome_simples`) makes `nome_simples` (45 characters) longer than
    `nome_completo` (33 characters), which the pre-existing mutation never triggered before this
    rule existed.
  - No other section, and no other fixture's `errors`/`warnings` counts beyond the above, changed.

## 2026-09-13 (PROTO-004: DESC-013 `categoria` domain + staged absence warning)

- **Fixtures re-baselined**: all eight — `data_errors_01`, `data_errors_09`, `data_errors_11`,
  `data_errors_13`, `data_errors_14`, `data_errors_15`, `data_errors_xss`, `data_ground_truth_01`.
- **Reason**: PROTO-004 (`.specs/quality/backlog/09-protocol-v116.md`) implements DESC-013 per
  protocol §2.3 p.8 (since v1.13): `descricao.categoria` must be one of `social`/`economico`/
  `ambiental`/`climatico`. Staged rollout, step 1: the column's absence is a **warning**, not a
  missing-required-column error (a future re-baseline promotes it to an error once sectors have
  had time to add the column); `specs/sheet_specs.py` gains `categoria` as `ColumnKind.OPTIONAL`,
  and `NamesEnum.CATEG_DESC` (`verification_name_indicator_category`) is a new report category.
- **Content diff (every fixture, reviewed line-by-line)**: strictly additive —
  - New section **"Categoria do indicador"** appears in `section_order`/`sections` for every
    fixture (none of the eight fixtures' `descricao` sheets carry a `categoria` column), each
    with exactly one warning: `"{filename}: A coluna 'categoria' está ausente; o protocolo exige
    uma categoria (social, economico, ambiental ou climatico) para cada indicador."`.
  - `json_summary.data_validate.report.tests`: `34` → `35` (one new registered category,
    `SpreadsheetProcessor._prepare_statement` pre-populates every `NamesEnum` member); `warnings`
    `+1` per fixture; `errors` unchanged.
  - No other section, and no other field, changed in any fixture.

## 2026-09-13 (PROTO-005: `desc_simples` no longer requires a trailing period)

- **Fixtures re-baselined**: all eight — `data_errors_01`, `data_errors_09`, `data_errors_11`,
  `data_errors_13`, `data_errors_14`, `data_errors_15`, `data_errors_xss`, `data_ground_truth_01`.
- **Reason**: PROTO-005 (`.specs/quality/backlog/09-protocol-v116.md`) flips DESC-006 for
  `desc_simples` per protocol §2.3 p.7 (v1.13 and v1.16 agree): "Toda descrição simples não pode
  terminar com um caractere especial como o ponto." `desc_simples` moved from
  `_MUST_END_WITH_DOT_COLUMNS` to `_NO_PUNCTUATION_COLUMNS` in `rules/description.py`; only
  `desc_completa` still requires a trailing period.
- **Content diff (every fixture, reviewed line-by-line)**: strictly confined to the
  "Pontuações obrigatórias e proibidas em descrições" section and the derived `warnings` count in
  `json_summary`/CLI `tests`/`errors` fields unaffected:
  - Every `descricao` row whose `desc_simples` cell ends with `.` (every fixture's `descricao`
    sheet happened to end every `desc_simples` cell with a period, matching the *old*,
    now-reversed rule) gains one new warning: `"…, linha {row}: O valor da coluna 'desc_simples'
    não deve terminar com pontuação."`.
  - `data_errors_01` additionally **loses** its pre-existing `"…, linha 3: O valor da coluna
    'desc_simples' deve terminar com ponto."` warning (that row's `desc_simples` cell does not end
    with `.`, which used to violate the old "must end with dot" rule and now satisfies the new
    "must not end with dot" rule).
  - No other section, no `errors` count, and no other fixture field changed.
- No new/removed fixture in this entry (unlike the entry below, which added `data_errors_xss`).

## 2026-09-13

- **Fixtures re-baselined**: `data_errors_01` (one line changed, everything else byte-identical).
- **Fixture added**: `data_errors_xss` (new, additive — a `data_ground_truth_01` copy with one
  cell mutated: `descricao`'s row-1 `nome_simples` gets ` <Script>Alert(1)</Script>` appended,
  which breaks `DESC-004`'s ABNT-capitalisation check and surfaces the raw payload verbatim in
  that rule's "Encontrado: '...'" warning text).
- **Reason**: SEC-001 (Phase 4) rebuilt `FileReportGenerator`/`report_template.html` on
  `Environment(loader=PackageLoader(...), autoescape=select_autoescape(["html"]))` (ADR-0007):
  every message/CLI-metadata value is now escaped before being written to the saved HTML report,
  instead of being concatenated as a raw string in Python
  (`FileReportGenerator._format_messages_as_html`, deleted). The golden harness's own extractor
  (`_ReportSectionParser`, an `HTMLParser` with `convert_charrefs=True`) unescapes entities back
  to plain text before comparison, so this change is invisible to the stored JSON goldens **except**
  where a message previously contained a literal `<`/`>` that the pre-fix, non-escaping renderer
  emitted raw into the HTML — the naive `HTMLParser` misread that raw `<...>` as a bogus tag and
  silently dropped its contents from the extracted text. `data_errors_01`'s
  "Estrutura dos arquivos da pasta de entrada" section carries exactly one such case: a corrupt
  `legenda.xlsx` raises `python_calamine.CalamineError`, and the abort message embeds
  `str(type(exc))` (`"...Detalhes: Cannot detect file format (<class 'python_calamine.CalamineError'>)"`).
  Pre-fix, the raw `<class 'python_calamine.CalamineError'>` in the saved HTML was parsed as a
  (bogus) tag and its text silently disappeared, so the *previous* golden recorded the mangled
  `"...format ()"`. Post-fix, the same content is written as
  `&lt;class &#39;python_calamine.CalamineError&#39;&gt;`, which `HTMLParser` correctly unescapes
  back to the full, undamaged message — this is the one and only content diff in
  `data_errors_01.json`, reviewed line-by-line above; no other fixture's extracted section content
  changed at all (`exit_code`, already excluded from the comparison per the 2026-09-12 entry below,
  is the only other field that differs, an artefact of re-running the harness rather than of this
  change).
- **XSS regression evidence** (not itself part of the golden, verified manually and via
  `tests/unit/controllers/report/test_file_report_generator.py::TestXssEscaping`): the raw HTML
  report generated for `data_errors_xss` contains `&lt;Script&gt;Alert(1)&lt;/Script&gt;`, never a
  literal `<Script>` tag.

## 2026-09-12

- **Fixtures**: none regenerated — every `tests/e2e/golden/*.json` file is byte-identical to the
  previous baseline.
- **Reason**: ARC-011/SEC-008 landed the documented exit-code contract (`0` = no errors, `1` =
  validation errors found, `2` = a runtime failure — `.specs/api/cli-contract.md`,
  `docs/adrs/0005-cli-contract-flags-exit-codes-json.md`), replacing the previous "always 0".
  `tests/e2e/test_golden.py::test_golden_report` now asserts the CLI's real exit code against the
  expected value derived from the run's own parsed JSON summary (`0` for `data_ground_truth_01`,
  `1` for every `data_errors_*` fixture) as a dedicated assertion, instead of hardcoding
  `result.returncode == 0` for every fixture.
- **Notes**: every stored golden file still carries `"exit_code": 0` from before this change (the
  field was never meaningful before SEC-008, since the CLI always exited 0). Re-baselining every
  golden purely to update that one stale field was judged unnecessary churn for a value the
  content diff no longer needs: the golden equality comparison now excludes the `exit_code` key
  (the real contract check happens via the dedicated assertion described above, not via the
  golden diff), so the stale `0` values are harmless and require no action until the next
  deliberate `make harness-update`.

## 2026-08-25

- **Fixtures**: all (`data_errors_01`, `data_errors_09`, `data_errors_11`, `data_errors_13`,
  `data_errors_14`, `data_errors_15`, `data_ground_truth_01`).
- **Reason**: initial baseline for the golden harness, generated from v0.7.65 @ d1ae7c1. No prior
  golden existed; this is the safety net the migration (Phase 1 onward) will be diffed against.
- **Notes**: `spell_skipped: true` in every golden — this development environment has `pyenchant`
  installed but no `pt_BR` hunspell word list, so the `SPELL-*` rules were not exercised. Re-running
  `make harness-update` on a machine with `hunspell-pt-br` installed will exercise spelling and
  should be reviewed as a deliberate, separate golden update.
- **Non-determinism found and normalised (harness-side, not a golden change)**: three consecutive
  `make test-e2e` runs showed `data_errors_11` flapping — two "missing required column" messages
  from `value_validator.py` (built from a Python `set` difference) swapped order between process
  runs. `tests/e2e/test_golden.py` now sorts the `errors`/`warnings` lists within each section
  before storing/comparing, so message *order* is not part of the golden's signal — only message
  *presence/text* is. The underlying `set`-ordering issue in the pipeline is unchanged (out of
  scope here; see backlog for a vectorised-columns fix).
