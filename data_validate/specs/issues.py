#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Structured validation findings: `Issue`, `Severity`, `ValidationResult` (ARC-004, ADR-0004).

Replaces the pre-formatted Portuguese strings produced today by every validator
(`f"{self._filename}, linha {idx + 2}: ..."`) with a stable, queryable value object: a rule ID,
a severity, an optional location (sheet/row/column), a catalog key, and named parameters. Rules
never build text themselves — `data_validate.i18n.catalog.MessageCatalog.render(issue)` does that
translation step (see `.specs/architecture/error-model.md`).

This module is model-only (Phase 1 step 2 of `08-migration-roadmap.md`): nothing here is wired
into the legacy pipeline yet. It depends only on the standard library, per
`.claude/rules/architecture-boundaries.md` (`specs` depends on nothing else in the package).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

_RULE_ID_PATTERN = re.compile(r"^(STRUCT|DESC|COMP|VAL|TEMP|SCEN|LEG|PROP|SPELL|CLEAN)-\d{3}$")


class Severity(StrEnum):
    """Severity of a validation finding.

    `ERROR` means the bundle is rejected (non-zero exit code); `WARNING` means the bundle is
    accepted but the finding is shown to the sector team. See `.specs/architecture/error-model.md`
    ("Severity policy") for which rules use which severity.
    """

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Issue:
    """One structured validation finding.

    Attributes:
        rule_id: Stable rule identifier (`"DESC-004"`), also the link to `.specs/business-rules/`.
            Must match `^(STRUCT|DESC|COMP|VAL|TEMP|SCEN|LEG|PROP|SPELL|CLEAN)-\\d{3}$`.
        severity: Whether this finding is an error or a warning.
        sheet: File name as delivered (`"descricao.xlsx"`), or `None` for a folder-level issue.
        row: Spreadsheet row (0-based data index, i.e. the position in the sheet's data rows,
            excluding header rows), or `None` for a sheet-level issue.
        column: Column name (`"parent/child"` for a double-header sheet), or `None`.
        message_key: Catalog key resolved by `MessageCatalog.render` (`"rule.DESC-004.error"`).
        params: Named placeholders for the message (e.g. `{"value": "Abc.", "expected": "Abc"}`).
            Stored as a read-only `MappingProxyType` regardless of what was passed in.
        category: The legacy `NamesEnum` verification key this issue reports under, used only by
            the Phase 1-2 adapter that renders `Issue`s into today's report buckets. `None` once a
            rule has no legacy category to map to.

    Raises:
        ValueError: If `rule_id` does not match the stable rule-ID pattern.
    """

    rule_id: str
    severity: Severity
    sheet: str | None
    row: int | None
    column: str | None
    message_key: str
    params: Mapping[str, object]
    category: str | None = None

    def __post_init__(self) -> None:
        """Validate `rule_id` and freeze `params` into a read-only mapping."""
        if not _RULE_ID_PATTERN.match(self.rule_id):
            raise ValueError(
                f"Issue.rule_id {self.rule_id!r} does not match "
                f"'^(STRUCT|DESC|COMP|VAL|TEMP|SCEN|LEG|PROP|SPELL|CLEAN)-\\d{{3}}$'"
            )
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))


@dataclass(frozen=True)
class ValidationResult:
    """An immutable collection of `Issue`s, grouped and truncated for reporting.

    Attributes:
        issues: Every issue found during a validation run, in the order rules produced them.
    """

    issues: tuple[Issue, ...] = field(default_factory=tuple)

    @property
    def errors(self) -> tuple[Issue, ...]:
        """Every issue with `severity is Severity.ERROR`, in original order."""
        return tuple(issue for issue in self.issues if issue.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[Issue, ...]:
        """Every issue with `severity is Severity.WARNING`, in original order."""
        return tuple(issue for issue in self.issues if issue.severity is Severity.WARNING)

    @property
    def error_count(self) -> int:
        """Total number of error-severity issues."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Total number of warning-severity issues."""
        return len(self.warnings)

    def by_category(self) -> dict[str, list[Issue]]:
        """Group issues by `Issue.category`, in first-seen category order.

        `Issue.category is None` is grouped under the empty string `""` so the return type stays
        `dict[str, list[Issue]]` (a category-less issue has no legacy report bucket to sort into
        yet — see `Issue.category`'s docstring).

        Returns:
            dict[str, list[Issue]]: Category key -> issues in that category, insertion order
                preserved both across categories and within each category's list.
        """
        groups: dict[str, list[Issue]] = {}
        for issue in self.issues:
            key = issue.category if issue.category is not None else ""
            groups.setdefault(key, []).append(issue)
        return groups

    def truncated(self, limit: int) -> ValidationResult:
        """Truncate errors and warnings to `limit` entries, per category, independently.

        Mirrors today's `ValidationReport.flatten` semantics
        (`controllers/report/validation_report.py`): the first `limit` errors and the first
        `limit` warnings of each category are kept, in their original order; this method does
        **not** append an omitted-count entry itself — that synthetic message is the renderer's
        job (see `omitted_counts`).

        Args:
            limit: Maximum number of errors, and separately of warnings, kept per category.

        Returns:
            ValidationResult: A new result with the truncated issue list.
        """
        kept: list[Issue] = []
        for category_issues in self.by_category().values():
            errors = [issue for issue in category_issues if issue.severity is Severity.ERROR][:limit]
            warnings = [issue for issue in category_issues if issue.severity is Severity.WARNING][:limit]
            kept.extend(errors)
            kept.extend(warnings)
        return ValidationResult(issues=tuple(kept))

    def omitted_counts(self, limit: int) -> dict[tuple[str, Severity], int]:
        """Count how many issues `truncated(limit)` would drop, per category and severity.

        Args:
            limit: Same truncation limit that would be passed to `truncated`.

        Returns:
            dict[tuple[str, Severity], int]: `(category, severity) -> omitted count`, only for
                combinations that actually exceed `limit`.
        """
        counts: dict[tuple[str, Severity], int] = {}
        for category, category_issues in self.by_category().items():
            for severity in (Severity.ERROR, Severity.WARNING):
                total = sum(1 for issue in category_issues if issue.severity is severity)
                omitted = total - limit
                if omitted > 0:
                    counts[(category, severity)] = omitted
        return counts
