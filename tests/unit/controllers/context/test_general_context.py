#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `GeneralContext` (controllers/context/general_context.py).

Covers the Phase 1 locale/context slice:
- BUG-004/BUG-023: a single `LanguageManager`, built from `data_args.data_file.locale`,
  is shared by `ApplicationConfig` and `FileSystemUtils` (one locale source of truth).
- BUG-021: the file logger is only created in debug mode, under
  `<output_folder>/logs` (never a `logs/` directory relative to the CWD), and
  `finalize()` closes and detaches every handler instead of leaking the file
  descriptor / deleting the file.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from data_validate.controllers.context.general_context import GeneralContext

_FILE_LOGGER_NAME = "data_validate_file_logger"


def _make_data_args(mocker, *, locale: str, debug: bool, output_folder: str):
    """Build a minimal fake `DataArgs` with only the attributes `GeneralContext` reads."""
    data_args = mocker.MagicMock()
    data_args.data_file.locale = locale
    data_args.data_file.output_folder = output_folder
    data_args.data_action.debug = debug
    return data_args


@pytest.fixture(autouse=True)
def _isolated_file_logger():
    """Reset the process-wide `data_validate_file_logger` around every test.

    `GeneralContext` always configures the file logger under the same fixed
    name (`logging.getLogger` returns the same singleton for that name across
    the whole test process), so a `disabled`/handler state left over from one
    test would otherwise leak into the next.
    """

    def _reset():
        logger = logging.getLogger(_FILE_LOGGER_NAME)
        logger.disabled = False
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    _reset()
    yield
    _reset()


class TestGeneralContextLogging:
    """Regression tests for BUG-021."""

    def test_debug_false_creates_no_logs_directory_and_disables_logger(self, tmp_cwd: Path, mocker) -> None:
        """Not in debug mode: no `logs/` directory is created anywhere, logger is disabled."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="pt_BR", debug=False, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)

        assert context.logger.disabled is True
        assert context.logger_manager.log_file is None
        # Nothing at all was created under the isolated CWD - not the output
        # folder, not a `logs/` directory relative to the CWD.
        assert list(tmp_cwd.iterdir()) == []

    def test_debug_true_creates_log_file_under_output_folder(self, tmp_cwd: Path, mocker) -> None:
        """In debug mode: the log file is created under `<output_folder>/logs`."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="pt_BR", debug=True, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)

        assert context.logger.disabled is False
        log_file = Path(context.logger_manager.log_file)
        assert log_file.parent == Path(output_folder) / "logs"
        assert log_file.exists()
        assert log_file.suffix == ".log"

    def test_finalize_closes_and_removes_all_handlers_in_debug_mode(self, tmp_cwd: Path, mocker) -> None:
        """`finalize()` closes every handler and leaves `logger.handlers` empty."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="pt_BR", debug=True, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)
        assert context.logger.handlers != []

        context.finalize()

        assert context.logger.handlers == []

    def test_finalize_closes_all_handlers_when_not_debug(self, tmp_cwd: Path, mocker) -> None:
        """`finalize()` also detaches handlers when not in debug mode (no file to delete)."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="pt_BR", debug=False, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)

        context.finalize()

        assert context.logger.handlers == []


class TestGeneralContextLocale:
    """Regression tests for BUG-004/BUG-023: a single locale source of truth."""

    def test_locale_en_us_produces_english_text(self, tmp_cwd: Path, mocker) -> None:
        """`--locale en_US` makes `language_manager.text(...)` return the English string."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="en_US", debug=False, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)

        assert context.language_manager.current_language == "en_US"
        assert context.language_manager.text("fs_utils_error_file_path_empty") == "The file path is empty."

    def test_config_and_file_system_utils_share_the_same_language_manager(self, tmp_cwd: Path, mocker) -> None:
        """`ApplicationConfig` and `FileSystemUtils` receive the exact same `LanguageManager` instance."""
        output_folder = str(tmp_cwd / "out")
        data_args = _make_data_args(mocker, locale="en_US", debug=False, output_folder=output_folder)

        context = GeneralContext(data_args=data_args)

        assert context.config.language_manager is context.language_manager
        assert context.file_system_utils.language_manager is context.language_manager
