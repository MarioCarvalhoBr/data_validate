# ADR-0004: Structured `Issue` model and message catalog replace pre-formatted strings

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

Every validator today produces plain Python strings, already formatted in Portuguese, as its unit
of error/warning: the pervasive pattern is `f"{self._filename}, linha {idx + 2}: ..."` scattered
across `validators/**`, `models/sp_*.py` and `helpers/common/**`. `BaseValidator.build_reports`
(`validators/spreadsheets/base/base_validator.py:262-295`) accepts a list of
`(Callable, report_key)` pairs, each function returning `Tuple[List[str], List[str]]`
(errors, warnings), and simply extends those string lists into `self._report_list` — there is no
rule ID, severity enum, sheet/row/column location or parameter metadata attached to a message
anywhere in the pipeline (ARC-004). `ValidationReport` (`controllers/report/validation_report.py`)
stores these as `List[str]` too; `flatten` dereferences `self.context.language_manager`
unconditionally even though `context` is typed `Optional` (BUG-005, lines 92, 208, 213), because
there is no `Issue`/`translate` seam to inject a fallback. Because messages are pre-rendered
strings, they cannot be: sorted or deduplicated by rule, exported as structured JSON for the
platform, counted per column, correlated back to a protocol section, or translated after the fact
— which is also why 95 % of messages are hard-coded Portuguese today (ARC-005) instead of catalog
lookups. `build_reports`'s `except Exception as e:` (line 290) also converts *any* crash inside a
validation function into a user-facing string
(`f"Exception validation in file during {func.__name__}: {str(e)}"`, line 293) — SEC-004's
"programming errors become user-facing strings and the process exits 0" is a direct consequence of
having no distinct crash/issue representation.

## Decision

Adopt the `Issue` model and `MessageCatalog` seam defined in
`.specs/architecture/target-architecture.md`: a frozen `Issue(rule_id: str, severity: Severity,
sheet: str | None, row: int | None, column: str | None, message_key: str, params:
Mapping[str, object])`, where `Severity` is a `StrEnum` of `ERROR`/`WARNING`, and a
`ValidationResult` that groups `Issue`s by rule/category for rendering. Rules
(`rules/<sheet>/<RULE-ID>.py`, ADR-0006) return `Iterable[Issue]` instead of formatted strings; a
`MessageCatalog.render(issue, locale) -> str` looks up `message_key` in
`static/locales/<locale>/messages.json` (i18n keyed by rule ID, ADR-0014) and interpolates `params`.
For Phase 1 (`08-migration-roadmap.md`), an adapter renders `Issue`s to **the same strings produced
today**, so the golden harness (ADR-0002) stays green while the representation changes underneath;
only in Phase 3-4 do rendered strings change as messages move fully into the catalog. Renderers
(console/JSON/HTML/PDF, ADR-0007) consume `ValidationResult` directly instead of pre-formatted HTML
fragments, giving the platform's `--json` output real structure (rule_id, severity, location) for
the first time, addressing BUG-010's `str(dict).replace("'", '"')` invalid-JSON problem alongside
it. Unexpected exceptions inside a rule become a distinct `engine.rule_crashed` issue and exit code
2 (see ADR-0006) — never silently absorbed into the same list as a business-rule error.

## Consequences

### Positive
- Errors and warnings become queryable data: sortable, deduplicable, exportable as valid JSON,
  countable per rule/column, and traceable to the protocol section that motivated the rule.
- Programming errors (crashes) are now structurally distinct from validation findings, closing the
  SEC-004 gap where a bug could be reported to the platform as "the spreadsheet is valid".
- Translating a message, adding a new locale, or changing wording no longer requires touching
  validator code — it's a catalog edit (supports ADR-0014's i18n completion).

### Negative
- Every existing validator function must be rewritten to return `Issue`s instead of strings — a
  large, mechanical but error-prone change, mitigated by porting one sheet at a time (Phase 3) with
  a unit test and golden case per rule.
- The Phase 1 "render identical strings" adapter is throwaway work, kept only long enough to
  decouple the representation change from the wording change; it must be deleted once Phase 3-4
  moves messages fully into the catalog, or it becomes permanent debt.

## Alternatives considered

### Keep strings, but prefix each with a rule ID by convention (e.g. `"DESC-004: linha 3: ..."`)
Rejected: still unparseable without fragile string splitting, still carries no `params` for JSON
export or safe HTML escaping (the exact gap SEC-001 exploits by concatenating raw cell content into
HTML strings), and still can't be translated without re-deriving structure from prose after the
fact.

### Represent failures as exceptions/error codes propagated up the call stack
Rejected: this project's own coding standard (`.github/copilot-instructions.md` §6, "Clean Error
Handling — use exceptions, not error codes") argues against error-code tuples for *control flow*,
but a validation run legitimately produces *many* findings per rule, not a single pass/fail — an
`Issue` value collected in a list is the right shape for "here are the findings", while exceptions
remain reserved for genuine crashes (which is exactly how ADR-0006 separates `RuleOutcome.status ==
"skipped"`/issues from unexpected exceptions).

### Adopt a third-party structured-logging schema (e.g. OpenTelemetry log records) for issues
Rejected: `data_validate` is a batch CLI, not a service emitting telemetry to a collector; pulling
in an OTel dependency and its schema for what is fundamentally "list of (rule, location, message)"
records adds a runtime dependency and conceptual overhead the project doesn't need — `Issue` is a
plain dataclass with no external dependency.

## Links

- Backlog: `ARC-004`, `ARC-005` (`03-architecture.md`); `BUG-005`, `BUG-010` (`01-bugs.md`);
  `SEC-004` (`02-security.md`); `08-migration-roadmap.md` Phase 1 item 2
- Specs: `.specs/architecture/target-architecture.md` (`Issue`, `Severity`, `RuleOutcome`),
  `.specs/architecture/error-model.md`
- Related ADRs: ADR-0002, ADR-0006, ADR-0007, ADR-0014

---
Last synced with code: a4f76c7
