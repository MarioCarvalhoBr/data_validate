# Protocol versions and protocol ↔ code gaps

Protocol: "Especificação de Requisitos e Formatos para Entrega de Setores Estratégicos para o
AdaptaBrasil MCTI" — **current version 1.16, 2026-08-21** (`assets/protocolo-v-1.16.pdf`;
`assets/protocolo-v-1.13.pdf` and `assets/protocolo-1.0.pdf` are kept as historical references).
The validator declares which protocol version it implements via `MetadataInfo.PROTOCOL_VERSION`/
`__protocol_version__ = "1.16"` (backlog DOC-006, done), surfaced in the HTML report's version
line; this table records what each version changed and whether the code follows it. The rule
files in this directory were originally traced against v1.13; v1.16 deltas are recorded below and
in each affected file under "Protocol v1.16 update", and the code changes they require are
backlog items `PROTO-001…` in `.specs/quality/backlog/09-protocol-v116.md`.

## v1.13 → v1.16 delta (announced by the user on 2026-09-12)

| Change | Protocol | Affected rules | Code status |
|---|---|---|---|
| Each `.xlsx` file must contain exactly one worksheet | §2 p.3 (v1.14) | STRUCT-014 | **implemented** (PROTO-003, done 2026-09-13) — `DataLoaderFacade.load()` reports extra worksheets; the first sheet is still what gets parsed |
| `relacao` column removed from `descricao` ("esta informação já esta na legenda") | §2.3 (v1.15 history) | DESC-011/12 column set, COMP tree prerequisites | **implemented** — `relacao` is `ColumnKind.DEPRECATED`, no longer injected, no longer required by the composition tree checks (PROTO-002, done) |
| `fontes` column removed from `descricao` ("não é usada") | §2.3 (v1.16 history) | DESC-011 required-column set, SPELL exception | **implemented** — `fontes` is `ColumnKind.DEPRECATED`, accepted silently, no longer required (PROTO-001, done) |
| `categoria` domain restated (social, economico, ambiental, climatico) | §2.3 p.8 | DESC-013 | **implemented** (G-05, PROTO-004 step 1, done) — domain validated when present; absence is a staged warning, not yet an error |
| Scenario `simbolo` explicitly "Um único caractere", letters/digits | §2.1 p.4 | SCEN-005 | **implemented** (PROTO-006, done 2026-09-13) — length 1 + ASCII alphanumeric |
| §2.6 still explains value orientation via `relacao` although §2.3 removed it | §2.6 p.12 vs §2.3 | — | **protocol internal inconsistency** (new gap G-28) — report to the protocol owners |
| `#…#` spell-ignore delimiter absent from the v1.16 FAQ | §"6)" p.16–17 | SPELL | G-25 downgraded to historical; confirm with owners before implementing |

## Version history (protocol §7; v1.16 pp.17–19)

| Version | Date | Change | Code status |
|---|---|---|---|
| 1.16 | 2026-08-21 | `fontes` removed from `descricao` | **implemented** (PROTO-001, done) |
| 1.15 | 2026-08-11 | Editorial fixes; `relacao` removed from `descricao` | **implemented** (PROTO-002, done) |
| 1.14 | 2025-10-02 | Each xlsx file must have exactly one worksheet | **implemented** (PROTO-003, done 2026-09-13) |
| 1.13 | 2025-08-05 | New `categoria` column in `descricao` | **implemented** (G-05, PROTO-004 step 1, done) |
| 1.12 | 2025-07-22 | Better description of the `legenda` column in `descricao` | n/a (documentation) |
| 1.11 | 2025-05-23 | Legends only through the optional `legenda.xlsx` (QML dropped) | implemented; `.qml` still scanned by the loader (G-04) |
| 1.10 | 2025-03-21 | Scenario `simbolo` letters/digits only; optional `dicionario.xlsx` | dictionary implemented; charset **implemented** (G-17, PROTO-006, done 2026-09-13) |
| 1.9 | 2025-03-07 | Child level > parent level; siblings share a level | COMP-008, COMP-009 |
| 1.8 | 2024-10-10 | Two decimals for values, three for proportionalities; QML naming `XX.qml` | VAL-005, PROP-008 |
| 1.7 | 2024-10-07 | `#…#` delimiter ignored by the spell-checker; legend format update | delimiter **not implemented** (G-25) |
| 1.6 | 2024-09-25 | Figure 3; `cenario` description | n/a |
| 1.5 | 2024-08-07 | Zero/NI composition ⇒ factors zero, sum zero | PROP-009 |
| 1.4 | 2024-07-31 | Optional `ordem` column | accepted as optional; **sequence validated** (G-10, DESC-017, PROTO-010, done) |
| 1.3 | 2024-07-16 | §4 error explanations; UTF-8 requirement; FAQ | UTF-8 check **implemented, proactive** (G-01, PROTO-007, done 2026-09-13) |
| 1.2 | 2024-06-28 | `DI` in proportionalities | PROP-007 |
| 1.1 | 2024-06-14 | `DI` in values; version history; unique identifiers | VAL-004 |
| 1.0 | 2024-05-09 | First version, delivered with the validation tool | — |

