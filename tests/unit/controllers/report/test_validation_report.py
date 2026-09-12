#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `data_validate.controllers.report.validation_report`.

Covers BUG-005 (``flatten`` dereferencing a ``None`` context) and BUG-020
(``TestReportItem`` being collected by pytest as a test class).
"""

from __future__ import annotations

import pytest

from data_validate.controllers.report.validation_report import (
    ReportItem,
    TestReportItem,
    ValidationReport,
)


class TestReportItemClass:
    """Test suite for the `ReportItem` data model (formerly `TestReportItem`)."""

    def test_report_item_is_not_collected_as_a_test_class(self) -> None:
        """BUG-020: pytest must not collect `ReportItem`/`TestReportItem` as a test class."""
        assert ReportItem.__test__ is False
        assert TestReportItem.__test__ is False

    def test_report_item_alias_points_to_same_class(self) -> None:
        """The legacy name `TestReportItem` remains a backward-compatible alias."""
        assert TestReportItem is ReportItem


class TestValidationReportFlatten:
    """Test suite for `ValidationReport.flatten`."""

    def test_flatten_without_truncation_and_no_context_succeeds(self) -> None:
        """BUG-005a: no truncation needed -> no context required."""
        report = ValidationReport(context=None)
        report.add_by_name("check_a", errors=["e1"], warnings=["w1"])

        flattened = report.flatten(n_messages=5)

        assert flattened["check_a"].errors == ["e1"]
        assert flattened["check_a"].warnings == ["w1"]

    def test_flatten_with_truncation_and_no_context_raises_value_error(self) -> None:
        """BUG-005b: truncation needed but context is None -> explicit ValueError."""
        report = ValidationReport(context=None)
        report.add_by_name("check_a", errors=["e1", "e2", "e3"], warnings=[])

        with pytest.raises(ValueError, match="requires a context"):
            report.flatten(n_messages=1)

    def test_flatten_with_truncation_and_context_appends_omitted_message(self, mocker) -> None:
        """BUG-005c: with a context, the omitted-message line is appended via the language manager."""
        context = mocker.MagicMock()
        context.language_manager.text.return_value = "2 mensagens de erro omitidas"

        report = ValidationReport(context=context)
        report.add_by_name("check_a", errors=["e1", "e2", "e3"], warnings=[])

        flattened = report.flatten(n_messages=1)

        context.language_manager.text.assert_called_once_with("model_report_msg_errors_omitted", count="2")
        assert flattened["check_a"].errors == ["e1", "2 mensagens de erro omitidas"]
