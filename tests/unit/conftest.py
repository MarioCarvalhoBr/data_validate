#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
`tests/unit/**`-only pytest configuration.

TST-003: every test under `tests/unit/` now runs with an isolated current
working directory by default (`monkeypatch.chdir(tmp_path)`), via the
autouse `_isolate_unit_test_cwd` fixture below. This was previously
blocked: the module docstring of `tests/conftest.py` explains that an
autouse chdir broke several `tests/unit/` tests that resolved
repository-relative paths (default log/output folders, `.config/store.locale`)
against the process's CWD at fixture-setup time. Both blockers are now
fixed:

- BUG-004: `LanguageManager` takes its locale as an explicit constructor
  argument and never reads/writes `<cwd>/.config/store.locale`; its locale
  directory defaults to a path resolved from `Path(__file__)`, never the CWD.
- BUG-021: `LoggerManager`/`GeneralContext` only ever create a file logger
  under `<output_folder>/logs` (an explicit, caller-supplied path) and only
  in debug mode; there is no more implicit `logs/` directory relative to
  the CWD.

This fixture is scoped to `tests/unit/` only (this file, not
`tests/conftest.py`) so that `tests/e2e/` and `tests/benchmarks/` keep
running from the repository root, where they invoke the CLI (via
subprocess) with relative `data/input/<fixture>` paths.

A test that still needs the real CWD (e.g. one that asserts on a path
resolved relative to the repository root without using the `repo_root`/
`fixture_folder` fixtures) can opt out with `@pytest.mark.keep_cwd`. The
opt-in `tmp_cwd` fixture in `tests/conftest.py` remains available and is
unaffected by this change — a test may still request it explicitly (it is
simply a no-op re-chdir to the same `tmp_path` under this autouse regime).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_unit_test_cwd(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path | None:
    """Change every `tests/unit/**` test's CWD to an isolated temp directory.

    Args:
        request: pytest's request object, used to check for the
            `keep_cwd` opt-out marker on the current test item.
        tmp_path: pytest's built-in per-test temporary directory.
        monkeypatch: pytest's monkeypatch fixture, used to restore the
            original working directory automatically at teardown.

    Returns:
        Path | None: The temporary directory that is now the process's
            CWD, or `None` when the test opted out via `@pytest.mark.keep_cwd`.
    """
    if request.node.get_closest_marker("keep_cwd") is not None:
        return None
    monkeypatch.chdir(tmp_path)
    return tmp_path
