#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

class Report:
    """
    Data model for validation reports.

    Attributes:
        name_test (str): The name of the test or validation.
        errors (list[str]): List of error messages.
        warnings (list[str]): List of warning messages.
    """
    def __init__(self, name_test: str, errors: list[str] = None, warnings: list[str] = None):
        self.name_test = name_test
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []

    def add_error(self, error: str):
        self.errors.append(error)

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        return bool(self.errors)

    def has_warnings(self) -> bool:
        return bool(self.warnings)


class ReportList:
    """
    Data model for a list of Report objects, accessible by name.

    Attributes:
        reports (dict[str, Report]): Dictionary of Report instances by name_test.
    """
    def __init__(self, reports: list = None):
        self.reports = {}
        if reports:
            for report in reports:
                self.add_report(report)

    def add_report(self, report):
        self.reports[report.name_test] = report

    def add_by_name(self, name_test: str, errors: list[str] = None, warnings: list[str] = None):
        self.reports[name_test] = Report(name_test, errors, warnings)

    def extend(self, name_test: str, errors: list[str] = None, warnings: list[str] = None):
        if name_test in self.reports:
            if errors:
                self.reports[name_test].errors.extend(errors)
            if warnings:
                self.reports[name_test].warnings.extend(warnings)
        else:
            self.add_by_name(name_test, errors, warnings)

    def __getitem__(self, name):
        return self.reports[name]

    def __iter__(self):
        return iter(self.reports.values())

    def __len__(self):
        return len(self.reports)

def main():
    # Create 4 reports, each with 5 different errors
    report_names = ["Structure", "Cleaning", "Relations", "Legend"]
    report_list = ReportList()
    for idx, name in enumerate(report_names):
        errors = [f"Error {i+1} in {name}" for i in range(5)]
        report = Report(name_test=name, errors=errors)
        report_list.add_report(report)

    # Print all reports and their errors
    for report in report_list:
        print(f"Report: {report.name_test}")
        print("  Errors:")
        for error in report.errors:
            print(f"    - {error}")
        print("  Warnings:")
        for warning in report.warnings:
            print(f"    - {warning}")
        print()

if __name__ == "__main__":
    main()