## How to version the protocol in the tool (target)

1. **Done (DOC-006)**: `PROTOCOL_VERSION = "1.16"` constant — lives on `MetadataInfo`
   (`data_validate/config/metadata_info.py`), not yet on the sheet-spec registry; surfaced in the
   report header's version line. Not yet printed by `--version` (that flag shows only the tool
   version, via `argparse`'s own `action="version"`, read-only per DOC-006's brief).
2. Still open: each rule carries `since: <protocol version>` and, when removed, `until:`.
3. Still open: a protocol bump is an ADR + an entry here + updates to the rule files + golden
   re-baseline with reviewed diff.

## Consolidated gap list (protocol ↔ current code)

| ID | Where | Gap | Suggested action |
|---|---|---|---|
| G-01 | file-structure | UTF-8 not detected proactively; FAQ message "está no formato YYY, deveria ser UTF-8" never emitted | **resolved** — STRUCT-013 (PROTO-007, done) using `chardet` (only a confident, non-UTF-8-decodable sample is flagged) |
| G-02 | file-structure | `\|` inside CSV cannot be detected after parsing | pre-parse raw scan for CSV |
| G-03 | file-structure | decimal comma mandated for CSV; code accepts `.` too | keep lenient, document |
| G-04 | file-structure | `.qml` still scanned | remove from loader config |
| G-05 | description | `categoria` (v1.13) unknown to the code | **resolved** — DESC-013 (domain check), step 1 (PROTO-004, done); step 2 (absence → error) still open |
| G-06 | description | codes must be ordered by level | **resolved** — DESC-014 (PROTO-008, done) |
| G-07 | description | `desc_simples` trailing `.`: code requires, protocol forbids | **resolved** (PROTO-005, done, 2026-09-13) — DESC-006 now forbids it, goldens re-baselined |
| G-08 | several | `LB_SCEN`, `LB_TEMP`, `LEG_OVER` titles registered but never emitted | either implement CR/LF checks for scenarios/temporal reference and map overlap to LEG-010, or drop the titles |
| G-09 | description/values | `cenario` domain {0,1} and hierarchy propagation | **resolved** — DESC-015 (PROTO-009, done); domain half is an error, propagation half is staged as a **warning** (see the maintainer note below); scoped to direct `composicao` edges, not the full transitive closure |
| G-10 | description | `relacao ∈ {1,−1}`, `ordem` sibling sequence, `meta` format, `nome_completo` length | `relacao` sub-gap retired unimplemented (column removed, PROTO-002); **`ordem` sequence resolved** — DESC-017 (PROTO-010, done); `meta` format still parked (DESC-018, no owner decision); **`nome_completo` length resolved** — DESC-019 (PROTO-010, done) |
| G-11 | description/composition | global uniqueness of names vs per-subtree | clarify; possibly a second UT variant |
| G-12 | composition | root semantics (code `0` vs node `"1"`) | unify in `SheetSpec` |
| G-13 | values | `id` completeness/uniqueness | **uniqueness resolved** — VAL-006 (PROTO-017, done); completeness out of scope (tracked as TERR-001, PROTO-013) |
| G-14 | values | [0,1] normalisation only via legend default | document |
| G-15 | temporal | four-digit symbol | **resolved** — TEMP-004 (PROTO-014, done) |
| G-16 | temporal | at most one observed (past/present) time | **resolved** — TEMP-005 (PROTO-014, done, warning severity) |
| G-17 | scenarios | symbol charset | **resolved** — SCEN-005 (PROTO-006, done) |
| G-18 | scenarios | default symbols `O`/`P` when file absent | clarify with protocol owners |
| G-19 | legend | colour must be six hex digits | **resolved** — LEG-008 tightened to `^#[A-Fa-f0-9]{6}$` (PROTO-011, done) |
| G-20 | legend | empty `legenda` ⇒ default legend vs LEG-014 error | **resolved** — LEG-014 retired to a permanent no-op (PROTO-012, done) |
| G-21 | legend | grey for DI; max 11 slices | **max-slices half resolved** — LEG-016 warning (PROTO-011, done); grey-for-DI stays documentation only |
| G-22 | legend | legend must cover data min/max | equivalent to LEG-015; document |
| G-23 | proportionality | blank cells treated as valid | align with protocol (error) |
| G-24 | proportionality | first two spatial columns vs single `id` | clarify |
| G-25 | spelling | `#…#` ignore delimiter (v1.7) | absent from the v1.16 FAQ — treat as historical; confirm with owners before implementing |
| G-26 | spelling | not all textual columns are checked | extend `model_columns_map` |
| G-27 | spelling | case-sensitive dictionary matching unverified | add tests |
| G-28 | values/description | §2.6 (v1.16) still references the `relacao` column removed by v1.15 | report the inconsistency to the protocol owners; until resolved, treat value orientation as legend-defined |
| ~~—~~ | spelling | dictionary initialisation errors silently dropped | **resolved** — BUG-027 fixed (`_prepare_statement` now runs and reports) |

