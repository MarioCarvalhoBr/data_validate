#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Pytest configuration for the golden end-to-end harness (`tests/e2e/`).

Adds the `--update-golden` CLI option (used by `make harness-update`) and
automatically applies the `e2e` marker to every test collected under this
directory, so `make test-e2e` (`pytest tests/e2e -m e2e`) and `make
test-unit` (`pytest tests/unit -m "not e2e"`) select the right tests
without every test module having to repeat `pytestmark`.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the `--update-golden` option.

    Args:
        parser: The pytest argument parser to extend.
    """
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate tests/e2e/golden/*.json from the current CLI output instead of comparing against it.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Mark every test collected under `tests/e2e/` with `@pytest.mark.e2e`.

    Args:
        config: The pytest configuration object (unused, required by the hook signature).
        items: The collected test items to mark.
    """
    del config
    e2e_marker = pytest.mark.e2e
    for item in items:
        item.add_marker(e2e_marker)
