"""Tests for application_config.py module."""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from datetime import datetime
from types import MappingProxyType

from data_validate.config.application_config import ApplicationConfig
from data_validate.config.names_enum import NamesEnum


class TestApplicationConfigClock:
    """Regression tests for BUG-011: CURRENT_YEAR/DATE_NOW must be computed per instance."""

    def test_current_year_and_date_now_use_injected_clock(self) -> None:
        """Two instances built with different fake clocks report different values.

        This pins the fix: before BUG-011, `CURRENT_YEAR`/`DATE_NOW` were class
        attributes computed once at import time, so no per-instance clock could
        influence them. Under the fix, each instance's clock is honoured.
        """
        fixed_past = datetime(2001, 1, 2, 3, 4, 5)
        fixed_future = datetime(2099, 12, 31, 23, 59, 59)

        config_past = ApplicationConfig(clock=lambda: fixed_past)
        config_future = ApplicationConfig(clock=lambda: fixed_future)

        assert config_past.CURRENT_YEAR == 2001
        assert config_past.DATE_NOW == "02/01/2001 03:04:05"

        assert config_future.CURRENT_YEAR == 2099
        assert config_future.DATE_NOW == "31/12/2099 23:59:59"

        # The two instances must diverge - proof the value is not a shared
        # class-level constant computed once at import time.
        assert config_past.CURRENT_YEAR != config_future.CURRENT_YEAR
        assert config_past.DATE_NOW != config_future.DATE_NOW

    def test_default_construction_matches_real_clock(self) -> None:
        """Default construction (no injected clock) still uses `datetime.now`."""
        config = ApplicationConfig()

        assert config.CURRENT_YEAR == datetime.now().year
        assert isinstance(config.DATE_NOW, str)
        # Format is fixed: dd/mm/yyyy HH:MM:SS.
        datetime.strptime(config.DATE_NOW, "%d/%m/%Y %H:%M:%S")

    def test_get_verify_names_returns_all_titles(self, mocker) -> None:
        """`get_verify_names()` still returns a localized title per `NamesEnum` member.

        Also documents the `TITLES_N`/`SIMP_DESC_N` interpolation: those two keys
        are looked up with a `value=` kwarg (the character-limit constants),
        every other key is looked up with no extra kwargs.
        """
        mock_language_manager_cls = mocker.patch(
            "data_validate.config.application_config.LanguageManager",
        )
        mock_language_manager = mock_language_manager_cls.return_value
        mock_language_manager.text.side_effect = lambda key, value=None: f"{key}:{value}"

        config = ApplicationConfig(clock=lambda: datetime(2024, 1, 1))
        verify_names = config.get_verify_names()

        assert isinstance(verify_names, MappingProxyType)
        assert len(verify_names) == len(NamesEnum)
        assert set(verify_names.keys()) == {element.value for element in NamesEnum}

        # TITLES_N and SIMP_DESC_N are interpolated with the configured limits.
        assert verify_names[NamesEnum.TITLES_N.value] == f"{NamesEnum.TITLES_N.value}:{config.TITLE_OVER_N_CHARS}"
        assert (
            verify_names[NamesEnum.SIMP_DESC_N.value]
            == f"{NamesEnum.SIMP_DESC_N.value}:{config.SIMPLE_DESCRIPTIONS_OVER_N_CHARS}"
        )

        # Every other key is looked up without a value kwarg.
        other_key = NamesEnum.FS.value
        assert verify_names[other_key] == f"{other_key}:None"

    def test_get_verify_names_caches_after_first_call(self, mocker) -> None:
        """PERF-004: a second `get_verify_names()` call must not re-hit the catalog.

        `base_validator.py` calls `get_verify_names()` once per validator and
        `FileReportGenerator` calls it twice more per run, so without caching
        the same `len(NamesEnum)` lookups repeat on every call. Calling it twice
        here must still only cost `len(NamesEnum)` `LanguageManager.text` calls in
        total (not double that).
        """
        mock_language_manager_cls = mocker.patch(
            "data_validate.config.application_config.LanguageManager",
        )
        mock_language_manager = mock_language_manager_cls.return_value
        mock_language_manager.text.side_effect = lambda key, value=None: f"{key}:{value}"

        config = ApplicationConfig(clock=lambda: datetime(2024, 1, 1))

        first_result = config.get_verify_names()
        assert mock_language_manager.text.call_count == len(NamesEnum)

        second_result = config.get_verify_names()
        assert mock_language_manager.text.call_count == len(NamesEnum)

        assert second_result is first_result


class TestApplicationConfigLanguageManagerInjection:
    """Regression tests for ARC-002/BUG-004/BUG-023: a single injected `LanguageManager`."""

    def test_injected_language_manager_is_used_as_is(self, mocker) -> None:
        """When a `language_manager` is given, no new instance is built internally."""
        mock_language_manager_cls = mocker.patch("data_validate.config.application_config.LanguageManager")
        shared_language_manager = mocker.MagicMock()

        config = ApplicationConfig(language_manager=shared_language_manager)

        assert config.language_manager is shared_language_manager
        mock_language_manager_cls.assert_not_called()

    def test_default_construction_builds_its_own_language_manager(self, mocker) -> None:
        """Backwards compatibility: no `language_manager` given builds a default one."""
        mock_language_manager_cls = mocker.patch("data_validate.config.application_config.LanguageManager")

        config = ApplicationConfig()

        mock_language_manager_cls.assert_called_once_with()
        assert config.language_manager is mock_language_manager_cls.return_value
