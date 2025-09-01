from data_validate.helpers.common.formatting.text_formatting import (
    is_acronym,
    capitalize_text_keep_acronyms
)


class TestTextFormatting:
    """Test cases for text formatting functions."""

    def test_is_acronym(self):
        """Test acronym detection function."""
        # Test valid acronyms
        assert is_acronym("USA") is True
        assert is_acronym("NASA") is True
        assert is_acronym("UN") is True
        assert is_acronym("EU") is True
        assert is_acronym("BR") is True

        # Test non-acronyms
        assert is_acronym("usa") is False  # lowercase
        assert is_acronym("Usa") is False  # mixed case
        assert is_acronym("A") is False    # single character
        assert is_acronym("") is False     # empty string
        assert is_acronym("Hello") is False  # regular word
        assert is_acronym("hello") is False  # lowercase word

    def test_capitalize_text_keep_acronyms(self):
        """Test text capitalization with acronym preservation."""
        # Test simple text
        result = capitalize_text_keep_acronyms("hello world")
        assert result == "Hello world"

        # Test text with acronyms
        result = capitalize_text_keep_acronyms("hello USA world")
        assert result == "Hello USA world"

        result = capitalize_text_keep_acronyms("NASA mission to mars")
        assert result == "NASA mission to mars"

        # Test text with multiple acronyms
        result = capitalize_text_keep_acronyms("USA and EU trade agreement")
        assert result == "USA and EU trade agreement"

        # Test single word
        result = capitalize_text_keep_acronyms("hello")
        assert result == "Hello"

        result = capitalize_text_keep_acronyms("USA")
        assert result == "USA"

        # Test mixed case words
        result = capitalize_text_keep_acronyms("hELLo WoRLd")
        assert result == "Hello world"

        # Test text with acronyms in different positions
        result = capitalize_text_keep_acronyms("welcome to the USA")
        assert result == "Welcome to the USA"

        result = capitalize_text_keep_acronyms("BR is a country")
        assert result == "BR is a country"

        # Test empty string
        result = capitalize_text_keep_acronyms("")
        assert result == ""

        # Test single space
        result = capitalize_text_keep_acronyms(" ")
        assert result == ""  # split() on single space returns empty list

        # Test multiple spaces
        result = capitalize_text_keep_acronyms("  hello  world  ")
        assert result == "Hello world"  # split() removes extra spaces 