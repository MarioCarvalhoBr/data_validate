# ADR-NNNN: <Short, decisive title — the decision, not the problem>

- Status: Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN
- Date: YYYY-MM-DD
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

What is the issue we're facing, grounded in the code **as it stands today**? Cite concrete
evidence — `file:line` ranges or `Class.method` references — not a paraphrase. Name the backlog
item(s) that raised this (`.specs/quality/backlog/0X-*.md#ID`). State the forces at play (project
pillars from `CLAUDE.md` §1: elegance, tests, scalability, maintenance, security; the platform
contract that must stay green: CLI, HTML/PDF report, JSON stdout summary). Keep this factual — no
opinions yet.

## Decision

What we decided, stated as a concrete, falsifiable design: interfaces (types, method signatures),
module/file locations, names. Prefer code-shaped decisions ("`SheetSpec` is a frozen dataclass in
`data_validate/specs/sheets.py` with fields `key, required, header, csv_separator, columns`") over
prose. State which migration phase (`08-migration-roadmap.md`) implements it and what stays
byte-identical (goldens) versus what is allowed to change.

## Consequences

### Positive
- ...

### Negative
- ...

## Alternatives considered

### <Alternative 1>
Why rejected.

### <Alternative 2>
Why rejected.

## Links

- Backlog: `ID-NNN` (`.specs/quality/backlog/0X-file.md`)
- Specs: `.specs/architecture/...`, `.specs/api/...`
- Related ADRs: ADR-NNNN

---
Last synced with code: a4f76c7
