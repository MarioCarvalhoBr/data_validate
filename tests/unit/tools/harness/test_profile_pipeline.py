#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/harness/profile_pipeline.py.

Mostly pure-helper tests (no full pipeline run); `TestProfilePipelineSystemExit` is the one
exception, mocking `runpy.run_module` to pin `profile_pipeline()`'s own `SystemExit` handling
(PERF-009) without paying for a real end-to-end CLI run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

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


class TestProfilePipelineSystemExit:
    """Regression tests (PERF-009): `data_validate.main` always raises `SystemExit` once run
    under `runpy.run_module(..., run_name="__main__")` (its own `if __name__ == "__main__":
    sys.exit(main())`). Before this fix, that `SystemExit` propagated straight out of
    `profile_pipeline()`, so the `.prof`/text report were never written and `make profile`
    silently produced nothing (no error, no artefacts, no `dev-reports/profile/*`) — these tests
    mock `runpy.run_module` instead of running the full CLI (kept in line with this module's own
    "pure helpers only; no full pipeline run" scope) to pin the fix without the weight of a real
    end-to-end run.
    """

    @pytest.mark.parametrize("exit_code", [0, 1, 2])
    def test_profile_pipeline_writes_artifacts_despite_system_exit(
        self, tmp_path: Path, mocker: MockerFixture, exit_code: int
    ) -> None:
        mocker.patch("tools.harness.profile_pipeline.runpy.run_module", side_effect=SystemExit(exit_code))
        input_dir = tmp_path / "some_fixture"

        prof_path = profile_pipeline.profile_pipeline(
            input_dir=input_dir,
            output_dir=tmp_path / "output",
            report_dir=tmp_path / "report",
            top=5,
        )

        assert prof_path.exists()
        assert prof_path == tmp_path / "report" / "some_fixture.prof"
        assert (tmp_path / "report" / "some_fixture.top5.txt").exists()

    def test_profile_pipeline_propagates_non_system_exit_errors(self, tmp_path: Path, mocker: MockerFixture) -> None:
        mocker.patch("tools.harness.profile_pipeline.runpy.run_module", side_effect=ValueError("boom"))
        argv_before = list(sys.argv)

        with pytest.raises(ValueError, match="boom"):
            profile_pipeline.profile_pipeline(
                input_dir=tmp_path / "some_fixture",
                output_dir=tmp_path / "output",
                report_dir=tmp_path / "report",
                top=5,
            )

        # sys.argv is restored even though the call raised (the outer `finally`).
        assert sys.argv == argv_before
