# Error model

## Today

- Every finding is a `str` created where it is detected (validators, models, helpers, readers).
- `ValidationReport` (`controllers/report/validation_report.py`) keeps
  `dict[title, ReportItem(errors: list[str], warnings: list[str], was_executed: bool)]` in
  `NamesEnum` order, pre-populated by `SpreadsheetProcessor._prepare_statement`. `ReportItem` is
  the BUG-020 rename of the former `TestReportItem` (a deprecated `TestReportItem = ReportItem`
  alias remains for one release, with `__test__ = False` so pytest never collects either name).
- `flatten(n_messages=20, locale)` copies the first 20 errors/warnings of each bucket and appends
  `model_report_msg_errors_omitted` / `model_report_msg_warnings_omitted` with the omitted count
  formatted by `babel` (`format_number_brazilian`). If truncation is actually needed and
  `ValidationReport.context` is `None`, `flatten` raises `ValueError` instead of dereferencing
  `None.language_manager` (BUG-005); a report with no truncation needed still works with no
  context.
- `FileReportGenerator` counts totals **before** flattening, renders the flattened lists, and
  prints `<{"data_validate": {"version": v, "report": {"errors": E, "warnings": W, "tests": T}}}>`
  (built with `json.dumps(summary, ensure_ascii=False)`, valid JSON even if a value contains a
  quote or non-ASCII character — BUG-010) where `T = len(report_list)` (number of buckets,
  currently 35 regardless of execution).
- `was_executed` is never set to `False` (the `set_not_executed` placeholder is a no-op), so
  "skipped tests" in the report only reflect `--no-spellchecker` and `--no-warning-titles-length`.

## Target

### `Issue`

| Field | Type | Meaning |
|---|---|---|
| `rule_id` | `str` | Stable rule identifier (`DESC-004`) — also the link to `business-rules/` |
| `severity` | `Severity` (`error`, `warning`) | Maps 1:1 to today's error/warning lists |
| `sheet` | `str \| None` | File name as delivered (`descricao.xlsx`); `None` for folder-level issues |
| `row` | `int \| None` | Spreadsheet row (1-based, header-aware) or `None` for sheet-level issues |
| `column` | `str \| None` | Column name (for double header: `"parent/child"`) |
| `message_key` | `str` | Catalog key (`rule.DESC-004.error`) |
| `params` | `Mapping[str, object]` | Named placeholders for the message (`{"value": "Abc.", "expected": "Abc"}`) |

Rules never build text. Text is produced by `MessageCatalog.render(issue, locale)`.

### `RuleOutcome`

`rule_id`, `status` (`executed` | `skipped`), `reason` (catalog key when skipped, e.g.
`engine.skipped.missing_sheet`, `engine.skipped.missing_column`, `engine.skipped.dependency_failed`,
`engine.skipped.disabled_by_option`), `issues`, `duration_ms`.

### `ValidationResult`

```python
@dataclass(frozen=True)
class ValidationResult:
    outcomes: tuple[RuleOutcome, ...]
    load_issues: tuple[Issue, ...]        # STRUCT-* from loading/normalising
    started_at: datetime
    duration_ms: float
    @property
    def errors(self) -> int: ...
    @property
    def warnings(self) -> int: ...
    @property
    def has_errors(self) -> bool: ...
```

### Report model (grouping, ordering, truncation)

1. Group issues by **category** (`Rule.category`, values = today's `NamesEnum` titles, same
   order) so the HTML layout is unchanged.
2. Inside a category: errors first, then warnings; each sorted by (`sheet`, `row`, `column`,
   `rule_id`) — deterministic, replaces today's insertion order (goldens are re-baselined once in
   Phase 4 with a reviewed diff).
3. Truncate each list to `limits.report_max_messages` (default 20) and append one synthetic
   entry with key `report.omitted.errors` / `report.omitted.warnings` and `{"count": n}`.
4. Totals are computed on the untruncated result.
5. Skipped rules are listed with their reason (today: only two flags).

### JSON shape (`--json PATH`, also the stdout summary)

