#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Proof that `tests/unit/**` runs with an isolated current working directory
(TST-003): the autouse `_isolate_unit_test_cwd` fixture in
`tests/unit/conftest.py` chdirs every test in this subtree into a fresh
`tmp_path` before it runs, and pytest/`monkeypatch` restore the original
CWD at teardown.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestAutouseCwdIsolation:
    """Regression tests for the TST-003 autouse `tests/unit/` CWD isolation."""

    def test_cwd_is_not_the_repository_root(self, repo_root: Path) -> None:
        """The process's CWD during a `tests/unit/` test is never the repo root."""
        assert Path.cwd() != repo_root

    def test_cwd_is_empty_and_writable(self) -> None:
        """The isolated CWD starts empty and accepts a stray write, harmlessly."""
        assert list(Path.cwd().iterdir()) == []

        stray = Path("stray.txt")
        stray.write_text("temporary, auto-cleaned by pytest's tmp_path", encoding="utf-8")

        assert stray.exists()
        assert stray.resolve().parent == Path.cwd()

    def test_cwd_matches_tmp_path(self, tmp_path: Path) -> None:
        """The isolated CWD is exactly this test's `tmp_path`, not merely *some* temp dir."""
        assert Path.cwd() == tmp_path

    def test_opt_in_tmp_cwd_fixture_is_a_harmless_no_op_here(self, tmp_cwd: Path, tmp_path: Path) -> None:
        """Requesting the opt-in `tmp_cwd` fixture on top of the autouse one re-chdirs to the same dir."""
        assert tmp_cwd == tmp_path
        assert Path.cwd() == tmp_path

    @pytest.mark.keep_cwd
    def test_keep_cwd_marker_opts_out_of_isolation(self, repo_root: Path) -> None:
        """`@pytest.mark.keep_cwd` leaves the real repository CWD untouched."""
        assert Path.cwd() == repo_root
