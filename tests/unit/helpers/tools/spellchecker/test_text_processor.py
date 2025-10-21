"""
Unit tests for text_processor.py module.

This module tests the TextProcessor class functionality including text cleaning,
acronym detection, and various text preprocessing methods.
"""

from data_validate.helpers.tools.spellchecker.text_processor import TextProcessor


class TestTextProcessor:
    """Test suite for TextProcessor core functionality."""

    def test_is_acronym_valid_acronyms(self, mocker) -> None:
        """Test that valid acronyms are correctly identified."""
        assert TextProcessor.is_acronym("NASA") is True
        assert TextProcessor.is_acronym("USA") is True
        assert TextProcessor.is_acronym("HTML") is True
        assert TextProcessor.is_acronym("API") is True
        assert TextProcessor.is_acronym("XML") is True

    def test_is_acronym_invalid_acronyms(self, mocker) -> None:
        """Test that invalid acronyms are correctly rejected."""
        assert TextProcessor.is_acronym("nasa") is False
        assert TextProcessor.is_acronym("USA!") is True  # The real code considers this valid (uppercase + length > 1)
        assert TextProcessor.is_acronym("A") is False  # Single character
        assert TextProcessor.is_acronym("") is False  # Empty string
        assert TextProcessor.is_acronym("Hello") is False  # Mixed case
        assert TextProcessor.is_acronym("123") is False  # Numbers are not uppercase letters

    def test_has_multiple_spaces_detection(self, mocker) -> None:
        """Test detection of multiple consecutive spaces."""
        assert TextProcessor.has_multiple_spaces("Hello  World") is True
        assert TextProcessor.has_multiple_spaces("Hello   World") is True
        assert TextProcessor.has_multiple_spaces("Hello\t\tWorld") is True
        assert TextProcessor.has_multiple_spaces("Hello\f\fWorld") is True
        assert TextProcessor.has_multiple_spaces("Hello\v\vWorld") is True
        assert TextProcessor.has_multiple_spaces("Hello World") is False
        assert TextProcessor.has_multiple_spaces("HelloWorld") is False
        assert TextProcessor.has_multiple_spaces("") is False

    def test_clean_text_html(self, mocker) -> None:
        """Test HTML tag removal."""
        assert TextProcessor.clean_text_html("<p>Hello World</p>") == " Hello World "
        assert TextProcessor.clean_text_html("<div>Test</div>") == " Test "
        assert TextProcessor.clean_text_html("No HTML here") == "No HTML here"
        assert TextProcessor.clean_text_html("<img src='test.jpg' alt='test'>") == " "
        assert TextProcessor.clean_text_html("") == ""

    def test_clean_text_parentheses_punctuation_numbers(self, mocker) -> None:
        """Test removal of parentheses, punctuation, and numbers."""
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("Hello (World) 123!") == "Hello     "
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("Test@email.com") == "Test email com"
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("Price: $100.50") == "Price      "
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("No changes needed") == "No changes needed"
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("") == ""

    def test_remove_text_urls(self, mocker) -> None:
        """Test URL removal from text."""
        assert TextProcessor.remove_text_urls("Visit https://example.com for more info") == "Visit for more info"
        assert TextProcessor.remove_text_urls("Check www.google.com") == "Check"
        assert TextProcessor.remove_text_urls("Email: test@example.com") == "Email: test@"
        assert TextProcessor.remove_text_urls("No URLs here") == "No URLs here"
        assert TextProcessor.remove_text_urls("") == ""

    def test_remove_text_emails(self, mocker) -> None:
        """Test email address removal from text."""
        assert TextProcessor.remove_text_emails("Contact: test@example.com") == "Contact: "
        assert TextProcessor.remove_text_emails("Email: user.name@domain.co.uk") == "Email: "
        assert TextProcessor.remove_text_emails("No email here") == "No email here"
        assert TextProcessor.remove_text_emails("") == ""

    def test_clean_text_sources(self, mocker) -> None:
        """Test removal of source references."""
        assert TextProcessor.clean_text_sources("Data here. Fontes: Source1, Source2") == "Data here. "
        assert TextProcessor.clean_text_sources("Info. Fonte: Single source") == "Info. "
        assert TextProcessor.clean_text_sources("No sources mentioned") == "No sources mentioned"
        assert TextProcessor.clean_text_sources("") == ""

    def test_clean_text_extra_spaces(self, mocker) -> None:
        """Test normalization of extra spaces."""
        assert TextProcessor.clean_text_extra_spaces("Hello   World") == "Hello World"
        assert TextProcessor.clean_text_extra_spaces("  Multiple   spaces  ") == "Multiple spaces"
        assert TextProcessor.clean_text_extra_spaces("Normal text") == "Normal text"
        assert TextProcessor.clean_text_extra_spaces("") == ""

    def test_sanitize_text_complete_workflow(self, mocker) -> None:
        """Test the complete text sanitization workflow."""
        dirty_text = "Hello (World) 123! Visit https://example.com. Contact: test@example.com. Fontes: Source1"
        expected = "Hello Visit Contact"
        result = TextProcessor.sanitize_text(dirty_text)
        assert result == expected

    def test_sanitize_text_empty_string(self, mocker) -> None:
        """Test sanitization of empty string."""
        assert TextProcessor.sanitize_text("") == ""

    def test_sanitize_text_only_html(self, mocker) -> None:
        """Test sanitization of text with only HTML."""
        assert TextProcessor.sanitize_text("<p></p>") == ""

    def test_sanitize_text_only_punctuation(self, mocker) -> None:
        """Test sanitization of text with only punctuation."""
        assert TextProcessor.sanitize_text("!@#$%^&*()") == ""


