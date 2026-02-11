#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module for managing validation reports data models.

This module defines structures to store, manage, and retrieve validation errors
and warnings generated during the data validation process.
"""

from typing import List, Optional, Iterator

from data_validate.controllers import GeneralContext
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class ModelItemReport:
    """
    Data model for a single validation report item.

    This class encapsulates results for a specific validation test, including
    lists of errors and warnings encountered.

    Attributes:
        name_test (str): The identifier of the test or validation.
        errors (List[str]): List of error messages associated with the test.
        warnings (List[str]): List of warning messages associated with the test.
        was_executed (bool): Flag indicating if the validation was executed.
    """

    def __init__(self, name_test: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        """
        Initialize a ModelItemReport.

        Args:
            name_test (str): The name/identifier of the test.
            errors (Optional[List[str]]): Initial list of error messages. Defaults to None.
            warnings (Optional[List[str]]): Initial list of warning messages. Defaults to None.
        """
        self.name_test = name_test
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

    def has_warnings(self) -> bool:
        """
        Check if the report contains any warnings.

        Returns:
            bool: True if validation warnings exist, False otherwise.
        """
        return bool(self.warnings)


class ModelListReport:
    """
    Data model for a collection of validation reports, accessible by test name.

    Aggregates multiple `ModelItemReport` instances and provides utility methods
    to report and manipulate validation results globally.

    Attributes:
        context (Optional[GeneralContext]): Application context for localization and utils.
        reports (dict[str, ModelItemReport]): Dictionary of reports indexed by their test name.
    """

    def __init__(self, context: Optional["GeneralContext"] = None, reports: Optional[List[ModelItemReport]] = None):
        """
        Initialize a ModelListReport.

        Args:
            context (Optional[GeneralContext]): DI context. Defaults to None.
            reports (Optional[List[ModelItemReport]]): Initial list of reports. Defaults to None.
        """
        self.context = context
        self.reports: dict[str, ModelItemReport] = {}
        if reports:
            for report in reports:
                self.add_report(report)

    def set_not_executed(self, name_test: str) -> None:
        """
        Mark a specific test as not executed.

        If the report does not exist, it creates a new one marked as not executed.

        Args:
            name_test (str): The name of the test to mark.
        """
        if name_test in self.reports:
            self.reports[name_test].was_executed = False
        else:
            self.reports[name_test] = ModelItemReport(name_test)
            self.reports[name_test].was_executed = False

    def add_report(self, report: ModelItemReport) -> None:
        """
        Add a full report object to the collection.

        Args:
            report (ModelItemReport): The report instance to add.
        """
        self.reports[report.name_test] = report

    def add_by_name(self, name_test: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> None:
        """
        Create and add a report by name with optional errors and warnings.

        Args:
            name_test (str): name of the test.
            errors (Optional[List[str]]): List of errors. Defaults to None.
            warnings (Optional[List[str]]): List of warnings. Defaults to None.
        """
        self.reports[name_test] = ModelItemReport(name_test, errors, warnings)

    def list_all_names(self) -> List[str]:
        """
        List all names of the stored reports.

        Returns:
            List[str]: List of test names.
        """
        return list(self.reports.keys())

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

    def global_num_errors(self) -> int:
        """
        Calculate total number of errors across all reports.

        Returns:
            int: Global error count.
        """
        return sum(len(report.errors) for report in self.reports.values())

    def global_num_warnings(self) -> int:
        """
        Calculate total number of warnings across all reports.

        Returns:
            int: Global warning count.
        """
        return sum(len(report.warnings) for report in self.reports.values())

    def flatten(self, n_messages: int, locale: str = "pt_BR") -> "ModelListReport":
        """
        Create a new ModelListReport with truncated error/warning lists.

        Limits the number of messages per report to `n_messages`. If messages are
        truncated, adds a summary message indicating count of omitted items.

        Args:
            n_messages (int): Maximum number of messages to retain per category.
            locale (str): Locale for message formatting. Defaults to "pt_BR".

        Returns:
            ModelListReport: A new flattened report instance.
        """
        flattened_reports = []
        for report in self.reports.values():
            flattened_report = ModelItemReport(
                name_test=report.name_test,
                errors=report.errors[:n_messages],
                warnings=report.warnings[:n_messages],
            )
            if len(report.errors) > n_messages:
                count_omitted_errors = NumberFormattingProcessing.format_number_brazilian(len(report.errors) - n_messages, locale)
                flattened_report.add_error(self.context.lm.text("model_report_msg_errors_omitted", count=count_omitted_errors))

            if len(report.warnings) > n_messages:
                count_omitted_warnings = NumberFormattingProcessing.format_number_brazilian(len(report.warnings) - n_messages, locale)
                flattened_report.add_warning(
                    self.context.lm.text(
                        "model_report_msg_warnings_omitted",
                        count=count_omitted_warnings,
                    )
                )

            flattened_reports.append(flattened_report)
        return ModelListReport(context=self.context, reports=flattened_reports)

    def __getitem__(self, name: str) -> ModelItemReport:
        """
        Retrieve a report by name.

        Args:
            name (str): The name of the test.

        Returns:
            ModelItemReport: The requested report object.
        """
        return self.reports[name]

    def __iter__(self) -> Iterator[ModelItemReport]:
        """
        Iterate over the reports.

        Returns:
            Iterator[ModelItemReport]: Iterator over Report objects.
        """
        return iter(self.reports.values())

    def __len__(self) -> int:
        """
        Get the number of reports.

        Returns:
            int: Count of reports.
        """
        return len(self.reports)
