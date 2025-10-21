"""
Unit tests for language_manager.py module.

This module tests the LanguageManager class functionality including
translation loading, language switching, text retrieval, and configuration management.
"""

import pytest

from data_validate.helpers.tools.locale.language_enum import LanguageEnum
from data_validate.helpers.tools.locale.language_manager import LanguageManager


class TestLanguageManagerInitialization:
    """Test suite for LanguageManager initialization."""

    def test_initialization_creates_manager(self, mocker) -> None:
        """Test that LanguageManager can be initialized."""
        mock_configure = mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mock_load = mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()

        assert manager.default_language == LanguageEnum.DEFAULT_LANGUAGE.value
        assert isinstance(manager.translations, dict)
        mock_configure.assert_called_once()
        mock_load.assert_called_once()

    def test_initialization_with_custom_path(self, mocker) -> None:
        """Test LanguageManager initialization with custom locale directory."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        custom_path = "/custom/locales"
        manager = LanguageManager(path_locale_dir=custom_path)

        assert manager.path_locale_dir == custom_path


class TestLanguageManagerTextRetrieval:
    """Test suite for text retrieval functionality."""

    def test_text_success(self, mocker) -> None:
        """Test successful text retrieval."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": {"message": "Olá"}, "world": {"message": "Mundo"}}

        result = manager.text("hello")
        assert result == "Olá"

    def test_text_with_formatting(self, mocker) -> None:
        """Test text retrieval with formatting."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"greeting": {"message": "Olá {name}, você tem {count} mensagens"}}

        result = manager.text("greeting", name="João", count=5)
        assert result == "Olá João, você tem 5 mensagens"

    def test_text_key_not_found(self, mocker) -> None:
        """Test text retrieval when key is not found."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": {"message": "Olá"}}

        result = manager.text("nonexistent_key")
        assert "missing or invalid structure" in result

    def test_text_invalid_structure(self, mocker) -> None:
        """Test text retrieval with invalid translation structure."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {"hello": "invalid_structure"}

        result = manager.text("hello")
        assert "missing or invalid structure" in result

    def test_text_missing_message_key(self, mocker) -> None:
        """Test text retrieval when message key is missing."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
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
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mock_load = mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")
        mock_load.return_value = True

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]

        result = manager.set_language("en_US")

        assert result is True
        assert manager.current_language == "en_US"

    def test_set_language_unsupported(self, mocker) -> None:
        """Test setting unsupported language."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]
        manager.current_language = "pt_BR"

        result = manager.set_language("fr_FR")

        assert result is False

    def test_get_current_language(self, mocker) -> None:
        """Test getting current language."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "en_US"

        assert manager.get_current_language() == "en_US"

    def test_get_supported_languages(self, mocker) -> None:
        """Test getting supported languages."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.supported_languages = ["pt_BR", "en_US"]

        assert manager.get_supported_languages() == ["pt_BR", "en_US"]

    def test_get_info(self, mocker) -> None:
        """Test getting language information."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
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
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "en_US"
        manager.supported_languages = ["pt_BR", "en_US"]

        str_repr = str(manager)
        assert "LanguageManager" in str_repr
        assert "en_US" in str_repr

    def test_empty_translations(self, mocker) -> None:
        """Test behavior with empty translations."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager = LanguageManager()
        manager.current_language = "pt_BR"
        manager.translations = {}

        result = manager.text("hello")
        assert "missing or invalid structure" in result

    def test_none_translations(self, mocker) -> None:
        """Test behavior with None translations."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
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
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._load_translations")

        manager1 = LanguageManager()
        manager2 = LanguageManager()

        manager1.current_language = "en_US"
        manager2.current_language = "pt_BR"

        assert manager1.get_current_language() == "en_US"
        assert manager2.get_current_language() == "pt_BR"

    def test_error_recovery(self, mocker) -> None:
        """Test error recovery scenarios."""
        mocker.patch("data_validate.helpers.tools.locale.language_manager.LanguageManager._congifure_language")
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
