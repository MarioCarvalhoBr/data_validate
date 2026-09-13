#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Global pytest configuration and fixtures.

The `tmp_cwd` fixture below is opt-in — request it explicitly in a test's
signature — not autouse. An autouse `monkeypatch.chdir(tmp_path)` was tried first, as
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

import functools
import importlib
import importlib.util
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

_REQUIRES_ENCHANT_MARKER = "requires_enchant"
_REQUIRES_PDF_MARKER = "requires_pdf"


@functools.lru_cache(maxsize=1)
def enchant_pt_br_available() -> bool:
    """Detect whether a working pt_BR hunspell dictionary is available via `enchant`.

    Centralises the probe previously duplicated in `tests/e2e/test_golden.py`
    (`_spell_backend_available`) and
    `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py`
    (`_real_pt_br_dictionary_available`) — see TST-007. Cached because
    constructing an `enchant.Dict` touches the native libenchant/hunspell
    backend and is only worth paying for once per test session.

    Returns:
        bool: True when `enchant` is importable and can load a `pt_BR`
            dictionary; False when the module is missing, the native
            backend cannot be loaded, or no `pt_BR` word list is installed.
    """
    if importlib.util.find_spec("enchant") is None:
        return False
    try:
        # Deferred, optional import: pyenchant is a system-dependent runtime extra, not
        # guaranteed to be installed, so it cannot be imported unconditionally at module level
        # without breaking test collection on environments without it.
        enchant = importlib.import_module("enchant")
        enchant.Dict("pt_BR")
    except (enchant.errors.Error, OSError, ImportError):
        return False
    return True


@functools.lru_cache(maxsize=1)
def wkhtmltopdf_available() -> bool:
    """Detect whether the `wkhtmltopdf` binary is on `PATH`.

    Returns:
        bool: True when `wkhtmltopdf` can be resolved via `shutil.which`.
    """
    return shutil.which("wkhtmltopdf") is not None


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip `requires_enchant`/`requires_pdf` tests when the optional dependency is absent.

    Centralises the marker-driven skip described in `.claude/rules/testing.md`
    ("Skip (don't fail) when optional system dependency unavailable") so no
    individual test module needs its own `skipif`/probe (TST-007).

    Args:
        items: The collected test items, mutated in place to add skip
            markers where the corresponding backend is unavailable.
    """
    skip_enchant = pytest.mark.skip(reason="pyenchant/hunspell pt_BR backend unavailable in this environment")
    skip_pdf = pytest.mark.skip(reason="wkhtmltopdf not installed in this environment")
    enchant_ok = enchant_pt_br_available()
    pdf_ok = wkhtmltopdf_available()

    for item in items:
        if _REQUIRES_ENCHANT_MARKER in item.keywords and not enchant_ok:
            item.add_marker(skip_enchant)
        if _REQUIRES_PDF_MARKER in item.keywords and not pdf_ok:
            item.add_marker(skip_pdf)


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

    Opt-in: request the `tmp_cwd` fixture explicitly in a test's signature
    rather than autouse — see the module docstring for why: several
    `tests/unit/**` tests are sensitive to the working directory and this
    run may not edit `tests/unit/**`. New tests that would otherwise write
    `.config/` or `data/output/logs/` under the repo root should request
    this fixture explicitly.

    Args:
        tmp_path: pytest's built-in per-test temporary directory.
        monkeypatch: pytest's monkeypatch fixture, used to restore the
            original working directory automatically at teardown.

    Returns:
        Path: The temporary directory that is now the process's CWD.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
