from data_validate.helpers.common.formatting.text_formatting_processing import TextFormattingProcessing


class TestTextFormatting:
    """Test cases for text formatting functions."""

    def test_is_acronym(self):
        """Test acronym detection function."""
        # Test valid acronyms
        assert TextFormattingProcessing.is_acronym("USA") is True
        assert TextFormattingProcessing.is_acronym("NASA") is True
        assert TextFormattingProcessing.is_acronym("UN") is True
        assert TextFormattingProcessing.is_acronym("EU") is True
        assert TextFormattingProcessing.is_acronym("BR") is True

        # Test non-acronyms
        assert TextFormattingProcessing.is_acronym("usa") is False  # lowercase
        assert TextFormattingProcessing.is_acronym("Usa") is False  # mixed case
        assert TextFormattingProcessing.is_acronym("A") is False  # single character
        assert TextFormattingProcessing.is_acronym("") is False  # empty string
        assert TextFormattingProcessing.is_acronym("Hello") is False  # regular word
        assert TextFormattingProcessing.is_acronym("hello") is False  # lowercase word

    def test_capitalize_text_keep_acronyms(self):
        """Test text capitalization with acronym preservation."""
        # Test simple text
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("hello world")
        assert result == "Hello world"

        # Test text with acronyms
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("hello USA world")
        assert result == "Hello USA world"

        result = TextFormattingProcessing.capitalize_text_keep_acronyms("NASA mission to mars")
        assert result == "NASA mission to mars"

        # Test text with multiple acronyms
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("USA and EU trade agreement")
        assert result == "USA and EU trade agreement"

        # Test single word
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("hello")
        assert result == "Hello"

        result = TextFormattingProcessing.capitalize_text_keep_acronyms("USA")
        assert result == "USA"

        # Test mixed case words
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("hELLo WoRLd")
        assert result == "Hello world"

        # Test text with acronyms in different positions
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("welcome to the USA")
        assert result == "Welcome to the USA"

        result = TextFormattingProcessing.capitalize_text_keep_acronyms("BR is a country")
        assert result == "BR is a country"

        # Test empty string
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("")
        assert result == ""

        # Test single space
        result = TextFormattingProcessing.capitalize_text_keep_acronyms(" ")
        assert result == ""  # split() on single space returns empty list

        # Test multiple spaces
        result = TextFormattingProcessing.capitalize_text_keep_acronyms("  hello  world  ")
        assert result == "Hello world"  # split() removes extra spaces
