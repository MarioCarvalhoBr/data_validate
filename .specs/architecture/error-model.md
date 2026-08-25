# Error model

## Today

- Every finding is a `str` created where it is detected (validators, models, helpers, readers).
- `ValidationReport` (`controllers/report/validation_report.py`) keeps
  `dict[title, TestReportItem(errors: list[str], warnings: list[str], was_executed: bool)]` in
  `NamesEnum` order, pre-populated by `SpreadsheetProcessor._prepare_statement`.
- `flatten(n_messages=20, locale)` copies the first 20 errors/warnings of each bucket and appends
  `model_report_msg_errors_omitted` / `model_report_msg_warnings_omitted` with the omitted count
  formatted by `babel` (`format_number_brazilian`).
- `FileReportGenerator` counts totals **before** flattening, renders the flattened lists, and
  prints `<{"data_validate": {"version": v, "report": {"errors": E, "warnings": W, "tests": T}}}>`
  where `T = len(report_list)` (number of buckets, currently 35 regardless of execution).
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

Last synced with code: 3dcfdb1
