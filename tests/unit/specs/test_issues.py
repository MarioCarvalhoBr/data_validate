#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for the structured `Issue`/`ValidationResult` model (ARC-004, ADR-0004).

Covers `Issue` validation and immutability, and `ValidationResult`'s filtering, grouping,
truncation, and omitted-count semantics against hand-built fixtures (`.claude/rules/testing.md`).
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from data_validate.specs.issues import Issue, Severity, ValidationResult


def _make_issue(
    *,
    rule_id: str = "DESC-004",
    severity: Severity = Severity.ERROR,
    sheet: str | None = "descricao.xlsx",
    row: int | None = 3,
    column: str | None = "codigo",
    message_key: str = "rule.DESC-004.error",
    params: dict[str, object] | None = None,
    category: str | None = "indicator_name_pattern",
) -> Issue:
    """Build an `Issue` with sensible defaults, overridable per test."""
    return Issue(
        rule_id=rule_id,
        severity=severity,
        sheet=sheet,
        row=row,
        column=column,
        message_key=message_key,
        params=params if params is not None else {},
        category=category,
    )


class TestIssueValidation:
    """`Issue.rule_id` must match the stable rule-ID pattern."""

    @pytest.mark.parametrize(
        "rule_id",
        [
            "STRUCT-001",
            "DESC-004",
            "COMP-009",
            "VAL-005",
            "TEMP-003",
            "SCEN-004",
            "LEG-015",
            "PROP-010",
            "SPELL-001",
            "CLEAN-006",
        ],
    )
    def test_accepts_every_registered_prefix(self, rule_id: str) -> None:
        issue = _make_issue(rule_id=rule_id)

        assert issue.rule_id == rule_id

    @pytest.mark.parametrize(
        "bad_rule_id",
        [
            "",
            "DESC",
            "DESC-4",
            "DESC-0004",
            "desc-004",
            "UNKNOWN-001",
            "DESC-004-extra",
            "DESC_004",
        ],
    )
    def test_rejects_malformed_rule_id(self, bad_rule_id: str) -> None:
        with pytest.raises(ValueError, match="rule_id"):
            _make_issue(rule_id=bad_rule_id)


class TestIssueImmutability:
    """`Issue` is a frozen dataclass with a read-only `params` mapping."""

    def test_issue_is_frozen(self) -> None:
        issue = _make_issue()

        with pytest.raises(dataclasses.FrozenInstanceError):
            issue.rule_id = "DESC-005"  # type: ignore[misc]

    def test_params_becomes_a_read_only_mapping(self) -> None:
        issue = _make_issue(params={"value": "Abc."})

        assert isinstance(issue.params, MappingProxyType)
        assert issue.params["value"] == "Abc."
        with pytest.raises(TypeError):
            issue.params["value"] = "Xyz."  # type: ignore[index]

    def test_params_is_decoupled_from_the_original_dict(self) -> None:
        original = {"value": "Abc."}
        issue = _make_issue(params=original)
        original["value"] = "Mutated."

        assert issue.params["value"] == "Abc."

    def test_category_defaults_to_none(self) -> None:
        issue = Issue(
            rule_id="DESC-004",
            severity=Severity.ERROR,
            sheet=None,
            row=None,
            column=None,
            message_key="rule.DESC-004.error",
            params={},
        )

        assert issue.category is None


class TestValidationResultFiltering:
    """`errors`/`warnings`/`error_count`/`warning_count` filter by severity."""

    def test_errors_and_warnings_are_partitioned_by_severity(self) -> None:
        error_issue = _make_issue(severity=Severity.ERROR)
        warning_issue = _make_issue(rule_id="DESC-006", severity=Severity.WARNING)
        result = ValidationResult(issues=(error_issue, warning_issue))

        assert result.errors == (error_issue,)
        assert result.warnings == (warning_issue,)
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_empty_result_has_no_errors_or_warnings(self) -> None:
        result = ValidationResult(issues=())

        assert result.errors == ()
        assert result.warnings == ()
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_validation_result_defaults_to_no_issues(self) -> None:
        result = ValidationResult()

        assert result.issues == ()


