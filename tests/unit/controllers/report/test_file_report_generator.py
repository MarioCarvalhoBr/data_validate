#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `data_validate.controllers.report.file_report_generator`.

Covers BUG-010: the JSON summary printed to stdout must be built with
`json.dumps`, not `str(dict).replace("'", '"')`, so it stays valid JSON even
when a value contains a quote or a non-ASCII character.
"""

from __future__ import annotations

import json

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