```json
{
  "data_validate": {
    "version": "0.8.0",
    "protocol": "1.13",
    "locale": "pt_BR",
    "report": { "errors": 12, "warnings": 4, "tests": 35, "skipped": 2 },
    "categories": [
      {
        "key": "verification_name_sequential_codes",
        "title": "Códigos sequenciais",
        "errors": [ { "rule_id": "DESC-002", "sheet": "descricao.xlsx", "row": null, "column": "codigo",
                      "message": "descricao.xlsx: A coluna 'codigo' deve começar em 1." } ],
        "warnings": []
      }
    ],
    "skipped": [ { "rule_id": "SPELL-001", "reason": "engine.skipped.disabled_by_option" } ]
  }
}
```

The top-level `data_validate.version` and `report.{errors,warnings,tests}` keys are kept for
backward compatibility with the platform parser; new keys are additive.

### Severity policy

| Severity | Consequence | Examples |
|---|---|---|
| `error` | Bundle rejected; exit code 1 | missing required file, non-sequential codes, cycle, sum ≠ 1 |
| `warning` | Bundle accepted; shown to the team | title longer than 40 chars, capitalisation, unused legend code |

Which severity each rule uses is fixed in `business-rules/` and must not be decided ad hoc in code.

## Implementation status

ARC-004 (model only, Phase 1 step 2): `data_validate/specs/issues.py` implements `Severity` and
`Issue` as sketched above (`Issue` additionally validates `rule_id` against the stable rule-ID
pattern and carries a `category: str | None` field for the Phase 1-2 legacy-`NamesEnum` adapter,
not yet present in the sketch), plus a simplified `ValidationResult` — `issues: tuple[Issue, ...]`
with `errors`/`warnings`/`error_count`/`warning_count`, `by_category()`, `truncated(limit)` and
`omitted_counts(limit)` — rather than the `outcomes`/`load_issues`/`started_at`/`duration_ms` shape
sketched above, which belongs to `RuleOutcome`/the engine (ADR-0006) and lands with Phase 3.
`data_validate/i18n/catalog.py` implements `MessageCatalog.text`/`render` and
`default_catalog_dir()`. Nothing here is wired into the legacy pipeline yet: no validator, model,
or `ValidationReport` call site was changed. The full `ValidationResult` (`outcomes`/`load_issues`/
`started_at`/`duration_ms`) and the report-model grouping/truncation/JSON rendering steps remain
open (Phase 3-4).

ARC-017/ADR-0006 (engine core, Phase 3a): `data_validate/rules/engine.py` implements `RuleOutcome`
close to, but refined from, the sketch above: `status` is a 4-value `RuleStatus` StrEnum
(`PASSED`, `ISSUES`, `SKIPPED`, `FAILED`) rather than the sketch's `Literal["executed", "skipped"]`
— splitting "executed" into whether the rule actually found anything, and adding `FAILED` for a
rule that raised (never silently absorbed as a clean run, closing SEC-004 at the engine level); the
"reason" field is named `skip_reason` and, for `FAILED`, holds `repr(exception)` rather than a
catalog key (there is no separate error field in this slice). `SkipReason` provides the
`engine.skipped.missing_sheet`/`missing_column`/`dependency_skipped`/`dependency_failed` keys
named informally above. `EngineResult.validation_result` flattens every outcome's issues into the
existing `specs/issues.py::ValidationResult`, not yet the richer `outcomes`/`load_issues`/
`started_at`/`duration_ms` shape sketched above — that composition is Phase 3b's job once a rule
module exists to actually populate `RuleContext.sheets` from a loaded bundle. 100 % covered by
`tests/unit/rules/`.

PROTO-013 (Phase 6 round N3): `SkipReason.DISABLED_BY_OPTION` (`engine.skipped.disabled_by_option`)
is now implemented — its first consumer is `rules/territories.py`'s TERR-001/TERR-002, gated by a
new `RuleSpec.requires_options: tuple[str, ...]` field (`ctx.options` keys that must all be
truthy; checked by `Engine._unmet_prerequisite` after `requires`, before `depends_on`). This is the
only sketched `SkipReason` key that was still unimplemented; all four now exist.

Last synced with code: Phase 6 round N3, 2026-09-13 (PROTO-013: `RuleSpec.requires_options` /
`SkipReason.DISABLED_BY_OPTION` implemented)