class TestValidationResultGrouping:
    """`by_category` groups in first-seen category order, category-less issues under ""."""

    def test_groups_preserve_first_seen_category_order(self) -> None:
        first = _make_issue(rule_id="DESC-004", category="indicator_name_pattern")
        second = _make_issue(rule_id="COMP-007", category="tree_hierarchy")
        third = _make_issue(rule_id="DESC-006", category="indicator_name_pattern")
        result = ValidationResult(issues=(first, second, third))

        groups = result.by_category()

        assert list(groups) == ["indicator_name_pattern", "tree_hierarchy"]
        assert groups["indicator_name_pattern"] == [first, third]
        assert groups["tree_hierarchy"] == [second]

    def test_category_less_issues_are_grouped_under_empty_string(self) -> None:
        issue = _make_issue(category=None)
        result = ValidationResult(issues=(issue,))

        assert result.by_category() == {"": [issue]}


class TestValidationResultTruncation:
    """`truncated` mirrors `ValidationReport.flatten`'s per-category, per-severity limit."""

    def test_truncates_errors_and_warnings_independently_per_category(self) -> None:
        errors = [_make_issue(rule_id="DESC-004", severity=Severity.ERROR) for _ in range(3)]
        warnings = [_make_issue(rule_id="DESC-006", severity=Severity.WARNING) for _ in range(2)]
        result = ValidationResult(issues=tuple(errors + warnings))

        truncated = result.truncated(limit=1)

        assert truncated.errors == (errors[0],)
        assert truncated.warnings == (warnings[0],)

    def test_truncation_keeps_original_order(self) -> None:
        first, second, third = (_make_issue(row=row) for row in (1, 2, 3))
        result = ValidationResult(issues=(first, second, third))

        truncated = result.truncated(limit=2)

        assert truncated.errors == (first, second)

    def test_truncation_does_not_add_an_omitted_entry(self) -> None:
        issues = tuple(_make_issue(row=row) for row in range(5))
        result = ValidationResult(issues=issues)

        truncated = result.truncated(limit=2)

        assert len(truncated.issues) == 2

    def test_truncation_is_a_no_op_when_under_the_limit(self) -> None:
        issues = tuple(_make_issue(row=row) for row in range(2))
        result = ValidationResult(issues=issues)

        truncated = result.truncated(limit=20)

        assert truncated.issues == issues

    def test_truncation_is_independent_across_categories(self) -> None:
        category_a = [_make_issue(rule_id="DESC-004", category="a") for _ in range(3)]
        category_b = [_make_issue(rule_id="DESC-006", category="b") for _ in range(3)]
        result = ValidationResult(issues=tuple(category_a + category_b))

        truncated = result.truncated(limit=2)

        assert len(truncated.by_category()["a"]) == 2
        assert len(truncated.by_category()["b"]) == 2


class TestValidationResultOmittedCounts:
    """`omitted_counts` reports what `truncated` would drop, without dropping it."""

    def test_no_omissions_when_under_the_limit(self) -> None:
        issues = tuple(_make_issue(row=row) for row in range(2))
        result = ValidationResult(issues=issues)

        assert result.omitted_counts(limit=20) == {}

    def test_reports_omitted_count_per_category_and_severity(self) -> None:
        errors = [_make_issue(rule_id="DESC-004", severity=Severity.ERROR, category="a") for _ in range(5)]
        warnings = [_make_issue(rule_id="DESC-006", severity=Severity.WARNING, category="a") for _ in range(1)]
        result = ValidationResult(issues=tuple(errors + warnings))

        assert result.omitted_counts(limit=2) == {("a", Severity.ERROR): 3}

    def test_does_not_mutate_the_result(self) -> None:
        issues = tuple(_make_issue(row=row) for row in range(5))
        result = ValidationResult(issues=issues)

        result.omitted_counts(limit=2)

        assert result.issues == issues
