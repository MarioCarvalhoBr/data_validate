#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
import sys
import re
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
import pdfkit
import platform

from data_validate.common.base.metadata_info import METADATA
from data_validate.common.utils.formatting.number_formatting import format_number_brazilian
from data_validate.controller.context.general_context import GeneralContext
from data_validate.controller.report.model_report import ModelReportList

info = METADATA


class ReportGeneratorPDF:
    """PDF and HTML report generator for data validation results.

    This class handles the generation of HTML and PDF reports from validation
    test results, including error summaries, warnings, and metadata information.

    Attributes:
        context: General context containing configuration and arguments
        num_errors: Total number of errors found in validation
        num_warnings: Total number of warnings found in validation
        number_tests: Total number of tests executed
        template_data_text: HTML template content for report generation
    """

    def __init__(self, context: GeneralContext = None):
        """Initialize the report generator with context configuration.

        Args:
            context: General context containing validation configuration
        """
        self.context = context
        self._initialize_counters()
        self._setup_paths_and_template()
        self._validate_html_template()

    def _initialize_counters(self) -> None:
        """Initialize error, warning and test counters."""
        self.num_errors = 0
        self.num_warnings = 0
        self.number_tests = 0

    def _setup_paths_and_template(self) -> None:
        """Setup file paths and template environment."""
        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder
        self.template_name = self.context.config.OUTPUT_DEFAULT_HTML
        self.template_data_text = ""
        self.required_variables = []
        self.env = Environment(loader=FileSystemLoader(self.output_folder))

    def _validate_html_template(self) -> None:
        """Validate HTML template existence and required variables."""
        # Extract template variables using regex
        variable_pattern = r"\{\{\s*.*?\s*\}\}"
        self.required_variables = re.findall(
            variable_pattern,
            self.context.config.TEMPLATE_DEFAULT_BASIC_NO_CSS
        )

        # Load template from file or use default
        template_path = self._get_template_path()
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                self.template_data_text = file.read()

        # Validate required variables and fallback to default if needed
        if self._has_missing_variables():
            self.template_data_text = self.context.config.TEMPLATE_DEFAULT_BASIC_NO_CSS

    def _get_template_path(self) -> str:
        """Get absolute path to the HTML template file.

        Returns:
            Absolute path to report template file
        """
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '../../static/report/report_template.html'
            )
        )

    def _has_missing_variables(self) -> bool:
        """Check if template has missing required variables.

        Returns:
            True if any required variables are missing from template
        """
        return any(var not in self.template_data_text for var in self.required_variables)

    def save_html_pdf_report(self, report_list: ModelReportList, tests_not_executed: List[str]) -> None:
        """Generate and save HTML and PDF reports from validation results.

        Args:
            report_list: List of validation test reports
            tests_not_executed: List of test names that were not executed
        """
        file_name = self.context.fs_utils.get_last_directory_name(path=self.input_folder)
        html_output_file = self.context.config.OUTPUT_REPORT_HTML

        self._update_counters(report_list)

        try:
            html_content = self._generate_html_content(report_list, tests_not_executed)
            output_html_path = os.path.join(self.output_folder, file_name + html_output_file)

            self._save_html_file(html_content, output_html_path)
            self._save_pdf_report(output_html_path)
            self._print_json_summary()

        except Exception as error:
            print(f'\nError creating HTML report: {error}', file=sys.stderr)

    def _update_counters(self, report_list: ModelReportList) -> None:
        """Update error, warning and test counters from report list.

        Args:
            report_list: List of validation test reports
        """
        self.num_errors = sum(len(report.errors) for report in report_list)
        self.num_warnings = sum(len(report.warnings) for report in report_list)
        self.number_tests = len(report_list)

    def _generate_html_content(self, report_list: ModelReportList, tests_not_executed: List[str]) -> str:
        """Generate HTML content from template and report data.

        Args:
            report_list: List of validation test reports
            tests_not_executed: List of test names that were not executed

        Returns:
            Rendered HTML content as string
        """
        template = self.env.from_string(self.template_data_text)
        template_vars = self._build_template_variables(report_list, tests_not_executed)
        return template.render(template_vars)

    def _build_template_variables(self, report_list: ModelReportList, tests_not_executed: List[str]) -> Dict[str, Any]:
        """Build template variables dictionary for HTML generation.

        Args:
            report_list: List of validation test reports
            tests_not_executed: List of test names that were not executed

        Returns:
            Dictionary containing all template variables
        """
        errors_html = self._format_messages_as_html(report_list, 'errors', 'text-danger-errors')
        warnings_html = self._format_messages_as_html(report_list, 'warnings', 'text-orange-warning')

        return {
            "name": info.__project_name__,
            "errors": errors_html,
            "warnings": warnings_html,
            "num_errors": format_number_brazilian(self.num_errors),
            "num_warnings": format_number_brazilian(self.num_warnings),
            "number_tests": self.number_tests,
            "text_display_version": self._get_version_text(),
            "text_display_date": self._get_date_text(),
            "text_display_sector": self._get_optional_field_text("sector", "Setor estrat&eacute;gico"),
            "text_display_protocol": self._get_optional_field_text("protocol", "Protocolo"),
            "text_display_user": self._get_optional_field_text("user", "Usu&aacute;rio"),
            "text_display_file": self._get_optional_field_text("file", "Arquivo submetido"),
            "tests_not_executed": self._format_tests_not_executed(tests_not_executed),
            "display_tests_not_executed": "block" if tests_not_executed else "none"
        }

    def _format_messages_as_html(self, report_list: ModelReportList, message_type: str, css_class: str) -> str:
        """Format error or warning messages as HTML.

        Args:
            report_list: List of validation test reports
            message_type: Type of messages to format ('errors' or 'warnings')
            css_class: CSS class for styling the messages

        Returns:
            Formatted HTML string with messages
        """
        html_parts = []

        for report in report_list:
            html_parts.append(f"<br><span class='text-primary'>{report.name_test}</span>")

            messages = getattr(report, message_type, [])
            for message in messages:
                html_parts.append(f"<br><span class='{css_class}'>{message}</span>")

        result = "\n".join(html_parts)
        return result[4:] if result.startswith("<br>") else result

    def _get_version_text(self) -> str:
        """Get formatted version text for display.

        Returns:
            Formatted version text or empty string if disabled
        """
        if self.context.data_args.data_action.no_version:
            return ""

        os_name = platform.system()
        return (f"<strong>Vers&atilde;o do validador: "
                f"<strong class='text-gray'>{info.__version__} &ndash; {os_name}</strong></strong><br>")

    def _get_date_text(self) -> str:
        """Get formatted date text for display.

        Returns:
            Formatted date text or empty string if disabled
        """
        if self.context.data_args.data_action.no_time:
            return ""

        return (f"<strong>Data e hora do processo: "
                f"<strong class='text-gray'>{info.__date_now__}</strong></strong><br>")

    def _get_optional_field_text(self, field_name: str, display_label: str) -> str:
        """Get formatted text for optional report fields.

        Args:
            field_name: Name of the field in data_report
            display_label: Label to display for the field

        Returns:
            Formatted field text or empty string if field is None
        """
        field_value = getattr(self.context.data_args.data_report, field_name, None)
        if field_value is None:
            return ""

        return (f"<strong>{display_label}: "
                f"<strong class='text-gray'>{field_value}</strong></strong><br>")

    def _format_tests_not_executed(self, tests_not_executed: List[str]) -> str:
        """Format list of tests not executed as HTML.

        Args:
            tests_not_executed: List of test names that were not executed

        Returns:
            Formatted HTML list of tests not executed
        """
        test_items = "\n".join([f"<li>{test_name}</li>" for test_name in tests_not_executed])
        return f"<ul>{test_items}</ul>"

    def _save_html_file(self, html_content: str, output_path: str) -> None:
        """Save HTML content to file.

        Args:
            html_content: HTML content to save
            output_path: Path where to save the HTML file
        """
        with open(output_path, 'w', encoding="utf-8") as file:
            file.write(html_content)
        print(f'\nHTML report created at: {output_path}')

    def _save_pdf_report(self, html_file_path: str) -> None:
        """Generate and save PDF report from HTML file.

        Args:
            html_file_path: Path to the HTML file to convert to PDF
        """
        try:
            pdf_file_path = html_file_path.replace(".html", ".pdf")
            pdf_options = self._get_pdf_options()

            pdfkit.from_file(html_file_path, pdf_file_path, options=pdf_options)
            print(f'\nPDF report created at: {pdf_file_path}\n')

        except Exception as error:
            print(f'\nError creating PDF report: {error}', file=sys.stderr)

    def _get_pdf_options(self) -> Dict[str, Any]:
        """Get PDF generation options.

        Returns:
            Dictionary with PDF generation options
        """
        return {
            'page-size': 'Letter',
            'margin-top': '0.0in',
            'margin-right': '0.0in',
            'margin-bottom': '0.0in',
            'margin-left': '0.0in',
            'encoding': "UTF-8",
            'custom-header': [('Accept-Encoding', 'gzip')],
            'cookie': [],
            'no-outline': None
        }

    def _print_json_summary(self) -> None:
        """Print JSON summary of validation results."""
        summary = {
            "data_validate": {
                "version": info.__version__,
                "report": {
                    "errors": int(self.num_errors),
                    "warnings": int(self.num_warnings),
                    "tests": int(self.number_tests)
                }
            }
        }

        json_output = str(summary).replace("'", '"')
        print(f'\n<{json_output}>\n')

    # Legacy method for backward compatibility
    def save_pdf_report(self, html_file_path: str) -> None:
        """Legacy method for PDF generation. Use _save_pdf_report instead.

        Args:
            html_file_path: Path to the HTML file to convert to PDF
        """
        self._save_pdf_report(html_file_path)
