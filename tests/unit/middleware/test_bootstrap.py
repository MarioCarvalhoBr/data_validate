#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for the `Bootstrap` class (middleware/bootstrap.py).

Covers BUG-008 (argument-check ordering and the removal of the
single-task `ThreadPoolExecutor`) and the locale persistence behaviour of
`_check_and_set_locale`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from data_validate.helpers.base.data_args import DataArgs
from data_validate.helpers.tools.locale.language_enum import LanguageEnum
from data_validate.middleware.bootstrap import Bootstrap


def _make_bootstrap(tmp_path: Path) -> Bootstrap:
    """Build a `Bootstrap` instance without running `__init__`'s side effects.

    Args:
        tmp_path: Isolated temporary directory used for the config dir.

    Returns:
        Bootstrap: An instance with `config_dir`/`locale_file`/`default_locale`
            set, but without having called `run()`.
    """
    instance = Bootstrap.__new__(Bootstrap)
    instance.config_dir = str(tmp_path / ".config")
    instance.locale_file = os.path.join(instance.config_dir, "store.locale")
    instance.default_locale = LanguageEnum.DEFAULT_LANGUAGE.value
    return instance


class TestBootstrapRunArgumentOrder:
    """Regression tests for BUG-008: argument-check ordering."""

    def test_run_with_none_raises_value_error(self, tmp_cwd: Path) -> None:
        """`run(None)` must raise `ValueError`, not `TypeError`."""
        bootstrap = _make_bootstrap(tmp_cwd)

        with pytest.raises(ValueError, match="cannot be None"):
            bootstrap.run(None)

    def test_run_with_non_dataargs_raises_type_error(self, tmp_cwd: Path) -> None:
        """A non-`None`, non-`DataArgs` value must raise `TypeError`."""
        bootstrap = _make_bootstrap(tmp_cwd)

        with pytest.raises(TypeError, match="must be an instance of the DataArgs class"):
            bootstrap.run("not-a-data-args-instance")

    def test_run_with_valid_dataargs_calls_check_and_set_locale_once(self, tmp_cwd: Path, mocker) -> None:
        """A valid `DataArgs` must call `_check_and_set_locale` exactly once, directly (no executor)."""
        bootstrap = _make_bootstrap(tmp_cwd)
        mock_check_and_set_locale = mocker.patch.object(bootstrap, "_check_and_set_locale")

        args = DataArgs.__new__(DataArgs)
        args.data_file = mocker.MagicMock(locale="en_US")

        bootstrap.run(args)

        mock_check_and_set_locale.assert_called_once_with("en_US")

    def test_bootstrap_init_calls_check_and_set_locale_once(self, tmp_cwd: Path, mocker) -> None:
        """`Bootstrap(args)` must delegate to `_check_and_set_locale` exactly once."""
        mock_check_and_set_locale = mocker.patch.object(Bootstrap, "_check_and_set_locale")

        args = DataArgs.__new__(DataArgs)
        args.data_file = mocker.MagicMock(locale="pt_BR")

        Bootstrap(args)

        mock_check_and_set_locale.assert_called_once_with("pt_BR")


class TestBootstrapCheckAndSetLocale:
    """Coverage for `_check_and_set_locale`'s locale-resolution paths."""

    def test_valid_locale_is_persisted_to_file(self, tmp_cwd: Path) -> None:
        """A supported locale is written verbatim to `store.locale`."""
        bootstrap = _make_bootstrap(tmp_cwd)

        bootstrap._check_and_set_locale("en_US")

        assert Path(bootstrap.locale_file).read_text(encoding="utf-8") == "en_US"

    def test_invalid_locale_raises_value_error(self, tmp_cwd: Path) -> None:
        """An unsupported locale raises `ValueError` and writes nothing."""
        bootstrap = _make_bootstrap(tmp_cwd)

        with pytest.raises(ValueError, match="Invalid locale"):
            bootstrap._check_and_set_locale("fr_FR")

        assert not os.path.exists(bootstrap.locale_file)

    def test_absent_locale_without_existing_file_falls_back_to_default(self, tmp_cwd: Path) -> None:
        """No locale argument and no existing file: fall back to the default."""
        bootstrap = _make_bootstrap(tmp_cwd)

        bootstrap._check_and_set_locale(None)

        assert Path(bootstrap.locale_file).read_text(encoding="utf-8") == bootstrap.default_locale

    def test_absent_locale_with_valid_existing_file_keeps_it(self, tmp_cwd: Path) -> None:
        """No locale argument but a valid existing file: keep the stored value."""
        bootstrap = _make_bootstrap(tmp_cwd)
        Path(bootstrap.config_dir).mkdir(parents=True, exist_ok=True)
        with open(bootstrap.locale_file, "w", encoding="utf-8") as f:
            f.write("en_US")

        bootstrap._check_and_set_locale(None)

        assert Path(bootstrap.locale_file).read_text(encoding="utf-8") == "en_US"

    def test_absent_locale_with_invalid_existing_file_falls_back_to_default(self, tmp_cwd: Path) -> None:
        """No locale argument but an invalid existing file: overwrite with the default."""
        bootstrap = _make_bootstrap(tmp_cwd)
        Path(bootstrap.config_dir).mkdir(parents=True, exist_ok=True)
        with open(bootstrap.locale_file, "w", encoding="utf-8") as f:
            f.write("xx_XX")

        bootstrap._check_and_set_locale(None)

        assert Path(bootstrap.locale_file).read_text(encoding="utf-8") == bootstrap.default_locale
