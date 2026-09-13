#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `data_validate.controllers.report.file_report_generator`.

Covers BUG-010: the JSON summary printed to stdout must be built with
`json.dumps`, not `str(dict).replace("'", '"')`, so it stays valid JSON even
when a value contains a quote or a non-ASCII character.
"""

from __future__ import annotations

import builtins
import json
import subprocess
import sys

import jinja2
import pytest

from data_validate.controllers.report import file_report_generator as file_report_generator_module
from data_validate.controllers.report.file_report_generator import FileReportGenerator


def _build_generator(mocker, error_count: int, warning_count: int, total_tests: int) -> FileReportGenerator:
    """Build a `FileReportGenerator` without running its I/O-heavy `__init__`."""
    generator = FileReportGenerator.__new__(FileReportGenerator)
    generator.context = mocker.MagicMock()
    generator.error_count = error_count
    generator.warning_count = warning_count
    generator.total_tests = total_tests
    return generator


class TestPrintJsonSummary:
    """Test suite for `FileReportGenerator._print_json_summary`."""

    def test_print_json_summary_is_valid_json_with_quote_and_non_ascii_version(self, mocker, capsys) -> None:
        """BUG-010: a version containing a quote/non-ASCII char must still yield parseable JSON."""
        generator = _build_generator(mocker, error_count=2, warning_count=1, total_tests=10)

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = '1.0.0"-café'
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        generator._print_json_summary()

        captured = capsys.readouterr()
        fragment = captured.out.strip()
        assert fragment.startswith("<") and fragment.endswith(">")

        payload = json.loads(fragment[1:-1])
        assert payload == {
            "data_validate": {
                "version": '1.0.0"-café',
                "report": {"errors": 2, "warnings": 1, "tests": 10},
            }
        }

    def test_print_json_summary_matches_previous_fragment_shape_for_plain_version(self, mocker, capsys) -> None:
        """The printed fragment keeps the same shape/spacing for a version with no special characters."""
        generator = _build_generator(mocker, error_count=0, warning_count=3, total_tests=34)

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "1.2.3"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        generator._print_json_summary()

        captured = capsys.readouterr()
        fragment = captured.out.strip()

        summary = {
            "data_validate": {
                "version": "1.2.3",
                "report": {"errors": 0, "warnings": 3, "tests": 34},
            }
        }
        expected = f"<{str(summary).replace(chr(39), chr(34))}>"

        assert fragment == expected


class TestBuildTemplateVariablesVersionLine:
    """Test suite for the version/protocol line built by `_build_template_variables` (DOC-006)."""

    @staticmethod
    def _build_generator_for_html(mocker) -> FileReportGenerator:
        generator = _build_generator(mocker, error_count=0, warning_count=0, total_tests=0)
        generator.context.data_args.data_action.no_time = True
        generator.context.data_args.data_report.sector = None
        generator.context.data_args.data_report.protocol = None
        generator.context.data_args.data_report.user = None
        generator.context.data_args.data_report.file = None
        return generator

    def test_version_line_includes_validator_version_and_protocol_version(self, mocker) -> None:
        """DOC-006: the report header surfaces both the validator and the protocol version."""
        generator = self._build_generator_for_html(mocker)
        generator.context.data_args.data_action.no_version = False

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "0.7.65"
        fake_metadata.__protocol_version__ = "1.16"
        fake_metadata.__project_name__ = "Canoa"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        template_vars = generator._build_template_variables([], [])
        version_line = template_vars["text_display_version_and_os_info"]

        assert "0.7.65" in version_line
        assert "1.16" in version_line
        assert "Protocolo" in version_line

    def test_version_line_empty_when_no_version_flag_set(self, mocker) -> None:
        """`--no-version` still suppresses the whole line, protocol version included."""
        generator = self._build_generator_for_html(mocker)
        generator.context.data_args.data_action.no_version = True

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "0.7.65"
        fake_metadata.__protocol_version__ = "1.16"
        fake_metadata.__project_name__ = "Canoa"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        template_vars = generator._build_template_variables([], [])

        assert template_vars["text_display_version_and_os_info"] == ""


class TestBuildReportExceptionHandling:
    """SEC-004: `build_report`'s except clause narrows to `(OSError, jinja2.TemplateError)`."""

    @staticmethod
    def _build_generator_for_build_report(mocker) -> FileReportGenerator:
        generator = _build_generator(mocker, error_count=0, warning_count=0, total_tests=0)
        generator.input_folder = "/input"
        generator.output_folder = "/output"
        generator.locale = "pt_BR"
        generator.context.file_system_utils.get_last_directory_name.return_value = "bundle"
        generator.context.config.REPORT_OUTPUT_REPORT_HTML = "_report.html"
        generator.context.data_args.data_action.no_spellchecker = False
        generator.context.data_args.data_action.no_warning_titles_length = False
        return generator

    @staticmethod
    def _fake_report_list(mocker):
        report_list = mocker.MagicMock()
        report_list.get_total_errors.return_value = 0
        report_list.get_total_warnings.return_value = 0
        report_list.flatten.return_value = mocker.MagicMock()
        report_list.reports = {}
        return report_list

    def test_build_report_catches_template_error(self, mocker, capsys) -> None:
        """A template-rendering failure is reported, not raised."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_generate_html_content", side_effect=jinja2.TemplateError("bad template"))

        generator.build_report(report_list)

        captured = capsys.readouterr()
        assert "Error creating HTML report" in captured.err
        generator.context.logger.info.assert_called_once()

    def test_build_report_catches_os_error(self, mocker, capsys) -> None:
        """A filesystem failure surfacing from the report pipeline is reported, not raised."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_generate_html_content", side_effect=OSError("disk full"))

        generator.build_report(report_list)

        captured = capsys.readouterr()
        assert "Error creating HTML report" in captured.err

    def test_build_report_propagates_unexpected_error(self, mocker) -> None:
        """A programming error that is neither `OSError` nor `jinja2.TemplateError` propagates."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_generate_html_content", side_effect=ValueError("boom"))

        with pytest.raises(ValueError, match="boom"):
            generator.build_report(report_list)


class TestSaveHtmlFileExceptionHandling:
    """SEC-004: `_save_html_file` catches only `OSError`."""

    def test_save_html_file_catches_os_error(self, mocker, capsys) -> None:
        mocker.patch("builtins.open", side_effect=OSError("disk full"))
        logger = mocker.MagicMock()

        FileReportGenerator._save_html_file("<html></html>", "/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error saving HTML report" in captured.err
        logger.error.assert_called_once()

    def test_save_html_file_propagates_unexpected_error(self, mocker) -> None:
        mocker.patch("builtins.open", side_effect=ValueError("boom"))
        logger = mocker.MagicMock()

        with pytest.raises(ValueError, match="boom"):
            FileReportGenerator._save_html_file("<html></html>", "/out/report.html", logger)


class TestSavePdfFileExceptionHandling:
    """SEC-004: `_save_pdf_file` catches only `(ImportError, OSError)`."""

    def test_save_pdf_file_catches_import_error_when_pdfkit_missing(self, mocker, capsys) -> None:
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "pdfkit":
                raise ImportError("No module named 'pdfkit'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file({}, "/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error creating PDF report" in captured.err

    def test_save_pdf_file_catches_os_error_from_pdfkit(self, mocker, capsys) -> None:
        fake_pdfkit = mocker.MagicMock()
        fake_pdfkit.from_file.side_effect = OSError("wkhtmltopdf exited with non-zero code")
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file({}, "/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error creating PDF report" in captured.err

    def test_save_pdf_file_propagates_unexpected_error(self, mocker) -> None:
        fake_pdfkit = mocker.MagicMock()
        fake_pdfkit.from_file.side_effect = TypeError("boom")
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        with pytest.raises(TypeError, match="boom"):
            FileReportGenerator._save_pdf_file({}, "/out/report.html", logger)


class TestLazyPdfkitImport:
    """PERF-008: `pdfkit` must not be imported by merely importing this module.

    `pdfkit` is a heavy/optional dependency needed only by `_save_pdf_file`'s
    HTML→PDF conversion; HTML-only flows (or a process that never reaches PDF
    generation) must not pay its import cost.
    """

    def test_module_import_does_not_import_pdfkit(self) -> None:
        """Importing the module alone, in a fresh subprocess, must not import `pdfkit`."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                "import data_validate.controllers.report.file_report_generator; "
                "import sys; "
                "assert 'pdfkit' not in sys.modules, sys.modules.keys()",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
