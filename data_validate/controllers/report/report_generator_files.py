#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
import platform
import re
import sys
from typing import List, Dict, Any

import pdfkit
from jinja2 import Environment, FileSystemLoader

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.base.metadata_info import METADATA
from data_validate.helpers.common.formatting.number_formatting import (
    format_number_brazilian,
)


class ReportGeneratorFiles:
    """PDF and HTML report generator for data validation results.

    This class handles the generation of HTML and PDF reports from validation
    test results, including error summaries, warnings, and metadata information.

    Attributes:
        context: General context containing configuration and arguments
        num_errors: Total number of errors found in validation
        num_warnings: Total number of warnings found in validation
        number_tests: Total number of tests executed

        input_folder: Path to the input data folder
        output_folder: Path to the output folder for reports
        template_name: Name of the HTML template file
        template_data_text: Content of the HTML template
        required_variables: List of required variables in the template
        env: Jinja2 environment for template rendering

    """

    def __init__(self, context: GeneralContext = None):
        """Initialize the report generator with context configuration.

        Args:
            context: General context containing validation configuration
        """
        self.context = context
        self.locale = self.context.lm.current_language

        # Initialize counters
        self.num_errors = 0
        self.num_warnings = 0
        self.number_tests = 0

        # Setup file paths and template environment.
        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder
        self.template_name = self.context.config.REPORT_OUTPUT_DEFAULT_HTML
        self.template_data_text = ""
        self.required_variables = []
        self.env = Environment(loader=FileSystemLoader(self.output_folder))

        self._prepare_environment()
        self._validate_html_template()

    def _prepare_environment(self) -> None:
        self.context.fs_utils.create_directory(self.output_folder)

    def _validate_html_template(self) -> None:
        """Validate HTML template existence and required variables."""
        # Extract template variables using regex
        variable_pattern = r"\{\{\s*.*?\s*\}\}"
        self.required_variables = re.findall(
            variable_pattern, self.context.config.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS
        )

        # Load template from file or use default
        template_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../static/report/report_template.html"
            )
        )
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as file:
                self.template_data_text = file.read()

        # Validate required variables and fallback to default if needed
        if any(var not in self.template_data_text for var in self.required_variables):
            self.template_data_text = (
                self.context.config.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS
            )

    def build_report(self, report_list: ModelListReport) -> None:
        """Generate and save HTML and PDF reports from validation results.

        Args:
            report_list: List of validation test reports
        """
        file_name = self.context.fs_utils.get_last_directory_name(
            path=self.input_folder
        )
        html_output_file = self.context.config.REPORT_OUTPUT_REPORT_HTML

        self.num_errors = report_list.global_num_errors()
        self.num_warnings = report_list.global_num_warnings()
        self.number_tests = len(report_list)

        report_list_flattened = report_list.flatten(
            n_messages=self.context.config.REPORT_LIMIT_N_MESSAGES, locale=self.locale
        )

        tests_not_executed = []
        if self.context.data_args.data_action.no_spellchecker:
            tests_not_executed.append(
                self.context.config.get_verify_names()[NamesEnum.SPELL.value]
            )
        if self.context.data_args.data_action.no_warning_titles_length:
            tests_not_executed.append(
                self.context.config.get_verify_names()[NamesEnum.TITLES_N.value]
            )

        for report in report_list.reports.values():
            if not report.was_executed:
                tests_not_executed.append(report.name_test)

        try:
            html_content = self._generate_html_content(
                report_list_flattened, tests_not_executed
            )
            output_html_path = os.path.join(
                self.output_folder, file_name + html_output_file
            )

            self._save_html_file(
                html_content, output_html_path, logger=self.context.logger
            )
            self._save_pdf_file(
                pdf_options=self._get_pdf_options(),
                html_file_path=output_html_path,
                logger=self.context.logger,
            )
            self._print_json_summary()

        except Exception as error:
            msg_error = f"\nError creating HTML report: {error}"
            self.context.logger.info(msg_error)
            print(msg_error, file=sys.stderr)

    def _generate_html_content(
        self, report_list: ModelListReport, tests_not_executed: List[str]
    ) -> str:
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

    def _build_template_variables(
        self, report_list: ModelListReport, tests_not_executed: List[str]
    ) -> Dict[str, Any]:
        """Build template variables dictionary for HTML generation.

        Args:
            report_list: List of validation test reports
            tests_not_executed: List of test names that were not executed

        Returns:
            Dictionary containing all template variables
        """
        text_html_errors = self._format_messages_as_html(
            report_list, "errors", "text-danger-errors"
        )
        text_html_warnings = self._format_messages_as_html(
            report_list, "warnings", "text-orange-warning"
        )

        text_html_date_display = (
            ""
            if self.context.data_args.data_action.no_time
            else f"<strong>Data e hora do processo: <strong class='text-gray'>{METADATA.__date_now__}</strong></strong><br>"
        )
        text_html_version_and_os_info = (
            ""
            if self.context.data_args.data_action.no_version
            else f"<strong>Vers&atilde;o do validador: <strong class='text-gray'>{METADATA.__version__} &ndash; {platform.system()}</strong></strong><br>"
        )
        text_html_tests_not_executed = f"<ul>{"\n".join([f"<li>{test_name}</li>" for test_name in tests_not_executed])}</ul>"

        return {
            "name": METADATA.__project_name__,
            "errors": text_html_errors,
            "warnings": text_html_warnings,
            "num_errors": format_number_brazilian(self.num_errors),
            "num_warnings": format_number_brazilian(self.num_warnings),
            "number_tests": self.number_tests,
            "text_display_version_and_os_info": text_html_version_and_os_info,
            "text_display_date": text_html_date_display,
            "text_display_sector": self._get_optional_field_text(
                "sector", "Setor estrat&eacute;gico"
            ),
            "text_display_protocol": self._get_optional_field_text(
                "protocol", "Protocolo"
            ),
            "text_display_user": self._get_optional_field_text(
                "user", "Usu&aacute;rio"
            ),
            "text_display_file": self._get_optional_field_text(
                "file", "Arquivo submetido"
            ),
            "tests_not_executed": text_html_tests_not_executed,
            "display_tests_not_executed": "block" if tests_not_executed else "none",
        }

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

        return (
            f"<strong>{display_label}: "
            f"<strong class='text-gray'>{field_value}</strong></strong><br>"
        )

    def _print_json_summary(self) -> None:
        """Print JSON summary of validation results."""
        summary = {
            "data_validate": {
                "version": METADATA.__version__,
                "report": {
                    "errors": int(self.num_errors),
                    "warnings": int(self.num_warnings),
                    "tests": int(self.number_tests),
                },
            }
        }

        json_output = str(summary).replace("'", '"')

        msg_info = f"\n<{json_output}>\n"

        self.context.logger.info(msg_info)
        print(msg_info, file=sys.stdout)

    @staticmethod
    def _format_messages_as_html(
        report_list: ModelListReport, message_type: str, css_class: str
    ) -> str:
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
            html_parts.append(
                f"<br><span class='text-primary'>{report.name_test}</span>"
            )

            messages = getattr(report, message_type, [])
            for message in messages:
                html_parts.append(f"<br><span class='{css_class}'>{message}</span>")

        result = "\n".join(html_parts)
        return result[4:] if result.startswith("<br>") else result

    @staticmethod
    def _get_pdf_options() -> Dict[str, Any]:
        """Get PDF generation options.

        Returns:
            Dictionary with PDF generation options
        """
        return {
            "page-size": "Letter",
            "margin-top": "0.0in",
            "margin-right": "0.0in",
            "margin-bottom": "0.0in",
            "margin-left": "0.0in",
            "encoding": "UTF-8",
            "custom-header": [("Accept-Encoding", "gzip")],
            "cookie": [],
            "no-outline": None,
        }

    @staticmethod
    def _save_html_file(html_content: str, output_path: str, logger) -> None:
        """Save HTML content to file.

        Args:
            html_content: HTML content to save
            output_path: Path where to save the HTML file
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(html_content)

            msg_info = f"HTML report created at: {output_path}"

            logger.info(msg_info)
            print(msg_info, file=sys.stdout)
        except Exception as error:
            msg_error = f"Error saving HTML report: {error}"

            logger.error(msg_error)
            print(msg_error, file=sys.stderr)

    @staticmethod
    def _save_pdf_file(
        pdf_options: Dict[str, Any], html_file_path: str, logger
    ) -> None:
        """Generate and save PDF report from HTML file.

        Args:
            html_file_path: Path to the HTML file to convert to PDF
        """
        try:
            pdf_file_path = html_file_path.replace(".html", ".pdf")

            pdfkit.from_file(html_file_path, pdf_file_path, options=pdf_options)
            msg_info = f"PDF report created at: {pdf_file_path}"

            logger.info(msg_info)
            print(msg_info, file=sys.stdout)

        except Exception as error:
            msg_error = f"Error creating PDF report: {error}"

            logger.error(msg_error)
            print(msg_error, file=sys.stderr)
