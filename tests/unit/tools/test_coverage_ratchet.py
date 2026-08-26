#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/coverage_ratchet.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import coverage_ratchet


def _write_coverage_xml(path: Path, line_rate: float) -> None:
    path.write_text(f'<?xml version="1.0"?><coverage line-rate="{line_rate}"></coverage>', encoding="utf-8")


class TestReadLineRatePercent:
    """Test suite for _read_line_rate_percent()."""

    def test_read_line_rate_percent_converts_to_percentage(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        _write_coverage_xml(xml_path, 0.5599)

        assert coverage_ratchet._read_line_rate_percent(xml_path) == pytest.approx(55.99)

    def test_read_line_rate_percent_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            coverage_ratchet._read_line_rate_percent(tmp_path / "missing.xml")

    def test_read_line_rate_percent_missing_attribute_raises(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        xml_path.write_text("<coverage></coverage>", encoding="utf-8")

        with pytest.raises(ValueError):
            coverage_ratchet._read_line_rate_percent(xml_path)


class TestMain:
    """Test suite for main()."""

    def test_main_passes_when_coverage_is_higher(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        baseline_path = tmp_path / "baseline.txt"
        _write_coverage_xml(xml_path, 0.60)
        baseline_path.write_text("55.00\n", encoding="utf-8")

        exit_code = coverage_ratchet.main(["--coverage-xml", str(xml_path), "--baseline", str(baseline_path)])

        assert exit_code == 0

    def test_main_fails_when_coverage_drops_beyond_tolerance(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        baseline_path = tmp_path / "baseline.txt"
        _write_coverage_xml(xml_path, 0.50)
        baseline_path.write_text("55.00\n", encoding="utf-8")

        exit_code = coverage_ratchet.main(["--coverage-xml", str(xml_path), "--baseline", str(baseline_path)])

        assert exit_code == 1

    def test_main_tolerates_a_small_drop(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        baseline_path = tmp_path / "baseline.txt"
        _write_coverage_xml(xml_path, 0.5498)
        baseline_path.write_text("55.00\n", encoding="utf-8")

        exit_code = coverage_ratchet.main(["--coverage-xml", str(xml_path), "--baseline", str(baseline_path)])

        assert exit_code == 0

    def test_main_updates_baseline_when_requested_and_higher(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        baseline_path = tmp_path / "baseline.txt"
        _write_coverage_xml(xml_path, 0.60)
        baseline_path.write_text("55.00\n", encoding="utf-8")

        exit_code = coverage_ratchet.main(
            ["--coverage-xml", str(xml_path), "--baseline", str(baseline_path), "--update"]
        )

        assert exit_code == 0
        assert baseline_path.read_text(encoding="utf-8").strip() == "60.00"

    def test_main_does_not_lower_baseline_without_update_flag(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "coverage.xml"
        baseline_path = tmp_path / "baseline.txt"
        _write_coverage_xml(xml_path, 0.60)
        baseline_path.write_text("55.00\n", encoding="utf-8")

        coverage_ratchet.main(["--coverage-xml", str(xml_path), "--baseline", str(baseline_path)])

        assert baseline_path.read_text(encoding="utf-8").strip() == "55.00"

    def test_main_missing_coverage_report_returns_2(self, tmp_path: Path) -> None:
        baseline_path = tmp_path / "baseline.txt"
        baseline_path.write_text("55.00\n", encoding="utf-8")

        exit_code = coverage_ratchet.main(
            ["--coverage-xml", str(tmp_path / "missing.xml"), "--baseline", str(baseline_path)]
        )

        assert exit_code == 2
