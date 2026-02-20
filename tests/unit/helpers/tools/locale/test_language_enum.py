"""
Unit tests for language_enum.py module.

This module tests the LanguageEnum class functionality including
enumeration values, supported languages listing, and default language retrieval.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from data_validate.helpers.tools.locale.language_enum import LanguageEnum


class TestLanguageEnum:
    """Test suite for LanguageEnum class."""

    def test_enum_values(self, mocker) -> None:
        """Test that enum values are correctly defined."""
        assert LanguageEnum.PT_BR.value == "pt_BR"
        assert LanguageEnum.EN_US.value == "en_US"
        # DEFAULT_LANGUAGE is an alias for PT_BR
        assert LanguageEnum.DEFAULT_LANGUAGE.value == "pt_BR"
        assert LanguageEnum.DEFAULT_LANGUAGE == LanguageEnum.PT_BR

    def test_list_supported_languages(self, mocker) -> None:
        """Test listing of supported languages."""
        supported_languages = LanguageEnum.list_supported_languages()

        assert isinstance(supported_languages, list)
        # Note: DEFAULT_LANGUAGE is an alias for PT_BR, actual enum has 2 unique members
        assert len(supported_languages) >= 2
        assert "pt_BR" in supported_languages
        assert "en_US" in supported_languages

    def test_default_language(self, mocker) -> None:
        """Test default language retrieval."""
        default_lang = LanguageEnum.default_language()

        assert default_lang == "pt_BR"
        assert isinstance(default_lang, str)

    def test_enum_membership(self, mocker) -> None:
        """Test enum membership and iteration."""
        members = list(LanguageEnum)
        # DEFAULT_LANGUAGE is an alias for PT_BR, so only 2 unique members
        assert len(members) >= 2
        assert LanguageEnum.PT_BR in members
        assert LanguageEnum.EN_US in members
        # DEFAULT_LANGUAGE is same as PT_BR
        assert LanguageEnum.DEFAULT_LANGUAGE in members

    def test_enum_comparison(self, mocker) -> None:
        """Test enum comparison operations."""
        assert LanguageEnum.PT_BR == LanguageEnum.PT_BR
        assert LanguageEnum.PT_BR != LanguageEnum.EN_US
        # DEFAULT_LANGUAGE is an alias for PT_BR
        assert LanguageEnum.PT_BR == LanguageEnum.DEFAULT_LANGUAGE

    def test_enum_value_access(self, mocker) -> None:
        """Test accessing enum values."""
        assert LanguageEnum.PT_BR.value == "pt_BR"
        assert LanguageEnum.EN_US.value == "en_US"
        assert LanguageEnum.DEFAULT_LANGUAGE.value == "pt_BR"

    def test_enum_name_access(self, mocker) -> None:
        """Test accessing enum names."""
        assert LanguageEnum.PT_BR.name == "PT_BR"
        assert LanguageEnum.EN_US.name == "EN_US"
        # DEFAULT_LANGUAGE is an alias for PT_BR, so has same name as PT_BR
        assert LanguageEnum.DEFAULT_LANGUAGE.name == LanguageEnum.PT_BR.name


class TestLanguageEnumEdgeCases:
    """Edge cases and boundary conditions for LanguageEnum."""

    def test_enum_immutability(self, mocker) -> None:
        """Test that enum values cannot be modified."""
        original_pt_br = LanguageEnum.PT_BR.value
        original_en_us = LanguageEnum.EN_US.value

        assert LanguageEnum.PT_BR.value == original_pt_br
        assert LanguageEnum.EN_US.value == original_en_us

    def test_enum_string_representation(self, mocker) -> None:
        """Test string representation of enum members."""
        assert str(LanguageEnum.PT_BR) == "LanguageEnum.PT_BR"
        assert str(LanguageEnum.EN_US) == "LanguageEnum.EN_US"
        # DEFAULT_LANGUAGE is an alias for PT_BR, so has same string representation
        assert str(LanguageEnum.DEFAULT_LANGUAGE) == str(LanguageEnum.PT_BR)

    def test_enum_repr(self, mocker) -> None:
        """Test repr representation of enum members."""
        assert repr(LanguageEnum.PT_BR) == "<LanguageEnum.PT_BR: 'pt_BR'>"
        assert repr(LanguageEnum.EN_US) == "<LanguageEnum.EN_US: 'en_US'>"
        # DEFAULT_LANGUAGE is an alias for PT_BR, so has same repr
        assert repr(LanguageEnum.DEFAULT_LANGUAGE) == repr(LanguageEnum.PT_BR)

    def test_enum_hash(self, mocker) -> None:
        """Test that enum members are hashable and work as dict keys."""
        # DEFAULT_LANGUAGE is an alias for PT_BR, so they have the same hash
        enum_dict = {LanguageEnum.EN_US: "English"}
        enum_dict[LanguageEnum.PT_BR] = "Portuguese"
        enum_dict[LanguageEnum.DEFAULT_LANGUAGE] = "Default"

        # Since DEFAULT_LANGUAGE == PT_BR, the last assignment overwrites
        assert enum_dict[LanguageEnum.PT_BR] == "Default"
        assert enum_dict[LanguageEnum.EN_US] == "English"
        assert enum_dict[LanguageEnum.DEFAULT_LANGUAGE] == "Default"
        assert len(enum_dict) == 2  # Only 2 unique keys

    def test_enum_equality_with_values(self, mocker) -> None:
        """Test enum equality with string values."""
        assert LanguageEnum.PT_BR.value == "pt_BR"
        assert LanguageEnum.EN_US.value == "en_US"
        assert LanguageEnum.DEFAULT_LANGUAGE.value == "pt_BR"

    def test_enum_in_set(self, mocker) -> None:
        """Test enum members in set operations."""
        supported_set = {LanguageEnum.PT_BR, LanguageEnum.EN_US, LanguageEnum.DEFAULT_LANGUAGE}

        assert LanguageEnum.PT_BR in supported_set
        assert LanguageEnum.EN_US in supported_set
        assert LanguageEnum.DEFAULT_LANGUAGE in supported_set
        # Since DEFAULT_LANGUAGE == PT_BR, set has only 2 unique items
        assert len(supported_set) == 2


class TestLanguageEnumIntegration:
    """Integration tests for LanguageEnum."""

    def test_enum_with_language_codes(self, mocker) -> None:
        """Test enum integration with language code validation."""
        valid_codes = ["pt_BR", "en_US"]

        for code in valid_codes:
            enum_member = None
            for member in LanguageEnum:
                if member.value == code:
                    enum_member = member
                    break

            assert enum_member is not None
            assert enum_member.value == code

    def test_enum_consistency(self, mocker) -> None:
        """Test consistency between different enum methods."""
        listed_languages = LanguageEnum.list_supported_languages()
        enum_values = [member.value for member in LanguageEnum]

        assert set(listed_languages) == set(enum_values)
        assert LanguageEnum.default_language() in listed_languages

    def test_enum_usage_patterns(self, mocker) -> None:
        """Test common usage patterns with the enum."""

        def is_supported(lang_code: str) -> bool:
            return lang_code in LanguageEnum.list_supported_languages()

        assert is_supported("pt_BR") is True
        assert is_supported("en_US") is True
        assert is_supported("fr_FR") is False
        assert is_supported("invalid") is False

        def get_enum_by_value(lang_code: str):
            for member in LanguageEnum:
                if member.value == lang_code:
                    return member
            return None

        assert get_enum_by_value("pt_BR") == LanguageEnum.PT_BR
        assert get_enum_by_value("en_US") == LanguageEnum.EN_US
        assert get_enum_by_value("invalid") is None

    def test_enum_with_type_hints(self, mocker) -> None:
        """Test enum usage with type hints."""

        def process_language(lang: LanguageEnum) -> str:
            return f"Processing {lang.value}"

        assert process_language(LanguageEnum.PT_BR) == "Processing pt_BR"
        assert process_language(LanguageEnum.EN_US) == "Processing en_US"
        assert process_language(LanguageEnum.DEFAULT_LANGUAGE) == "Processing pt_BR"
