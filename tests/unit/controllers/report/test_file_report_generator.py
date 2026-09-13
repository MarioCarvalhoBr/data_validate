#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `data_validate.controllers.report.file_report_generator`.

Covers BUG-010: the JSON summary printed to stdout must be built with
`json.dumps`, not `str(dict).replace("'", '"')`, so it stays valid JSON even
when a value contains a quote or a non-ASCII character.
"""

from __future__ import annotations

import json
import subprocess
import sys

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
