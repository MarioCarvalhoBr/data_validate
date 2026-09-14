#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for managing validation reports data models.

This module defines structures to store, manage, and retrieve validation errors
and warnings generated during the data validation process.
"""

from typing import List, Optional, Iterator, cast

from data_validate.controllers import GeneralContext
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class ReportItem:
    """
    Data model for a single validation report item.

    This class encapsulates results for a specific validation test, including
    lists of errors and warnings encountered.

    Attributes:
        test_name (str): The identifier of the test or validation.
        errors (List[str]): List of error messages associated with the test.
        warnings (List[str]): List of warning messages associated with the test.
        was_executed (bool): Flag indicating if the validation was executed.
    """

    # Not a pytest test class despite the legacy `TestReportItem` alias name below (BUG-020).
    __test__ = False

    def __init__(self, test_name: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        """
        Initialize a ReportItem.

        Args:
            test_name (str): The name/identifier of the test.
            errors (Optional[List[str]]): Initial list of error messages. Defaults to None.
            warnings (Optional[List[str]]): Initial list of warning messages. Defaults to None.
        """
        self.test_name = test_name
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []
        self.was_executed = True

    def add_error(self, error: str) -> None:
        """
        Add an error message to the report.

        Args:
            error (str): The error message to add.
        """
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """
        Add a warning message to the report.

        Args:
            warning (str): The warning message to add.
        """
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """
        Check if the report contains any errors.

        Returns:
            bool: True if validation errors exist, False otherwise.
        """
        return bool(self.errors)


# Backward-compatible alias kept for one release after the BUG-020 rename;
# `ReportItem.__test__ = False` above already stops pytest from collecting it.
TestReportItem = ReportItem


class ValidationReport:
    """
    Data model for a collection of validation reports, accessible by test name.

    Aggregates multiple `ModelItemReport` instances and provides utility methods
    to report and manipulate validation results globally.

    Attributes:
        context (Optional[GeneralContext]): Application context for localization and utils.
        reports (dict[str, ReportItem]): Dictionary of reports indexed by their test name.
    """

    def __init__(self, context: Optional["GeneralContext"] = None, reports: Optional[List[ReportItem]] = None):
        """
        Initialize a ValidationReport.

        Args:
            context (Optional[GeneralContext]): DI context. Defaults to None.
            reports (Optional[List[ReportItem]]): Initial list of reports. Defaults to None.
        """
        self.context = context
        self.reports: dict[str, ReportItem] = {}
        if reports:
            for report in reports:
                self.add_report(report)

    def add_report(self, report: ReportItem) -> None:
        """
        Add a full report object to the collection.

        Args:
            report (ReportItem): The report instance to add.
        """
        self.reports[report.test_name] = report

    def add_by_name(
        self, name_test: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None
    ) -> None:
        """
        Create and add a report by name with optional errors and warnings.

        Args:
            name_test (str): name of the test.
            errors (Optional[List[str]]): List of errors. Defaults to None.
            warnings (Optional[List[str]]): List of warnings. Defaults to None.
        """
        self.reports[name_test] = ReportItem(name_test, errors, warnings)

    def extend(self, name_test: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> None:
        """
        Extend an existing report with new errors/warnings, or create it if missing.

        Args:
            name_test (str): The name of the test to extend.
            errors (Optional[List[str]]): List of errors to append. Defaults to None.
            warnings (Optional[List[str]]): List of warnings to append. Defaults to None.
        """
        if name_test in self.reports:
            if errors:
                self.reports[name_test].errors.extend(errors)
            if warnings:
                self.reports[name_test].warnings.extend(warnings)
        else:
            self.add_by_name(name_test, errors, warnings)

    def get_total_errors(self) -> int:
        """
        Calculate total number of errors across all reports.

        Returns:
            int: Global error count.
        """
        return sum(len(report.errors) for report in self.reports.values())

    def get_total_warnings(self) -> int:
        """
        Calculate total number of warnings across all reports.

        Returns:
            int: Global warning count.
        """
        return sum(len(report.warnings) for report in self.reports.values())

    def flatten(self, n_messages: int, locale: str = "pt_BR") -> "ValidationReport":
        """
        Create a new ModelListReport with truncated error/warning lists.

        Limits the number of messages per report to `n_messages`. If messages are
        truncated, adds a summary message indicating count of omitted items.

        Args:
            n_messages (int): Maximum number of messages to retain per category.
            locale (str): Locale for message formatting. Defaults to "pt_BR".

        Returns:
            ValidationReport: A new flattened report instance.

        Raises:
            ValueError: If truncation is required (some report exceeds
                `n_messages` errors or warnings) but no `context` was set on
                this instance, since a context is needed to translate the
                omitted-message summary. Instances with no truncation needed
                do not require a context (BUG-005).
        """
        needs_truncation = any(
            len(report.errors) > n_messages or len(report.warnings) > n_messages for report in self.reports.values()
        )
        if needs_truncation and self.context is None:
            raise ValueError("ValidationReport.flatten requires a context for message translation")

        flattened_reports = []
        for report in self.reports.values():
            flattened_report = ReportItem(
                test_name=report.test_name,
                errors=report.errors[:n_messages],
                warnings=report.warnings[:n_messages],
            )
            if len(report.errors) > n_messages:
                omitted_errors_count = NumberFormattingProcessing.format_number_brazilian(
                    len(report.errors) - n_messages, locale
                )
                # `needs_truncation` (checked above) is exactly this condition ORed across
                # every report, so reaching here means `self.context is None` would already
                # have raised; the cast is typing-only narrowing, not a new guard.
                context = cast(GeneralContext, self.context)
                flattened_report.add_error(
                    context.language_manager.text("model_report_msg_errors_omitted", count=omitted_errors_count)
                )

            if len(report.warnings) > n_messages:
                count_omitted_warnings = NumberFormattingProcessing.format_number_brazilian(
                    len(report.warnings) - n_messages, locale
                )
                context = cast(GeneralContext, self.context)
                flattened_report.add_warning(
                    context.language_manager.text(
                        "model_report_msg_warnings_omitted",
                        count=count_omitted_warnings,
                    )
                )

            flattened_reports.append(flattened_report)
        return ValidationReport(context=self.context, reports=flattened_reports)

    def __getitem__(self, name: str) -> ReportItem:
        """
        Retrieve a report by name.

        Args:
            name (str): The name of the test.

        Returns:
            ReportItem: The requested report object.
        """
        return self.reports[name]

    def __iter__(self) -> Iterator[ReportItem]:
        """
        Iterate over the reports.

        Returns:
            Iterator[ReportItem]: Iterator over Report objects.
        """
        return iter(self.reports.values())

    def __len__(self) -> int:
        """
        Get the number of reports.

        Returns:
            int: Count of reports.
        """
        return len(self.reports)