Gap status after v1.16 (2026-09-12): G-05 and G-07 are confirmed unchanged by v1.16 (the protocol
still requires `categoria` and still forbids a trailing period in `desc_simples`); **G-05, G-06,
G-07, G-09 and G-10 are now resolved in code** (PROTO-004 step 1, PROTO-005, PROTO-008,
PROTO-009, and PROTO-010, all done 2026-09-13 — G-10's `meta`-format sub-gap, DESC-018, stays
open, parked pending an owner decision); G-25 is downgraded to historical.

**Phase 6 round N2 (2026-09-13)**: seven more gaps resolved — **G-01** (STRUCT-013, proactive
UTF-8 check), the **worksheet-count gap** behind PROTO-003 (STRUCT-014), **G-17** (SCEN-005,
symbol charset), **G-19**/**the max-slices half of G-21** (LEG-008 tightened to six-hex-only,
new LEG-016 warning), **G-20** (LEG-014 retired to a permanent no-op), **G-15**/**G-16**
(TEMP-004/TEMP-005), and **the uniqueness half of G-13** (VAL-006). None of the seven changes an
existing fixture's error/warning content except TEMP-004, which surfaces one pre-existing,
previously-undetected defect in `data_errors_01` (`referencia_temporal.simbolo="2050B"`); every
fixture's golden gains the two new, always-empty `NamesEnum` sections (`SYMB_SCEN`/`UNIQ_VAL`).
See `tests/e2e/golden/CHANGELOG.md`'s "Phase 6 round N2" entry for the full reviewed diff.

**PROTO-009/DESC-015 maintainer note (2026-09-13, staged same day)**: implementing the
`cenario` propagation check first revealed that `data_ground_truth_01` — the canonical
"everything passes" e2e fixture — has always had a level-2 indicator (`codigo=2`, `cenario=1`)
whose two direct children lack it (`cenario=0`); with the propagation half reported as an
error, the fixture's `exit_code` flipped from `0` to `1` for the first time, an unacceptable
regression risk for production bundles whose data predates this rule. **Staged: warning now,
error by future owner decision** — before that change reached a commit, the propagation half
(`rule.DESC-015.propagation_warning`, message text unchanged) was downgraded to `Severity.WARNING`
(matching the PROTO-004 staging precedent for `categoria`'s absence check); the domain half
(`cenario` outside `{0, 1}`, `rule.DESC-015.domain_error`) is unaffected and stays an error.
`data_ground_truth_01`'s `exit_code` is back to `0`. This is called out explicitly in
`tests/e2e/golden/CHANGELOG.md`'s PROTO-008/009/010 entry (and its same-day amendment), since
other docs (`CLAUDE.md`) point at this fixture as a "run it and see it pass" example; promoting
the propagation half back to an error is left to a future owner decision.

Last synced with code: Phase 6 round N2, 2026-09-13
