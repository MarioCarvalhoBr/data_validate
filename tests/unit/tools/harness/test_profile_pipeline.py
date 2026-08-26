#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/harness/profile_pipeline.py (pure helpers only; no full pipeline run)."""

from __future__ import annotations

from pathlib import Path

from tools.harness import profile_pipeline


class TestResolveInputDir:
    """Test suite for _resolve_input_dir()."""

    def test_resolve_input_dir_known_fixture_name(self) -> None:
        resolved = profile_pipeline._resolve_input_dir("data_ground_truth_01")

        assert resolved == profile_pipeline._REPO_ROOT / "data" / "input" / "data_ground_truth_01"

    def test_resolve_input_dir_existing_relative_path(self, tmp_path: Path, monkeypatch) -> None:
        target = tmp_path / "some_fixture"
        target.mkdir()
        monkeypatch.chdir(tmp_path)

        resolved = profile_pipeline._resolve_input_dir("some_fixture")

        assert resolved.resolve() == target.resolve()

    def test_resolve_input_dir_absolute_path(self, tmp_path: Path) -> None:
        assert profile_pipeline._resolve_input_dir(str(tmp_path)) == tmp_path


class TestBuildParser:
    """Test suite for build_parser()."""

    def test_build_parser_defaults(self) -> None:
        args = profile_pipeline.build_parser().parse_args([])

        assert args.fixture == profile_pipeline._DEFAULT_FIXTURE
        assert args.top == profile_pipeline._DEFAULT_TOP_N
