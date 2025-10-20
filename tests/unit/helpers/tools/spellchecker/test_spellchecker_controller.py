"""
Unit tests for spellchecker_controller.py module.

This module tests the SpellCheckerController class functionality including
spelling error detection, text quality checking, and dictionary integration.
"""

import pytest

from data_validate.helpers.tools.spellchecker.spellchecker_controller import SpellCheckerController
from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager
from data_validate.helpers.tools.spellchecker.text_processor import TextProcessor


class TestSpellCheckerController:
    """Test suite for SpellCheckerController core functionality."""

    @pytest.fixture
    def mock_dictionary_manager(self, mocker):
        """Create a mock DictionaryManager for testing."""
        return mocker.MagicMock(spec=DictionaryManager)

    @pytest.fixture
    def mock_dictionary(self, mocker):
        """Create a mock dictionary for testing."""
        mock_dict = mocker.MagicMock()
        mock_dict.check.return_value = True
        return mock_dict

    @pytest.fixture
    def spellchecker_controller(self, mock_dictionary_manager) -> SpellCheckerController:
        """Create SpellCheckerController instance for testing."""
        controller = SpellCheckerController(mock_dictionary_manager)
        return controller

    def test_initialization(self, mock_dictionary_manager) -> None:
        """Test SpellCheckerController initialization."""
        controller = SpellCheckerController(mock_dictionary_manager)
        
        assert controller.dictionary_manager == mock_dictionary_manager
        assert isinstance(controller.text_processor, TextProcessor)
        assert controller.dictionary is None

    def test_find_spelling_errors_no_errors(self, spellchecker_controller, mock_dictionary) -> None:
        """Test finding spelling errors when there are no errors."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True
        
        errors = spellchecker_controller.find_spelling_errors("Hello World")
        
        assert errors == []
        assert mock_dictionary.check.call_count == 2  # "Hello" and "World"

    def test_find_spelling_errors_with_errors(self, spellchecker_controller, mock_dictionary) -> None:
        """Test finding spelling errors when there are errors."""
        spellchecker_controller.dictionary = mock_dictionary
        
        # Mock dictionary to return False for "Wrld" (misspelled)
        def mock_check(word):
            return word != "Wrld"
        
        mock_dictionary.check.side_effect = mock_check
        
        errors = spellchecker_controller.find_spelling_errors("Hello Wrld")
        
        assert errors == ["Wrld"]
        assert mock_dictionary.check.call_count == 2

    def test_find_spelling_errors_with_acronyms(self, spellchecker_controller, mock_dictionary) -> None:
        """Test that acronyms are skipped in spelling check."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = False  # All words are "wrong"
        
        errors = spellchecker_controller.find_spelling_errors("NASA Hello")
        
        # "NASA" should be skipped (acronym), only "Hello" should be in errors
        assert errors == ["Hello"]
        # Dictionary should only be called for "Hello", not "NASA"
        mock_dictionary.check.assert_called_once_with("Hello")

    def test_find_spelling_errors_empty_words(self, spellchecker_controller, mock_dictionary) -> None:
        """Test handling of empty words after text processing."""
        spellchecker_controller.dictionary = mock_dictionary
        
        errors = spellchecker_controller.find_spelling_errors("Hello   World")  # Multiple spaces
        
        # Should process "Hello" and "World", skip empty strings
        assert mock_dictionary.check.call_count == 2
        mock_dictionary.check.assert_any_call("Hello")
        mock_dictionary.check.assert_any_call("World")

    def test_find_spelling_errors_empty_text(self, spellchecker_controller, mock_dictionary) -> None:
        """Test handling of empty text."""
        spellchecker_controller.dictionary = mock_dictionary
        
        errors = spellchecker_controller.find_spelling_errors("")
        
        assert errors == []
        mock_dictionary.check.assert_not_called()

    def test_check_text_quality_no_issues(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with no issues."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True
        
        warnings = spellchecker_controller.check_text_quality("Hello World", "column1", 0, "Sheet1")
        
        assert warnings == []

    def test_check_text_quality_multiple_spaces(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with multiple spaces."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True
        
        warnings = spellchecker_controller.check_text_quality("Hello  World", "column1", 0, "Sheet1")
        
        assert len(warnings) == 1
        assert "dois ou mais espaços seguidos" in warnings[0]
        assert "Sheet1" in warnings[0]
        assert "linha 2" in warnings[0]  # row_index + 2
        assert "column1" in warnings[0]

    def test_check_text_quality_spelling_errors(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with spelling errors."""
        spellchecker_controller.dictionary = mock_dictionary
        
        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"
        
        mock_dictionary.check.side_effect = mock_check
        
        warnings = spellchecker_controller.check_text_quality("Hello Wrld", "column1", 1, "Sheet1")
        
        assert len(warnings) == 1
        assert "erros ortográficos" in warnings[0]
        assert "Wrld" in warnings[0]
        assert "Sheet1" in warnings[0]
        assert "linha 3" in warnings[0]  # row_index + 2
        assert "column1" in warnings[0]

    def test_check_text_quality_both_issues(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with both multiple spaces and spelling errors."""
        spellchecker_controller.dictionary = mock_dictionary
        
        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"
        
        mock_dictionary.check.side_effect = mock_check
        
        warnings = spellchecker_controller.check_text_quality("Hello  Wrld", "column1", 2, "Sheet1")
        
        assert len(warnings) == 2
        # Check that both warnings are present
        space_warning = next((w for w in warnings if "espaços seguidos" in w), None)
        spelling_warning = next((w for w in warnings if "erros ortográficos" in w), None)
        
        assert space_warning is not None
        assert spelling_warning is not None

    def test_check_text_quality_with_acronyms(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with acronyms (should not flag as spelling errors)."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = False  # All words are "wrong"
        
        warnings = spellchecker_controller.check_text_quality("NASA Hello", "column1", 0, "Sheet1")
        
        # Should only flag "Hello" as spelling error, not "NASA" (acronym)
        assert len(warnings) == 1
        assert "Hello" in warnings[0]
        assert "NASA" not in warnings[0]

    def test_check_text_quality_empty_text(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with empty text."""
        spellchecker_controller.dictionary = mock_dictionary
        
        warnings = spellchecker_controller.check_text_quality("", "column1", 0, "Sheet1")
        
        assert warnings == []

    def test_check_text_quality_special_characters(self, spellchecker_controller, mock_dictionary) -> None:
        """Test text quality check with special characters."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True
        
        warnings = spellchecker_controller.check_text_quality("Hello! World?", "column1", 0, "Sheet1")
        
        # Should process text normally, special characters handled by text processor
        assert warnings == []


class TestSpellCheckerControllerEdgeCases:
    """Edge cases and boundary conditions for SpellCheckerController."""

    @pytest.fixture
    def mock_dictionary_manager(self, mocker):
        """Create a mock DictionaryManager for testing."""
        return mocker.MagicMock(spec=DictionaryManager)

    @pytest.fixture
    def spellchecker_controller(self, mock_dictionary_manager) -> SpellCheckerController:
        """Create SpellCheckerController instance for testing."""
        return SpellCheckerController(mock_dictionary_manager)

    def test_find_spelling_errors_very_long_text(self, spellchecker_controller, mocker) -> None:
        """Test spelling error detection with very long text."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        # Create very long text
        long_text = "word " * 1000
        
        errors = spellchecker_controller.find_spelling_errors(long_text)
        
        assert errors == []
        assert mock_dictionary.check.call_count == 1000

    def test_find_spelling_errors_unicode_text(self, spellchecker_controller, mocker) -> None:
        """Test spelling error detection with Unicode text."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        errors = spellchecker_controller.find_spelling_errors("Olá Mundo 世界")
        
        assert errors == []
        # Should process Unicode text normally
        assert mock_dictionary.check.call_count == 3  # "Olá", "Mundo", "世界"

    def test_find_spelling_errors_mixed_case_acronyms(self, spellchecker_controller, mocker) -> None:
        """Test spelling error detection with mixed case (not acronyms)."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = False  # All words are "wrong"
        spellchecker_controller.dictionary = mock_dictionary
        
        errors = spellchecker_controller.find_spelling_errors("NASA Hello World")
        
        # "NASA" is acronym (uppercase), should be skipped
        # "Hello" and "World" are not acronyms, should be flagged
        assert "NASA" not in errors
        assert "Hello" in errors
        assert "World" in errors

    def test_check_text_quality_negative_row_index(self, spellchecker_controller, mocker) -> None:
        """Test text quality check with negative row index."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        warnings = spellchecker_controller.check_text_quality("Hello  World", "column1", -1, "Sheet1")
        
        # Should handle negative row index gracefully
        if warnings:  # If there are warnings
            for warning in warnings:
                assert "linha 1" in warning  # -1 + 2 = 1

    def test_check_text_quality_large_row_index(self, spellchecker_controller, mocker) -> None:
        """Test text quality check with large row index."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        warnings = spellchecker_controller.check_text_quality("Hello  World", "column1", 1000000, "Sheet1")
        
        # Should handle large row index
        if warnings:  # If there are warnings
            for warning in warnings:
                assert "linha 1000002" in warning  # 1000000 + 2

    def test_dictionary_not_initialized(self, spellchecker_controller) -> None:
        """Test behavior when dictionary is not initialized."""
        # Don't set spellchecker_controller.dictionary
        
        with pytest.raises(AttributeError):
            spellchecker_controller.find_spelling_errors("Hello World")

    def test_dictionary_check_raises_exception(self, spellchecker_controller, mocker) -> None:
        """Test handling when dictionary.check raises exception."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.side_effect = Exception("Dictionary error")
        spellchecker_controller.dictionary = mock_dictionary
        
        with pytest.raises(Exception, match="Dictionary error"):
            spellchecker_controller.find_spelling_errors("Hello World")


class TestSpellCheckerControllerIntegration:
    """Integration tests for SpellCheckerController."""

    @pytest.fixture
    def mock_dictionary_manager(self, mocker):
        """Create a mock DictionaryManager for testing."""
        return mocker.MagicMock(spec=DictionaryManager)

    @pytest.fixture
    def spellchecker_controller(self, mock_dictionary_manager) -> SpellCheckerController:
        """Create SpellCheckerController instance for testing."""
        return SpellCheckerController(mock_dictionary_manager)

    def test_text_processor_integration(self, spellchecker_controller, mocker) -> None:
        """Test integration with TextProcessor."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        # Test that text processor methods are called
        mock_sanitize = mocker.patch.object(TextProcessor, 'sanitize_text', return_value="Hello World")
        mock_acronym = mocker.patch.object(TextProcessor, 'is_acronym', return_value=False)
        mock_spaces = mocker.patch.object(TextProcessor, 'has_multiple_spaces', return_value=False)
        
        errors = spellchecker_controller.find_spelling_errors("Original Text")
        warnings = spellchecker_controller.check_text_quality("Original Text", "col", 0, "sheet")
        
        # Verify methods were called
        mock_sanitize.assert_called_with("Original Text")
        assert mock_acronym.called
        assert mock_spaces.called

    def test_complete_workflow(self, spellchecker_controller, mocker) -> None:
        """Test complete workflow from text input to warnings output."""
        mock_dictionary = mocker.MagicMock()
        
        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"
        
        mock_dictionary.check.side_effect = mock_check
        spellchecker_controller.dictionary = mock_dictionary
        
        # Test complete workflow
        text = "Hello  Wrld"  # Multiple spaces + spelling error
        warnings = spellchecker_controller.check_text_quality(text, "column1", 0, "Sheet1")
        
        # Should detect both issues
        assert len(warnings) == 2
        space_warning = next((w for w in warnings if "espaços seguidos" in w), None)
        spelling_warning = next((w for w in warnings if "erros ortográficos" in w), None)
        
        assert space_warning is not None
        assert spelling_warning is not None
        assert "Wrld" in spelling_warning

    def test_multiple_text_processing(self, spellchecker_controller, mocker) -> None:
        """Test processing multiple texts in sequence."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary
        
        texts = ["Hello World", "Test Text", "Another Test"]
        all_warnings = []
        
        for i, text in enumerate(texts):
            warnings = spellchecker_controller.check_text_quality(text, f"column{i}", i, "Sheet1")
            all_warnings.extend(warnings)
        
        # All texts should be processed without issues
        assert all_warnings == []
        assert mock_dictionary.check.call_count == 6  # 2 words per text * 3 texts
