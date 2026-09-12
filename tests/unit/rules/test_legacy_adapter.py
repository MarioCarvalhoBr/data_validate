#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.legacy_adapter.extend_report_from_outcomes` (ARC-017 Phase 3b).

Covers rendering ISSUES outcomes into the right `ValidationReport` bucket by severity, skipping
outcomes with no issues (`PASSED`/`SKIPPED`/`FAILED`), preserving order across outcomes, and the
`category is None` guard (`.claude/rules/testing.md`: table-driven, no mocks needed here since
`ValidationReport` is a real, lightweight in-memory object).
"""

from __future__ import annotations

from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.rules.engine import RuleOutcome, RuleStatus
from data_validate.rules.legacy_adapter import extend_report_from_outcomes
from data_validate.specs.issues import Issue, Severity

_TITLES = {
    "verification_name_file_structure": "Estrutura dos arquivos da pasta de entrada",
    "verification_name_file_cleaning": "Limpeza dos arquivos",
}


def _make_issue(
    rule_id: str,
    *,
    severity: Severity = Severity.ERROR,
    category: str | None = "verification_name_file_structure",
    message_key: str = "validator_structure_error_unexpected_file",
    params: dict[str, object] | None = None,
) -> Issue:
    return Issue(
        rule_id=rule_id,
        severity=severity,
        sheet=None,
        row=None,
        column=None,
        message_key=message_key,
        params=params if params is not None else {"file_name": "arquivo.txt"},
        category=category,
    )


def _make_outcome(rule_id: str, issues: tuple[Issue, ...] = ()) -> RuleOutcome:
    status = RuleStatus.ISSUES if issues else RuleStatus.PASSED
    return RuleOutcome(rule_id=rule_id, status=status, issues=issues, skip_reason=None, duration_ms=0.0)


class TestExtendReportFromOutcomesRendering:
    """An ISSUES outcome's issues are rendered and appended to the right bucket."""

    def test_an_error_issue_is_rendered_and_appended_as_an_error(self) -> None:
        issue = _make_issue("STRUCT-004", params={"file_name": "arquivo.txt"})
        outcome = _make_outcome("STRUCT-004", (issue,))
        report = ValidationReport()

        extend_report_from_outcomes(
            [outcome],
            translate=lambda key, **params: f"{key}:{params}",
            report=report,
            titles=_TITLES,
        )

        bucket = report[_TITLES["verification_name_file_structure"]]
        assert bucket.errors == ["validator_structure_error_unexpected_file:{'file_name': 'arquivo.txt'}"]
        assert bucket.warnings == []

    def test_a_warning_issue_is_rendered_and_appended_as_a_warning(self) -> None:
        issue = _make_issue("STRUCT-012", severity=Severity.WARNING, message_key="rule.STRUCT-012.warning", params={})
        outcome = _make_outcome("STRUCT-012", (issue,))
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=lambda key, **params: key, report=report, titles=_TITLES)

        bucket = report[_TITLES["verification_name_file_structure"]]
        assert bucket.errors == []
        assert bucket.warnings == ["rule.STRUCT-012.warning"]

    def test_translate_receives_the_message_key_and_params(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def translate(key: str, **params: object) -> str:
            calls.append((key, params))
            return "rendered"

        issue = _make_issue(
            "STRUCT-005", message_key="validator_structure_error_missing_file", params={"file_base": "valores"}
        )
        outcome = _make_outcome("STRUCT-005", (issue,))
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=translate, report=report, titles=_TITLES)

        assert calls == [("validator_structure_error_missing_file", {"file_base": "valores"})]


class TestExtendReportFromOutcomesNonIssuesOutcomes:
    """PASSED/SKIPPED/FAILED outcomes contribute nothing."""

    def test_a_passed_outcome_appends_nothing(self) -> None:
        outcome = _make_outcome("STRUCT-001")
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=lambda key, **params: key, report=report, titles=_TITLES)

        assert list(report) == []

    def test_a_skipped_outcome_appends_nothing(self) -> None:
        outcome = RuleOutcome(
            rule_id="LEG-012",
            status=RuleStatus.SKIPPED,
            issues=(),
            skip_reason="engine.skipped.missing_sheet",
            duration_ms=0.0,
        )
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=lambda key, **params: key, report=report, titles=_TITLES)

        assert list(report) == []

    def test_a_failed_outcome_appends_nothing(self) -> None:
        outcome = RuleOutcome(
            rule_id="LEG-012",
            status=RuleStatus.FAILED,
            issues=(),
            skip_reason=repr(ValueError("boom")),
            duration_ms=0.0,
        )
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=lambda key, **params: key, report=report, titles=_TITLES)

        assert list(report) == []


class TestExtendReportFromOutcomesOrderingAndCategory:
    """Issues are appended in outcome order; a `category is None` issue is skipped."""

    def test_issues_from_multiple_outcomes_are_appended_in_order(self) -> None:
        first = _make_issue(
            "STRUCT-001", message_key="validator_structure_error_empty_directory", params={"dir_path": "/x"}
        )
        second = _make_issue(
            "STRUCT-005", message_key="validator_structure_error_missing_file", params={"file_base": "valores"}
        )
        report = ValidationReport()

        extend_report_from_outcomes(
            [_make_outcome("STRUCT-001", (first,)), _make_outcome("STRUCT-005", (second,))],
            translate=lambda key, **params: key,
            report=report,
            titles=_TITLES,
        )

        bucket = report[_TITLES["verification_name_file_structure"]]
        assert bucket.errors == ["validator_structure_error_empty_directory", "validator_structure_error_missing_file"]

    def test_a_categoryless_issue_is_skipped_without_raising(self) -> None:
        issue = _make_issue("DESC-001", category=None, message_key="rule.DESC-001.error", params={})
        outcome = _make_outcome("DESC-001", (issue,))
        report = ValidationReport()

        extend_report_from_outcomes([outcome], translate=lambda key, **params: key, report=report, titles=_TITLES)

        assert list(report) == []

    def test_extend_report_from_outcomes_returns_none(self) -> None:
        report = ValidationReport()
        result = extend_report_from_outcomes([], translate=lambda key, **params: key, report=report, titles=_TITLES)
        assert result is None
