# Protocol versions and protocol ↔ code gaps

Protocol: "Especificação de Requisitos e Formatos para Entrega de Setores Estratégicos para o
AdaptaBrasil MCTI" (`assets/protocolo-v-1.13.pdf`; `assets/protocolo-1.0.pdf` is the first
version). The validator does not yet declare which protocol version it implements
(backlog DOC-006); this table records what each version changed and whether the code follows it.

## Version history (protocol §7, p.18–20)

| Version | Date | Change | Code status |
|---|---|---|---|
| 1.13 | 2025-08-05 | New `categoria` column in `descricao` | **not implemented** (G-05) |
| 1.12 | 2025-07-22 | Better description of the `legenda` column in `descricao` | n/a (documentation) |
| 1.11 | 2025-05-23 | Legends only through the optional `legenda.xlsx` (QML dropped) | implemented; `.qml` still scanned by the loader (G-04) |
| 1.10 | 2025-03-21 | Scenario `simbolo` letters/digits only; optional `dicionario.xlsx` | dictionary implemented; charset **not validated** (G-17) |
| 1.9 | 2025-03-07 | Child level > parent level; siblings share a level | COMP-008, COMP-009 |
| 1.8 | 2024-10-10 | Two decimals for values, three for proportionalities; QML naming `XX.qml` | VAL-005, PROP-008 |
| 1.7 | 2024-10-07 | `#…#` delimiter ignored by the spell-checker; legend format update | delimiter **not implemented** (G-25) |
| 1.6 | 2024-09-25 | Figure 3; `cenario` description | n/a |
| 1.5 | 2024-08-07 | Zero/NI composition ⇒ factors zero, sum zero | PROP-009 |
| 1.4 | 2024-07-31 | Optional `ordem` column | accepted as optional; **sequence not validated** (G-10) |
| 1.3 | 2024-07-16 | §4 error explanations; UTF-8 requirement; FAQ | UTF-8 check **not proactive** (G-01) |
| 1.2 | 2024-06-28 | `DI` in proportionalities | PROP-007 |
| 1.1 | 2024-06-14 | `DI` in values; version history; unique identifiers | VAL-004 |
| 1.0 | 2024-05-09 | First version, delivered with the validation tool | — |

## How to version the protocol in the tool (target)

1. `PROTOCOL_VERSION = "1.13"` constant in the sheet-spec registry; printed by `--version` and in
   the report header.
2. Each rule carries `since: <protocol version>` and, when removed, `until:`.
3. A protocol bump is an ADR + an entry here + updates to the rule files + golden re-baseline with
   reviewed diff.

## Consolidated gap list (protocol ↔ current code)

| ID | Where | Gap | Suggested action |
|---|---|---|---|
| G-01 | file-structure | UTF-8 not detected proactively; FAQ message "está no formato YYY, deveria ser UTF-8" never emitted | new rule STRUCT-013 using `chardet` |
| G-02 | file-structure | `\|` inside CSV cannot be detected after parsing | pre-parse raw scan for CSV |
| G-03 | file-structure | decimal comma mandated for CSV; code accepts `.` too | keep lenient, document |
| G-04 | file-structure | `.qml` still scanned | remove from loader config |
| G-05 | description | `categoria` (v1.13) unknown to the code | new rule DESC-013 (domain check) |
| G-06 | description | codes must be ordered by level | new rule DESC-014 |
| G-07 | description | `desc_simples` trailing `.`: code requires, protocol forbids | decide with protocol owners; adjust DESC-006 + goldens |
| G-08 | several | `LB_SCEN`, `LB_TEMP`, `LEG_OVER` titles registered but never emitted | either implement CR/LF checks for scenarios/temporal reference and map overlap to LEG-010, or drop the titles |
| G-09 | description/values | `cenario` domain {0,1} and hierarchy propagation | new rule DESC-015 |
| G-10 | description | `relacao ∈ {1,−1}`, `ordem` sibling sequence, `meta` format, `nome_completo` length | new rules DESC-016…019 |
| G-11 | description/composition | global uniqueness of names vs per-subtree | clarify; possibly a second UT variant |
| G-12 | composition | root semantics (code `0` vs node `"1"`) | unify in `SheetSpec` |
| G-13 | values | `id` completeness/uniqueness | uniqueness rule VAL-006; completeness out of scope |
| G-14 | values | [0,1] normalisation only via legend default | document |
| G-15 | temporal | four-digit symbol | new rule TEMP-004 |
| G-16 | temporal | at most one observed (past/present) time | new rule TEMP-005 |
| G-17 | scenarios | symbol charset | new rule SCEN-005 |
| G-18 | scenarios | default symbols `O`/`P` when file absent | clarify with protocol owners |
| G-19 | legend | colour must be six hex digits | tighten LEG-008 |
| G-20 | legend | empty `legenda` ⇒ default legend vs LEG-014 error | clarify with protocol owners |
| G-21 | legend | grey for DI; max 11 slices | optional warnings |
| G-22 | legend | legend must cover data min/max | equivalent to LEG-015; document |
| G-23 | proportionality | blank cells treated as valid | align with protocol (error) |
| G-24 | proportionality | first two spatial columns vs single `id` | clarify |
| G-25 | spelling | `#…#` ignore delimiter | implement in `TextProcessor` |
| G-26 | spelling | not all textual columns are checked | extend `model_columns_map` |
| G-27 | spelling | case-sensitive dictionary matching unverified | add tests |
| — | spelling | dictionary initialisation errors silently dropped (`_prepare_statement` never called) | bug fix + test |

Last synced with code: 3dcfdb1
