#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from helpers.common.formatting.number_formatting import format_number_brazilian
from controllers.context.general_context import GeneralContext


class ModelItemReport:
    """
    Data model for validation reports.

    Attributes:
        name_test (str): The name of the test or validation.
        errors (list[str]): List of error messages.
        warnings (list[str]): List of warning messages.
    """

    def __init__(
        self, name_test: str, errors: list[str] = None, warnings: list[str] = None
    ):
        self.name_test = name_test
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []
        self.was_executed = True

    def add_error(self, error: str):
        self.errors.append(error)

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        return bool(self.errors)

    def has_warnings(self) -> bool:
        return bool(self.warnings)


class ModelListReport:
    """
    Data model for a list of Report objects, accessible by name.

    Attributes:
        reports (dict[str, ModelItemReport]): Dictionary of Report instances by name_test.
    """

    def __init__(self, context: GeneralContext = None, reports: list = None):
        self.context = context
        self.reports = {}
        if reports:
            for report in reports:
                self.add_report(report)

    def set_not_executed(self, name_test: str):
        if name_test in self.reports:
            self.reports[name_test].was_executed = False
        else:
            self.reports[name_test] = ModelItemReport(name_test)
            self.reports[name_test].was_executed = False

    def add_report(self, report):
        self.reports[report.name_test] = report

    def add_by_name(
        self, name_test: str, errors: list[str] = None, warnings: list[str] = None
    ):
        self.reports[name_test] = ModelItemReport(name_test, errors, warnings)

    def list_all_names(self):
        return list(self.reports.keys())

    def extend(
        self, name_test: str, errors: list[str] = None, warnings: list[str] = None
    ):
        if name_test in self.reports:
            if errors:
                self.reports[name_test].errors.extend(errors)
            if warnings:
                self.reports[name_test].warnings.extend(warnings)
        else:
            self.add_by_name(name_test, errors, warnings)

    def global_num_errors(self):
        return sum(len(report.errors) for report in self.reports.values())

    def global_num_warnings(self):
        return sum(len(report.warnings) for report in self.reports.values())

    def flatten(self, n_messages: int, locale: str = "pt_BR"):
        flattened_reports = []
        for report in self.reports.values():
            flattened_report = ModelItemReport(
                name_test=report.name_test,
                errors=report.errors[:n_messages],
                warnings=report.warnings[:n_messages],
            )
            if len(report.errors) > n_messages:
                count_omitted_errors = format_number_brazilian(
                    len(report.errors) - n_messages, locale
                )
                flattened_report.add_error(
                    self.context.lm.text(
                        "model_report_msg_errors_omitted", count=count_omitted_errors
                    )
                )

            if len(report.warnings) > n_messages:
                count_omitted_warnings = format_number_brazilian(
                    len(report.warnings) - n_messages, locale
                )
                flattened_report.add_warning(
                    self.context.lm.text(
                        "model_report_msg_warnings_omitted",
                        count=count_omitted_warnings,
                    )
                )

            flattened_reports.append(flattened_report)
        return ModelListReport(context=self.context, reports=flattened_reports)

    def __getitem__(self, name):
        return self.reports[name]

    def __iter__(self):
        return iter(self.reports.values())

    def __len__(self):
        return len(self.reports)
