#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for generating validation reports in HTML and PDF formats.

This module provides the `FileReportGenerator` class, which handles the creation
of detailed validation reports based on the results collected during the data
validation process. It supports template-based HTML generation and PDF conversion
using `pdfkit` and `jinja2`.
"""

import os
import platform
import re
import sys
from typing import List, Dict, Any

import pdfkit
from jinja2 import Environment, FileSystemLoader

from data_validate.config import NamesEnum
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.config.metadata_info import METADATA
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class FileReportGenerator:
    """
    PDF and HTML report generator for data validation results.

    This class handles the generation of HTML and PDF reports from validation
    test results, including error summaries, warnings, and metadata information.

    Attributes:
        context (GeneralContext): General context containing configuration and arguments.
        error_count (int): Total number of errors found in validation.
        warning_count (int): Total number of warnings found in validation.
        total_tests (int): Total number of tests executed.
        input_folder (str): Path to the input data folder.
        output_folder (str): Path to the output folder for reports.
        template_name (str): Name of the HTML template file.
        template_data_text (str): Content of the HTML template.
        required_variables (List[str]): List of required variables in the template.
        env (Environment): Jinja2 environment for template rendering.
    """

    def __init__(self, context: GeneralContext = None):
        """
        Initialize the report generator with context configuration.

        Args:
            context (GeneralContext): General context containing validation configuration.
        """
        self.context = context
        self.locale = self.context.language_manager.current_language

        # Initialize counters
        self.error_count = 0
        self.warning_count = 0
        self.total_tests = 0

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
        """
        Prepare the output environment by ensuring the output directory exists.

        Uses the context's file system utils to create the directory if it
        doesn't already exist.
        """
        self.context.fs_utils.create_directory(self.output_folder)

    def _validate_html_template(self) -> None:
        """
        Validate HTML template existence and required variables.

        Loads the report template from the static files directory. If the file
        doesn't exist or misses required variables, falls back to a default basic
        template defined in the configuration.
        """
        # Extract template variables using regex
        variable_pattern = r"\{\{\s*.*?\s*\}\}"
        self.required_variables = re.findall(variable_pattern, self.context.config.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS)

        # Load template from file or use default
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../static/report/report_template.html"))
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as file:
                self.template_data_text = file.read()

        # Validate required variables and fallback to default if needed
        if any(var not in self.template_data_text for var in self.required_variables):
            self.template_data_text = self.context.config.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS

    def build_report(self, report_list: ValidationReport) -> None:
        """
        Generate and save HTML and PDF reports from validation results.

        Orchestrates the report generation process:
        1. Aggregates error and warning statistics.
        2. Identifies tests that were skipped.
        3. Flattens the report list (truncating excessive messages).
        4. Generates HTML content from the template.
        5. Saves the HTML file and converts it to PDF.
        6. Prints a JSON summary to stdout.

        Args:
            report_list (ValidationReport): List of validation test reports.
        """
        file_name = self.context.fs_utils.get_last_directory_name(path=self.input_folder)
        html_output_file = self.context.config.REPORT_OUTPUT_REPORT_HTML

        self.error_count = report_list.get_total_errors()
        self.warning_count = report_list.get_total_warnings()
        self.total_tests = len(report_list)

        flattened_reports = report_list.flatten(n_messages=self.context.config.REPORT_LIMIT_N_MESSAGES, locale=self.locale)

        skipped_tests = []
        if self.context.data_args.data_action.no_spellchecker:
            skipped_tests.append(self.context.config.get_verify_names()[NamesEnum.SPELL.value])
        if self.context.data_args.data_action.no_warning_titles_length:
            skipped_tests.append(self.context.config.get_verify_names()[NamesEnum.TITLES_N.value])

        for report in report_list.reports.values():
            if not report.was_executed:
                skipped_tests.append(report.test_name)

        try:
            html_content = self._generate_html_content(flattened_reports, skipped_tests)
            output_html_path = os.path.join(self.output_folder, file_name + html_output_file)

            self._save_html_file(html_content, output_html_path, logger=self.context.logger)
            self._save_pdf_file(
                pdf_options=self._get_pdf_options(),
                html_file_path=output_html_path,
                logger=self.context.logger,
            )
            self._print_json_summary()

        except Exception as error:
            error_message = f"\nError creating HTML report: {error}"
            self.context.logger.info(error_message)
            print(error_message, file=sys.stderr)

    def _generate_html_content(self, report_list: ValidationReport, skipped_tests: List[str]) -> str:
        """
        Generate HTML content from template and report data.

        Renders the Jinja2 template with the prepared variables derived from
        the validation results.

        Args:
            report_list (ValidationReport): List of validation test reports.
            skipped_tests (List[str]): List of test names that were not executed.

        Returns:
            str: Rendered HTML content as string.
        """
        template = self.env.from_string(self.template_data_text)
        template_vars = self._build_template_variables(report_list, skipped_tests)
        return template.render(template_vars)

    def _build_template_variables(self, report_list: ValidationReport, skipped_tests: List[str]) -> Dict[str, Any]:
        """
        Build template variables dictionary for HTML generation.

        Constructs a dictionary containing all necessary data bits (metadata,
        formatted lists of issues, statistics) required by the HTML template.

        Args:
            report_list (ValidationReport): List of validation test reports.
            skipped_tests (List[str]): List of test names that were not executed.

        Returns:
            Dict[str, Any]: Dictionary containing all template variables.
        """
        errors_html = self._format_messages_as_html(report_list, "errors", "text-danger-errors")
        warnings_html = self._format_messages_as_html(report_list, "warnings", "text-orange-warning")

        date_display_html = (
            ""
            if self.context.data_args.data_action.no_time
            else f"<strong>Data e hora do processo: <strong class='text-gray'>{self.context.config.DATE_NOW}</strong></strong><br>"
        )
        text_html_version_and_os_info = (
            ""
            if self.context.data_args.data_action.no_version
            else f"<strong>Vers&atilde;o do validador: <strong class='text-gray'>{METADATA.__version__} &ndash; {platform.system()}</strong></strong><br>"
        )
        text_html_skipped_tests = f"<ul>{"\n".join([f"<li>{test_name}</li>" for test_name in skipped_tests])}</ul>"

        return {
            "name": METADATA.__project_name__,
            "errors": errors_html,
            "warnings": warnings_html,
            "error_count": NumberFormattingProcessing.format_number_brazilian(self.error_count),
            "warning_count": NumberFormattingProcessing.format_number_brazilian(self.warning_count),
            "total_tests": self.total_tests,
            "text_display_version_and_os_info": text_html_version_and_os_info,
            "text_display_date": date_display_html,
            "text_display_sector": self._get_optional_field_text("sector", "Setor estrat&eacute;gico"),
            "text_display_protocol": self._get_optional_field_text("protocol", "Protocolo"),
            "text_display_user": self._get_optional_field_text("user", "Usu&aacute;rio"),
            "text_display_file": self._get_optional_field_text("file", "Arquivo submetido"),
            "skipped_tests": text_html_skipped_tests,
            "display_tests_not_executed": "block" if skipped_tests else "none",
        }

    def _get_optional_field_text(self, field_name: str, display_label: str) -> str:
        """
        Get formatted text for optional report fields.

        Helper method to format optional metadata fields (like sector, protocol,
        user) for display in the report header.

        Args:
            field_name (str): Name of the field in data_report.
            display_label (str): Label to display for the field in the HTML.

        Returns:
            str: Formatted field text (HTML) or empty string if field is None.
        """
        field_value = getattr(self.context.data_args.data_report, field_name, None)
        if field_value is None:
            return ""

        return f"<strong>{display_label}: " f"<strong class='text-gray'>{field_value}</strong></strong><br>"

    def _print_json_summary(self) -> None:
        """
        Print JSON summary of validation results.

        Outputs a concise JSON structure to stdout and logs, containing the
        version, and counts of errors, warnings, and tests run. Useful for parsing
        by external tools.
        """
        summary = {
            "data_validate": {
                "version": METADATA.__version__,
                "report": {
                    "errors": int(self.error_count),
                    "warnings": int(self.warning_count),
                    "tests": int(self.total_tests),
                },
            }
        }

        json_output = str(summary).replace("'", '"')

        info_message = f"\n<{json_output}>\n"

        self.context.logger.info(info_message)
        print(info_message, file=sys.stdout)

    @staticmethod
    def _format_messages_as_html(report_list: ValidationReport, message_type: str, css_class: str) -> str:
        """
        Format error or warning messages as HTML.

        Iterates through reports and formats lists of messages into HTML spans
        with appropriate CSS classes.

        Args:
            report_list (ValidationReport): List of validation test reports.
            message_type (str): Type of messages to format ('errors' or 'warnings').
            css_class (str): CSS class for styling the messages.

        Returns:
            str: Formatted HTML string with messages.
        """
        html_parts = []

        for report in report_list:
            html_parts.append(f"<br><span class='text-primary'>{report.test_name}</span>")

            messages = getattr(report, message_type, [])
            for message in messages:
                html_parts.append(f"<br><span class='{css_class}' preserve-spaces>{message}</span>")

        result = "\n".join(html_parts)
        return result[4:] if result.startswith("<br>") else result

    @staticmethod
    def _get_pdf_options() -> Dict[str, Any]:
        """
        Get PDF generation options.

        Returns a dictionary of configuration options for `pdfkit` (wkhtmltopdf wrapper).
        Configures page size, margins, and encoding.

        Returns:
            Dict[str, Any]: Dictionary with PDF generation options.
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
        """
        Save HTML content to file.

        Writes the rendered HTML content to the specified file path.

        Args:
            html_content (str): HTML content to save.
            output_path (str): Path where to save the HTML file.
            logger (logging.Logger): Logger instance for status messages.
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(html_content)

            info_message = f"HTML report created at: {output_path}"

            logger.info(info_message)
            print(info_message, file=sys.stdout)
        except Exception as error:
            error_message = f"Error saving HTML report: {error}"

            logger.error(error_message)
            print(error_message, file=sys.stderr)

    @staticmethod
    def _save_pdf_file(pdf_options: Dict[str, Any], html_file_path: str, logger) -> None:
        """
        Generate and save PDF report from HTML file.

        Uses the `pdfkit` library to convert the saved HTML file into a PDF report.
        The PDF filename is derived from the HTML filename.

        Args:
            pdf_options (Dict[str, Any]): Options for PDF generation.
            html_file_path (str): Path to the source HTML file.
            logger (logging.Logger): Logger instance for status messages.
        """
        try:
            pdf_file_path = html_file_path.replace(".html", ".pdf")

            pdfkit.from_file(html_file_path, pdf_file_path, options=pdf_options)
            info_message = f"PDF report created at: {pdf_file_path}"

            logger.info(info_message)
            print(info_message, file=sys.stdout)

        except Exception as error:
            error_message = f"Error creating PDF report: {error}"

            logger.error(error_message)
            print(error_message, file=sys.stderr)
