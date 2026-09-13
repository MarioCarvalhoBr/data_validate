#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for generating validation reports in HTML and PDF formats.

This module provides the `FileReportGenerator` class, which handles the creation
of detailed validation reports based on the results collected during the data
validation process. It supports template-based HTML generation (Jinja2,
autoescaped, SEC-001/ADR-0007) and optional PDF conversion (WeasyPrint, with a
legacy `pdfkit` compatibility path, SEC-002).
"""

import json
import platform
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, TemplateError, select_autoescape

from data_validate.config import NamesEnum
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.controllers.report.report_model import ReportModel, ReportSection
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.config.metadata_info import METADATA
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing

_TEMPLATE_NAME = "report_template.html"
"""str: Name of the report template, loaded from the package's own `static/report/`
directory (never the user-writable output directory -- SEC-001)."""


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
        input_folder (str): Path to the input data folder (already resolved to an
            absolute path by `DataFile`, SEC-010).
        output_folder (str): Path to the output folder for reports (already resolved
            to an absolute path by `DataFile`, SEC-010).
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

        # SEC-001/ADR-0007: templates are loaded exclusively from the package's own
        # `static/report/` directory -- never from the user-writable output directory, which
        # closed a template-planting hole -- and `autoescape` is always on, so every value
        # rendered through `{{ }}` (untrusted spreadsheet content or CLI metadata) is escaped
        # unless the template itself authors the markup (e.g. the `&ndash;`/`&eacute;` entities
        # and card layout already in `report_template.html`).
        self.env = Environment(
            loader=PackageLoader("data_validate", "static/report"),
            autoescape=select_autoescape(["html"]),
        )

        self._prepare_environment()

    def _prepare_environment(self) -> None:
        """
        Prepare the output environment by ensuring the output directory exists.

        Uses the context's file system utils to create the directory if it
        doesn't already exist.
        """
        self.context.file_system_utils.create_directory(self.output_folder)

    def _resolve_report_path(self, file_name: str, html_output_file: str) -> str:
        """Build the HTML report's output path, refusing to write outside the output dir.

        `file_name` is derived from `Path(input_folder).name` (SEC-010), which cannot itself
        contain a path separator, but this check is defence in depth against any future caller
        that supplies a `file_name` containing `..` or an absolute path.

        Args:
            file_name (str): Last path component of the input folder.
            html_output_file (str): Configured HTML report suffix (e.g. `_report.html`).

        Returns:
            str: The absolute, resolved report path.

        Raises:
            ValueError: If the resolved report path is not inside the resolved output
                directory.
        """
        output_dir = Path(self.output_folder).resolve()
        report_path = (output_dir / f"{file_name}{html_output_file}").resolve()

        if not report_path.is_relative_to(output_dir):
            raise ValueError(f"Refusing to write report outside the output directory: {report_path}")

        return str(report_path)

    def build_report(self, report_list: ValidationReport) -> None:
        """
        Generate and save HTML and PDF reports from validation results.

        Orchestrates the report generation process:
        1. Aggregates error and warning statistics.
        2. Identifies tests that were skipped.
        3. Flattens the report list (truncating excessive messages).
        4. Builds the `ReportModel` and renders it through the Jinja2 template.
        5. Saves the HTML file and converts it to PDF.
        6. Prints a JSON summary to stdout.

        SEC-004: only `OSError` (writing HTML/PDF to disk) and `jinja2.TemplateError` (rendering
        the report template) are caught here and reported to stderr/the logger; any other
        exception is an unexpected programming error and propagates to `main()`'s boundary, which
        exits with code 2.

        Args:
            report_list (ValidationReport): List of validation test reports.
        """
        file_name = self.context.file_system_utils.get_last_directory_name(path=self.input_folder)
        html_output_file = self.context.config.REPORT_OUTPUT_REPORT_HTML

        self.error_count = report_list.get_total_errors()
        self.warning_count = report_list.get_total_warnings()
        self.total_tests = len(report_list)

        flattened_reports = report_list.flatten(
            n_messages=self.context.config.REPORT_LIMIT_N_MESSAGES, locale=self.locale
        )

        skipped_tests = self._collect_skipped_tests(flattened_reports)

        try:
            report_model = self._build_report_model(flattened_reports, skipped_tests)
            html_content = self._render_html(report_model)
            output_html_path = self._resolve_report_path(file_name, html_output_file)

            self._save_html_file(html_content, output_html_path, logger=self.context.logger)
            self._save_pdf_file(
                html_file_path=output_html_path,
                logger=self.context.logger,
            )
            self._print_json_summary()

        except (OSError, TemplateError) as error:
            error_message = f"\nError creating HTML report: {error}"
            self.context.logger.info(error_message)
            print(error_message, file=sys.stderr)

    def _collect_skipped_tests(self, report_list: ValidationReport) -> list[str]:
        """
        Collect the localized names of every verification that was not executed.

        Args:
            report_list (ValidationReport): The (already flattened) report list.

        Returns:
            list[str]: Localized names of skipped verifications, in a fixed order
                (`--no-spellchecker`, then `--no-warning-titles-length`, then any report marked
                `was_executed=False`).
        """
        skipped_tests = []
        if self.context.data_args.data_action.no_spellchecker:
            skipped_tests.append(self.context.config.get_verify_names()[NamesEnum.SPELL.value])
        if self.context.data_args.data_action.no_warning_titles_length:
            skipped_tests.append(self.context.config.get_verify_names()[NamesEnum.TITLES_N.value])

        for report in report_list.reports.values():
            if not report.was_executed:
                skipped_tests.append(report.test_name)

        return skipped_tests

    def _render_html(self, report_model: ReportModel) -> str:
        """
        Render the report template against a `ReportModel`.

        Args:
            report_model (ReportModel): The immutable model built for this run.

        Returns:
            str: The rendered, autoescaped HTML content.
        """
        template = self.env.get_template(_TEMPLATE_NAME)
        return template.render(report=report_model)

    def _build_report_model(self, report_list: ValidationReport, skipped_tests: list[str]) -> ReportModel:
        """
        Build the `ReportModel` (ARC-016) the template renders.

        Every value here is a plain Python value -- no HTML is built in this method. The
        template loops over `sections`/`skipped_tests` itself (`{% for %}`) and renders every
        field through `{{ }}`, so Jinja2's `autoescape=True` (SEC-001) protects both untrusted
        spreadsheet content (`section.errors`/`section.warnings`) and CLI metadata
        (`sector`/`protocol`/`user`/`file`).

        Args:
            report_list (ValidationReport): The (already flattened) report list.
            skipped_tests (list[str]): Localized names of skipped verifications.

        Returns:
            ReportModel: The immutable model consumed by `_render_html`.
        """
        sections = tuple(
            ReportSection(
                title=report.test_name,
                errors=tuple(report.errors),
                warnings=tuple(report.warnings),
            )
            for report in report_list
        )

        show_date = not self.context.data_args.data_action.no_time
        show_version = not self.context.data_args.data_action.no_version

        return ReportModel(
            name=METADATA.__project_name__,
            error_count=NumberFormattingProcessing.format_number_brazilian(self.error_count),
            warning_count=NumberFormattingProcessing.format_number_brazilian(self.warning_count),
            total_tests=self.total_tests,
            sections=sections,
            skipped_tests=tuple(skipped_tests),
            show_date=show_date,
            date_now=self.context.config.DATE_NOW,
            show_version=show_version,
            version=METADATA.__version__,
            os_name=platform.system(),
            protocol_version=METADATA.__protocol_version__,
            sector=getattr(self.context.data_args.data_report, "sector", None),
            protocol=getattr(self.context.data_args.data_report, "protocol", None),
            user=getattr(self.context.data_args.data_report, "user", None),
            file=getattr(self.context.data_args.data_report, "file", None),
        )

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

        json_output = json.dumps(summary, ensure_ascii=False)

        info_message = f"\n<{json_output}>\n"

        self.context.logger.info(info_message)
        print(info_message, file=sys.stdout)

    @staticmethod
    def _get_pdf_options() -> dict[str, Any]:
        """
        Get PDF generation options for the legacy `pdfkit` compatibility path.

        Returns a dictionary of configuration options for `pdfkit` (wkhtmltopdf wrapper).
        Configures page size, margins, and encoding. Not used by the WeasyPrint path
        (SEC-002), which needs no equivalent options for this report's layout.

        Returns:
            dict[str, Any]: Dictionary with PDF generation options.
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

        SEC-004: only `OSError` (the family raised by `open()`/`write()` for a missing directory,
        a full disk, a permission failure, ...) is caught and reported; any other exception
        propagates.

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
            # ARC-012: machine stdout carries only the `<{json}>` summary fragment
            # (`_print_json_summary`); every other progress line goes to stderr.
            print(info_message, file=sys.stderr)
        except OSError as error:
            error_message = f"Error saving HTML report: {error}"

            logger.error(error_message)
            print(error_message, file=sys.stderr)

    @staticmethod
    def _save_pdf_file(html_file_path: str, logger) -> None:
        """
        Generate and save a PDF report from the HTML file (SEC-002).

        PDF is optional and pluggable: WeasyPrint (pure Python, actively maintained, the
        `[pdf]` Poetry extra) is tried first; `pdfkit`/`wkhtmltopdf` is tried next only for
        backward compatibility (neither is a declared dependency any more); if neither backend
        is usable, PDF generation is skipped with a message and the HTML report -- the primary,
        always-produced artefact -- is unaffected.

        SEC-004: a backend being unusable (`ImportError` -- not installed -- or `OSError` raised
        at import time, e.g. WeasyPrint's own native pango/cairo libraries missing) falls through
        to the next backend/the skip message; `OSError` raised by the backend's own conversion
        call (a real rendering failure, not an availability problem) is reported instead. Any
        other exception propagates.

        Args:
            html_file_path (str): Path to the source HTML file.
            logger (logging.Logger): Logger instance for status messages.
        """
        pdf_file_path = html_file_path.replace(".html", ".pdf")

        try:
            # Lazy import: heavy/optional dependency, only needed for PDF output (PERF-008).
            # `OSError` here (not just `ImportError`) covers WeasyPrint's own native
            # pango/cairo libraries being missing even though the Python package is installed.
            from weasyprint import HTML
        except (ImportError, OSError):
            pass
        else:
            try:
                HTML(filename=html_file_path).write_pdf(pdf_file_path)
            except OSError as error:
                error_message = f"Error creating PDF report: {error}"
                logger.error(error_message)
                print(error_message, file=sys.stderr)
                return
            info_message = f"PDF report created at: {pdf_file_path}"
            logger.info(info_message)
            print(info_message, file=sys.stderr)
            return

        try:
            # Legacy compatibility path (SEC-002): pdfkit/wkhtmltopdf are no longer declared
            # dependencies, but are still used when already present on the host.
            import pdfkit
        except ImportError:
            info_message = "PDF generation skipped: install canoa-data-validate[pdf] for PDF output."
            logger.info(info_message)
            print(info_message, file=sys.stderr)
            return

        try:
            pdfkit.from_file(html_file_path, pdf_file_path, options=FileReportGenerator._get_pdf_options())
        except OSError as error:
            error_message = f"Error creating PDF report: {error}"
            logger.error(error_message)
            print(error_message, file=sys.stderr)
            return
        info_message = f"PDF report created at: {pdf_file_path}"
        logger.info(info_message)
        print(info_message, file=sys.stderr)
