#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Global pytest configuration and fixtures.

The `tmp_cwd` fixture below is opt-in — request it explicitly in a test's
signature — and remains available repo-wide (e.g. for `tests/e2e/` cases
that want an isolated CWD for a single test without running the whole
subtree from one). It is no longer the only isolation mechanism: TST-003
adds an *autouse* CWD-isolation fixture scoped to `tests/unit/**` in
`tests/unit/conftest.py` (`_isolate_unit_test_cwd`), so every unit test
now runs with `Path.cwd()` pointed at a fresh `tmp_path` unless it opts
out with `@pytest.mark.keep_cwd`.

An autouse `monkeypatch.chdir(tmp_path)` at this repo-wide level was tried
first, as suggested by the harness spec, but `tests/e2e/` and
`tests/benchmarks/` invoke the CLI (via subprocess) with relative
`data/input/<fixture>` paths and must keep running from the repository
root — hence the fixture lives in `tests/unit/conftest.py` instead of
here. Making it autouse for `tests/unit/` specifically was blocked until
BUG-004 (no more `.config/store.locale` file I/O in `LanguageManager`) and
BUG-021 (the file logger is only created under an explicit
`<output_folder>/logs`, never a CWD-relative `logs/`) landed; both are
fixed, so the autouse fixture is now safe for the whole `tests/unit/`
subtree — see `tests/unit/conftest.py` for the fixture itself.
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

    Kept for the legacy `pdfkit`/`wkhtmltopdf` compatibility path (SEC-002); see
    `pdf_backend_available` for the probe that also covers WeasyPrint.

    Returns:
        bool: True when `wkhtmltopdf` can be resolved via `shutil.which`.
    """
    return shutil.which("wkhtmltopdf") is not None


@functools.lru_cache(maxsize=1)
def pdf_backend_available() -> bool:
    """Detect whether *any* PDF rendering backend is usable (SEC-002).

    `FileReportGenerator._save_pdf_file` tries WeasyPrint first (the `[pdf]` extra), then
    falls back to `pdfkit`/`wkhtmltopdf` if present, so a test asserting PDF output must
    accept either backend rather than only the legacy `wkhtmltopdf` binary.

    Returns:
        bool: True when WeasyPrint is importable or `wkhtmltopdf` is on `PATH`.
    """
    return importlib.util.find_spec("weasyprint") is not None or wkhtmltopdf_available()


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
    skip_pdf = pytest.mark.skip(reason="no PDF backend (WeasyPrint or wkhtmltopdf) available in this environment")
    enchant_ok = enchant_pt_br_available()
    pdf_ok = pdf_backend_available()

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

    Opt-in: request the `tmp_cwd` fixture explicitly in a test's signature.
    Every `tests/unit/**` test already gets this behaviour automatically
    via the autouse fixture in `tests/unit/conftest.py` (TST-003); this
    fixture remains available repo-wide (e.g. for an individual
    `tests/e2e/`/`tests/benchmarks/` test that wants isolation without
    the whole subtree running from `tmp_path`) and is a harmless no-op
    re-chdir when a `tests/unit/**` test requests it on top of the
    autouse isolation.

    Args:
        tmp_path: pytest's built-in per-test temporary directory.
        monkeypatch: pytest's monkeypatch fixture, used to restore the
            original working directory automatically at teardown.

    Returns:
        Path: The temporary directory that is now the process's CWD.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