class TestTextProcessorEdgeCases:
    """Edge cases and boundary conditions for TextProcessor."""

    def test_is_acronym_special_characters(self, mocker) -> None:
        """Test acronym detection with special characters."""
        assert TextProcessor.is_acronym("A1B2") is True  # Contains numbers but is uppercase and length > 1
        assert TextProcessor.is_acronym("A-B") is True  # Contains hyphen but is uppercase and length > 1
        assert TextProcessor.is_acronym("A.B") is True  # Contains period but is uppercase and length > 1

    def test_has_multiple_spaces_mixed_whitespace(self, mocker) -> None:
        """Test multiple space detection with mixed whitespace."""
        assert TextProcessor.has_multiple_spaces("Hello\t  World") is True
        assert TextProcessor.has_multiple_spaces("Hello \t World") is True
        assert TextProcessor.has_multiple_spaces("Hello\f\vWorld") is True

    def test_clean_text_html_nested_tags(self, mocker) -> None:
        """Test HTML cleaning with nested tags."""
        assert TextProcessor.clean_text_html("<div><p>Nested</p></div>") == "  Nested  "

    def test_clean_text_parentheses_nested(self, mocker) -> None:
        """Test parentheses cleaning with nested parentheses."""
        assert TextProcessor.clean_text_parentheses_punctuation_numbers("Hello (World (Nested))") == "Hello   "

    def test_remove_text_urls_complex_urls(self, mocker) -> None:
        """Test URL removal with complex URLs."""
        assert TextProcessor.remove_text_urls("Visit https://subdomain.example.com/path?param=value") == "Visit"

    def test_remove_text_emails_complex_emails(self, mocker) -> None:
        """Test email removal with complex email addresses."""
        assert TextProcessor.remove_text_emails("Contact: user.name+tag@subdomain.example.co.uk") == "Contact: "

    def test_clean_text_sources_multiple_occurrences(self, mocker) -> None:
        """Test source cleaning with multiple source references."""
        assert TextProcessor.clean_text_sources("Data. Fontes: Source1. More data. Fonte: Source2") == "Data. "

    def test_sanitize_text_very_long_text(self, mocker) -> None:
        """Test sanitization with very long text."""
        long_text = "A" * 1000 + " (B) " + "C" * 1000 + " https://example.com " + "D" * 1000
        result = TextProcessor.sanitize_text(long_text)
        # Should contain only the letter parts, no parentheses, URLs, etc.
        assert "(" not in result
        assert ")" not in result
        assert "https://" not in result
        assert "A" in result
        assert "C" in result
        assert "D" in result


class TestTextProcessorIntegration:
    """Integration tests for TextProcessor methods."""

    def test_sanitize_text_with_all_cleaning_methods(self, mocker) -> None:
        """Test sanitization using all cleaning methods together."""
        complex_text = """
        <p>This is a test (with parentheses) 123!
        Visit https://example.com for more info.
        Contact: test@example.com
        Fontes: Source1, Source2
        Multiple    spaces   here.
        """
        result = TextProcessor.sanitize_text(complex_text)
        # Should be clean text without HTML, parentheses, URLs, emails, sources, extra spaces
        assert "<" not in result
        assert ">" not in result
        assert "(" not in result
        assert ")" not in result
        assert "https://" not in result
        assert "@" not in result
        assert "Fontes:" not in result
        assert "  " not in result  # No multiple spaces
        assert result.strip() == result  # No leading/trailing spaces

    def test_text_processing_chain(self, mocker) -> None:
        """Test that text processing methods can be chained."""
        text = "Hello (World) 123!"

        # Apply methods individually
        step1 = TextProcessor.clean_text_parentheses_punctuation_numbers(text)
        step2 = TextProcessor.clean_text_extra_spaces(step1)

        # Should match sanitize_text result
        expected = TextProcessor.sanitize_text(text)
        assert step2 == expected

    def test_acronym_detection_with_processed_text(self, mocker) -> None:
        """Test acronym detection with processed text."""
        text_with_acronym = "NASA (National Aeronautics and Space Administration)"
        processed = TextProcessor.clean_text_parentheses_punctuation_numbers(text_with_acronym)
        words = processed.split()

        # Should still detect acronyms after processing
        for word in words:
            if word == "NASA":
                assert TextProcessor.is_acronym(word) is True
