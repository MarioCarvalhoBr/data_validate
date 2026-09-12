"""
Unit tests for language_manager.py module.

This module tests the LanguageManager class functionality including
translation loading, language switching, text retrieval, and configuration management.

BUG-004: `LanguageManager` now takes its locale as an explicit constructor argument and
never reads or writes `.config/store.locale` (no file I/O at all for locale resolution).
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from __future__ import annotations

from pathlib import Path

import pytest

from data_validate.helpers.tools.locale.language_enum import LanguageEnum
from data_validate.helpers.tools.locale.language_manager import LanguageManager


class TestLanguageManagerInitialization:
    """Test suite for LanguageManager initialization (BUG-004: explicit locale, no file I/O)."""

    def test_initialization_with_explicit_supported_locale(self, mocker) -> None:
        """A supported, explicitly given locale is used as-is."""
        mock_load = mocker.patch(
            "data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations"
        )

        manager = LanguageManager(locale="en_US")

        assert manager.current_language == "en_US"
        assert manager.default_language == LanguageEnum.DEFAULT_LANGUAGE.value
        assert isinstance(manager.translations, dict)
        mock_load.assert_called_once_with("en_US")

    def test_initialization_with_none_locale_falls_back_to_default(self, mocker) -> None:
        """`locale=None` falls back to `LanguageEnum.DEFAULT_LANGUAGE.value` directly."""
        mock_load = mocker.patch(
            "data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations"
        )

        manager = LanguageManager(locale=None)

        assert manager.current_language == LanguageEnum.DEFAULT_LANGUAGE.value
        mock_load.assert_called_once_with(LanguageEnum.DEFAULT_LANGUAGE.value)

    def test_initialization_with_unsupported_locale_falls_back_to_default(self, mocker) -> None:
        """An explicit but unsupported locale falls back to the default language."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager(locale="fr_FR")

        assert manager.current_language == LanguageEnum.DEFAULT_LANGUAGE.value

    def test_initialization_with_custom_path(self, mocker) -> None:
        """Test LanguageManager initialization with custom locale directory."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        custom_path = "/custom/locales"
        manager = LanguageManager(path_locale_dir=custom_path)

        assert manager.path_locale_dir == custom_path

    def test_initialization_performs_no_file_io_for_locale_resolution(self, tmp_cwd: Path, mocker) -> None:
        """BUG-004: no `.config/store.locale` file or directory is read, written, or created."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        LanguageManager(locale="en_US")
        LanguageManager(locale=None)
        LanguageManager(locale="fr_FR")

        assert not (tmp_cwd / ".config").exists()
        assert list(tmp_cwd.iterdir()) == []

    def test_no_congifure_language_method_left(self) -> None:
        """BUG-024/BUG-004: the typo'd `_congifure_language` helper is gone entirely."""
        assert not hasattr(LanguageManager, "_congifure_language")


class TestLanguageManagerTextRetrieval:
    """Test suite for text retrieval functionality."""

    def test_text_success(self, mocker) -> None:
        """Test successful text retrieval."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": {"message": "Olá"}, "world": {"message": "Mundo"}}

        result = manager.text("hello")
        assert result == "Olá"

    def test_text_with_formatting(self, mocker) -> None:
        """Test text retrieval with formatting."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"greeting": {"message": "Olá {name}, você tem {count} mensagens"}}

        result = manager.text("greeting", name="João", count=5)
        assert result == "Olá João, você tem 5 mensagens"

    def test_text_key_not_found(self, mocker) -> None:
        """Test text retrieval when key is not found."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": {"message": "Olá"}}

        result = manager.text("nonexistent_key")
        assert "missing or invalid structure" in result

    def test_text_invalid_structure(self, mocker) -> None:
        """Test text retrieval with invalid translation structure."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": "invalid_structure"}

        result = manager.text("hello")
        assert "missing or invalid structure" in result

    def test_text_missing_message_key(self, mocker) -> None:
        """Test text retrieval when message key is missing."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": {"other_key": "value"}}

        result = manager.text("hello")
        assert "Message for 'hello' missing" in result


class TestLanguageManagerLanguageManagement:
    """Test suite for language management functionality."""

    def test_set_language_success(self, mocker) -> None:
        """Test successful language setting."""
        mock_load = mocker.patch(
            "data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations"
        )
        mock_load.return_value = True

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]

        result = manager.set_language("en_US")

        assert result is True
        assert manager.current_language == "en_US"

    def test_set_language_unsupported(self, mocker) -> None:
        """Test setting unsupported language."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]
        manager.current_language = "pt_BR"

        result = manager.set_language("fr_FR")

        assert result is False

    def test_get_current_language(self, mocker) -> None:
        """Test getting current language."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "en_US"

        assert manager.get_current_language() == "en_US"

    def test_get_supported_languages(self, mocker) -> None:
        """Test getting supported languages."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]

        assert manager.get_supported_languages() == ["pt_BR", "en_US"]

    def test_get_info(self, mocker) -> None:
        """Test getting language information."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "en_US"
        manager.supported_languages = ["pt_BR", "en_US"]

        info = manager.get_info()

        assert info["current_language"] == "en_US"
        assert info["supported_languages"] == ["pt_BR", "en_US"]


class TestLanguageManagerEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_string_representation(self, mocker) -> None:
        """Test string representation of LanguageManager."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "en_US"
        manager.supported_languages = ["pt_BR", "en_US"]

        str_repr = str(manager)
        assert "LanguageManager" in str_repr
        assert "en_US" in str_repr

    def test_empty_translations(self, mocker) -> None:
        """Test behavior with empty translations."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {}

        result = manager.text("hello")
        assert "missing or invalid structure" in result

    def test_none_translations(self, mocker) -> None:
        """Test behavior with None translations."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = None

        with pytest.raises(AttributeError):
            manager.text("hello")


class TestLanguageManagerIntegration:
    """Integration tests for LanguageManager."""

    def test_multiple_instances_independence(self, mocker) -> None:
        """Test that multiple LanguageManager instances are independent."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager1 = LanguageManager()
        manager2 = LanguageManager()

        manager1.current_language = "en_US"
        manager2.current_language = "pt_BR"

        assert manager1.get_current_language() == "en_US"
        assert manager2.get_current_language() == "pt_BR"

    def test_error_recovery(self, mocker) -> None:
        """Test error recovery scenarios."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]
        manager.translations = {"hello": {"message": "Olá"}}
        manager.current_language = "pt_BR"

        # Test unsupported language
        assert manager.set_language("fr_FR") is False

        # Test missing translation key
        result = manager.text("nonexistent")
        assert "missing or invalid structure" in result


class TestLanguageManagerRealTranslations:
    """End-to-end tests loading the real locale catalogs (no mocking)."""

    def test_real_load_pt_br_default(self) -> None:
        """No locale given loads the real pt_BR catalog."""
        manager = LanguageManager()

        assert manager.current_language == "pt_BR"
        assert manager.translations != {}

    def test_real_load_en_us_locale(self) -> None:
        """An explicit, supported `en_US` locale loads the real en_US catalog."""
        manager = LanguageManager(locale="en_US")

        assert manager.current_language == "en_US"
        assert manager.translations != {}
