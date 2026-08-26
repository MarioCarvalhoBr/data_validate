#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/harness/run_fixtures.py (pure helpers only; no subprocess calls)."""

from __future__ import annotations

from pathlib import Path

from tools.harness import run_fixtures


class TestDiscoverFixtures:
    """Test suite for _discover_fixtures()."""

    def test_discover_fixtures_lists_subfolders_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "b").mkdir()
        (tmp_path / "a").mkdir()
        (tmp_path / "not_a_dir.txt").write_text("x", encoding="utf-8")

        assert run_fixtures._discover_fixtures(tmp_path) == ["a", "b"]

    def test_discover_fixtures_empty_directory(self, tmp_path: Path) -> None:
        assert run_fixtures._discover_fixtures(tmp_path) == []


class TestParseSummary:
    """Test suite for _parse_summary()."""

    def test_parse_summary_extracts_counts(self) -> None:
        stdout = '\n<{"data_validate": {"version": "0.0.0", "report": {"errors": 1, "warnings": 2, "tests": 3}}}>\n'

        assert run_fixtures._parse_summary(stdout) == (1, 2, 3)

    def test_parse_summary_returns_none_triple_when_fragment_missing(self) -> None:
        assert run_fixtures._parse_summary("no summary here") == (None, None, None)

    def test_parse_summary_returns_none_triple_on_malformed_json(self) -> None:
        assert run_fixtures._parse_summary("<{not valid json}>") == (None, None, None)


class TestFormatCell:
    """Test suite for _format_cell()."""

    def test_format_cell_none_becomes_question_mark(self) -> None:
        assert run_fixtures._format_cell(None) == "?"

    def test_format_cell_value_is_stringified(self) -> None:
        assert run_fixtures._format_cell(5) == "5"


class TestBuildParser:
    """Test suite for build_parser()."""

    def test_build_parser_defaults(self) -> None:
        args = run_fixtures.build_parser().parse_args([])

        assert args.locale == "pt_BR"
        assert args.fixtures is None
