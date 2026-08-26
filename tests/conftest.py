#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Global pytest configuration and fixtures.

The `tmp_cwd` fixture below is opt-in (marker `isolated_cwd`), not
autouse. An autouse `monkeypatch.chdir(tmp_path)` was tried first, as
suggested by the harness spec, but several existing unit tests under
`tests/unit/` construct `LoggerManager`/`FileSystemUtils` instances that
resolve relative paths (e.g. default log/output folders) against the
process's current working directory at collection or fixture-setup time,
and some read the real repository tree (e.g. locale catalogs) via paths
that are only valid from the repository root. Chdir'ing every test into an
empty `tmp_path` broke those tests, and this run may not modify
`tests/unit/**`. Making the fixture opt-in keeps all 878 existing unit
tests green while still giving new tests (e.g. `tests/e2e/`) an explicit,
readable way to ask for an isolated CWD when they need one.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the absolute path of the repository root.

    Returns:
        Path: The repository root directory, resolved from this file's
            location (`tests/conftest.py` is one level below the root).
    """
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def fixture_folder(repo_root: Path) -> Callable[[str], Path]:
    """Return a factory that resolves a fixture folder under `data/input/`.

    Args:
        repo_root: The repository root fixture.

    Returns:
        Callable[[str], Path]: A function that, given a fixture name, returns
            the absolute path to `data/input/<name>`. The returned function
            calls `pytest.skip` with a clear reason when the folder is
            missing, so tests can request a fixture without a manual
            existence check.
    """

    def _fixture_folder(name: str) -> Path:
        path = repo_root / "data" / "input" / name
        if not path.is_dir():
            pytest.skip(f"fixture folder not found: {path}")
        return path

    return _fixture_folder


@pytest.fixture
def tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change the process's working directory to an isolated temp directory.

    Opt-in via `@pytest.mark.isolated_cwd` (request the fixture explicitly
    in the test signature) rather than autouse — see the module docstring
    for why: several `tests/unit/**` tests are sensitive to the working
    directory and this run may not edit `tests/unit/**`. New tests that
    would otherwise write `.config/` or `data/output/logs/` under the repo
    root should request this fixture explicitly.

    Args:
        tmp_path: pytest's built-in per-test temporary directory.
        monkeypatch: pytest's monkeypatch fixture, used to restore the
            original working directory automatically at teardown.

    Returns:
        Path: The temporary directory that is now the process's CWD.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
