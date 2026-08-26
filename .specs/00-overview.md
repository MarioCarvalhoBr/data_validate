# 00 · Overview

## What

**Data Validate** (PyPI: `canoa_data_validate`, CLI: `canoa-data-validate`, codename *Canoa*) is
the spreadsheet validator of the **AdaptaBrasil** platform, developed by INPE (Instituto Nacional
de Pesquisas Espaciais). Sector teams (health, biodiversity, water, …) deliver a bundle of
spreadsheets describing climate-adaptation indicators; the validator checks the bundle against the
*Protocolo v1.13* and produces an HTML/PDF report plus a machine-readable summary that the
platform's ingestion pipeline consumes.

## Scope

In scope:
- Structural validation of the input folder and of each sheet (files present, columns, headers).
- Content and cross-sheet business rules (hierarchy, levels, codes, value patterns, legends,
  proportionality sums, temporal references, scenarios).
- Spell-check of descriptive text (pt-BR, en-US) with a per-bundle dictionary.
- Report generation (HTML always; PDF optional) and a JSON summary on stdout.
- Batch usage over many bundles (CI, platform server) and library usage (target).

Out of scope:
- Fixing or transforming data (the tool only reports).
- Storing data or talking to the platform's database.
- Web UI (see `future/ideas.md`).

## Stakeholders

| Actor | Needs |
|---|---|
| Sector data teams | Clear, localised, line-accurate messages to fix their sheets |
| AdaptaBrasil platform (Canoa ingestion) | Stable CLI, exit codes, JSON summary, HTML report path |
| INPE maintainers | Elegant, tested, secure code; rules traceable to the protocol |
| Researchers reusing the tool | Library API, documented rule set, permissive licence (MIT) |

## Input bundle

| Sheet (stem) | Required | Header | Purpose |
|---|---|---|---|
| `descricao` | yes | single | Indicator metadata: code, level, names, descriptions, sources, unit, scenario/legend links |
| `composicao` | yes | single | Parent → child edges of the indicator tree |
| `valores` | yes | single | One row per territory `id`; columns `CODE-YEAR[-SCENARIO]` |
| `referencia_temporal` | yes | single | Years (symbols) used in value columns |
| `proporcionalidades` | no | double | Influence weights of children on parents (`id` + `parent`/`child` MultiIndex) |
| `cenarios` | no | single | Scenario symbols (e.g. `O`, `P`) |
| `legenda` | no | single | Legend classes: code, label, colour, min, max, order |
| `dicionario` | no | single | Words to accept in spell-check |

Extensions `.csv` (separator `|`) or `.xlsx`; the same stem must not exist in both formats.

## Glossary

| Term | Meaning |
|---|---|
| Indicator | A node of the hierarchy identified by an integer `codigo`; level 1 is the sector root's children, deeper levels are compositions |
| Level (`nivel`) | Depth of the indicator in the tree; parents must have a lower level than children |
| Scenario (`cenario`) | Climate scenario symbol; value columns for future years carry the scenario suffix |
| Temporal reference | List of years; the first is the base year without scenario |
| `DI` | "Dado indisponível" — sentinel for unavailable values |
| Legend | Set of ranges (`minimo`–`maximo`) with labels/colours used to classify indicator values |
| Proportionality | Weights of children indicators that must sum to 1 per parent and territory |
| Golden | Frozen expected output of a fixture bundle used to detect regressions |
| Rule ID | Stable identifier of one business rule (`DESC-004`) |
| Protocol | The formal specification (`assets/protocolo-v-1.13.pdf`) |

## Current state (v0.7.65b732)

- Python 3.12, Poetry, pandas 3, networkx, pyenchant, jinja2, babel, calamine, pdfkit.
- 878 unit tests (all under `tests/unit/helpers/`), 54.99 % line coverage (measured with the current configuration; 55.97 % with legacy exclusions).
- 34 verification categories (`config/names_enum.py`), messages hard-coded in pt-BR.
- Known debt: `quality/backlog/` (90 items). Migration plan: `quality/backlog/08-migration-roadmap.md`.

## Where next

- How it works today → `architecture/current-architecture.md`
- Where it is going → `architecture/target-architecture.md`
- What must be true → `business-rules/`
- What to do next → `quality/backlog/README.md`

Last synced with code: 09279f4
