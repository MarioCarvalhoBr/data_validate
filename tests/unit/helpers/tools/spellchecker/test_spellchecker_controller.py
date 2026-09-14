"""
Unit tests for spellchecker_controller.py module.

This module tests the SpellCheckerController class functionality including
spelling error detection, text quality evaluation, and dictionary integration.

`format_quality_warnings`/`check_text_quality` (the legacy string-formatting path superseded by
`build_quality_findings`/`rules/spell.py`) were removed as dead code; their tests were rewritten
against `build_quality_findings`, the surviving structured counterpart.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pytest

from data_validate.helpers.tools.spellchecker.spellchecker_controller import SpellCheckerController
from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager
from data_validate.helpers.tools.spellchecker.text_processor import TextProcessor


def _findings_for(controller: SpellCheckerController, text: str, column: str, row_index: int):
    """Evaluate `text` and build its structured findings, mirroring the deleted `check_text_quality`."""
    has_multiple_spaces, spelling_errors = controller.evaluate_text_quality(text)
    return controller.build_quality_findings(has_multiple_spaces, spelling_errors, column, row_index)


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

        spellchecker_controller.find_spelling_errors("Hello   World")  # Multiple spaces

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

    def test_quality_findings_no_issues(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings when there are no quality issues."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True

        findings = _findings_for(spellchecker_controller, "Hello World", "column1", 0)

        assert findings == []

    def test_quality_findings_multiple_spaces(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with multiple spaces."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True

        findings = _findings_for(spellchecker_controller, "Hello  World", "column1", 0)

        assert findings == [(0, "column1", "multiple_spaces", None)]

    def test_quality_findings_spelling_errors(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with spelling errors."""
        spellchecker_controller.dictionary = mock_dictionary

        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"

        mock_dictionary.check.side_effect = mock_check

        findings = _findings_for(spellchecker_controller, "Hello Wrld", "column1", 1)

        assert findings == [(1, "column1", "misspelled_words", ["Wrld"])]

    def test_quality_findings_both_issues(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with both multiple spaces and spelling errors."""
        spellchecker_controller.dictionary = mock_dictionary

        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"

        mock_dictionary.check.side_effect = mock_check

        findings = _findings_for(spellchecker_controller, "Hello  Wrld", "column1", 2)

        assert findings == [
            (2, "column1", "multiple_spaces", None),
            (2, "column1", "misspelled_words", ["Wrld"]),
        ]

    def test_quality_findings_with_acronyms(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with acronyms (should not flag as spelling errors)."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = False  # All words are "wrong"

        findings = _findings_for(spellchecker_controller, "NASA Hello", "column1", 0)

        # Should only flag "Hello" as spelling error, not "NASA" (acronym)
        assert findings == [(0, "column1", "misspelled_words", ["Hello"])]

    def test_quality_findings_empty_text(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with empty text."""
        spellchecker_controller.dictionary = mock_dictionary

        findings = _findings_for(spellchecker_controller, "", "column1", 0)

        assert findings == []

    def test_quality_findings_special_characters(self, spellchecker_controller, mock_dictionary) -> None:
        """Test structured findings with special characters."""
        spellchecker_controller.dictionary = mock_dictionary
        mock_dictionary.check.return_value = True

        findings = _findings_for(spellchecker_controller, "Hello! World?", "column1", 0)

        # Should process text normally, special characters handled by text processor
        assert findings == []


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

        # Create very long text (a single repeated word)
        long_text = "word " * 1000

        errors = spellchecker_controller.find_spelling_errors(long_text)

        assert errors == []
        # PERF-006: the word-level cache means the dictionary is consulted
        # once per unique word, not once per occurrence (would be 1000
        # without the cache).
        assert mock_dictionary.check.call_count == 1

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

    def test_quality_findings_negative_row_index(self, spellchecker_controller, mocker) -> None:
        """Test structured findings with a negative row index (passed through as-is)."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary

        findings = _findings_for(spellchecker_controller, "Hello  World", "column1", -1)

        assert findings == [(-1, "column1", "multiple_spaces", None)]

    def test_quality_findings_large_row_index(self, spellchecker_controller, mocker) -> None:
        """Test structured findings with a large row index (passed through as-is)."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary

        findings = _findings_for(spellchecker_controller, "Hello  World", "column1", 1000000)

        assert findings == [(1000000, "column1", "multiple_spaces", None)]

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
        mock_sanitize = mocker.patch.object(TextProcessor, "sanitize_text", return_value="Hello World")
        mock_acronym = mocker.patch.object(TextProcessor, "is_acronym", return_value=False)
        mock_spaces = mocker.patch.object(TextProcessor, "has_multiple_spaces", return_value=False)

        spellchecker_controller.find_spelling_errors("Original Text")
        spellchecker_controller.evaluate_text_quality("Original Text")

        # Verify methods were called
        mock_sanitize.assert_called_with("Original Text")
        assert mock_acronym.called
        assert mock_spaces.called

    def test_complete_workflow(self, spellchecker_controller, mocker) -> None:
        """Test complete workflow from text input to structured findings output."""
        mock_dictionary = mocker.MagicMock()

        # Mock dictionary to return False for "Wrld"
        def mock_check(word):
            return word != "Wrld"

        mock_dictionary.check.side_effect = mock_check
        spellchecker_controller.dictionary = mock_dictionary

        # Test complete workflow
        text = "Hello  Wrld"  # Multiple spaces + spelling error
        findings = _findings_for(spellchecker_controller, text, "column1", 0)

        # Should detect both issues
        assert findings == [
            (0, "column1", "multiple_spaces", None),
            (0, "column1", "misspelled_words", ["Wrld"]),
        ]

    def test_multiple_text_processing(self, spellchecker_controller, mocker) -> None:
        """Test processing multiple texts in sequence."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary

        texts = ["Hello World", "Test Text", "Another Test"]
        all_findings = []

        for i, text in enumerate(texts):
            all_findings.extend(_findings_for(spellchecker_controller, text, f"column{i}", i))

        # All texts should be processed without issues
        assert all_findings == []
        # PERF-006: "Test" repeats between "Test Text" and "Another Test",
        # so the word-level cache means it is only checked once — 5 unique
        # words (Hello, World, Test, Text, Another), not 6 occurrences.
        assert mock_dictionary.check.call_count == 5


class TestSpellCheckerControllerCaching:
    """PERF-006 regression tests: word-level check-call caching."""

    @pytest.fixture
    def mock_dictionary_manager(self, mocker):
        """Create a mock DictionaryManager for testing."""
        return mocker.MagicMock(spec=DictionaryManager)

    @pytest.fixture
    def spellchecker_controller(self, mock_dictionary_manager) -> SpellCheckerController:
        """Create SpellCheckerController instance for testing."""
        return SpellCheckerController(mock_dictionary_manager)

    def test_find_spelling_errors_calls_dictionary_once_per_unique_word(self, spellchecker_controller, mocker) -> None:
        """A counting fake in place of enchant's Dict shows one call per unique word.

        Before PERF-006 this counted one call per occurrence (4 calls for
        4 repetitions of "dado"); the cache brings it down to one call per
        unique word.
        """

        class CountingFakeDict:
            def __init__(self) -> None:
                self.calls = 0

            def check(self, word: str) -> bool:
                self.calls += 1
                return True

        counting_dict = CountingFakeDict()
        spellchecker_controller.dictionary = counting_dict

        spellchecker_controller.find_spelling_errors("dado dado disponivel dado")

        assert counting_dict.calls == 2  # only "dado" and "disponivel" are unique

    def test_find_spelling_errors_cache_persists_across_calls(self, spellchecker_controller, mocker) -> None:
        """The word cache is not cleared between calls within the same controller instance."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.return_value = True
        spellchecker_controller.dictionary = mock_dictionary

        spellchecker_controller.find_spelling_errors("Hello World")
        spellchecker_controller.find_spelling_errors("Hello Test")

        # "Hello" is cached after the first call; only "World" and "Test" are new
        assert mock_dictionary.check.call_count == 3
        assert spellchecker_controller._check_cache == {"Hello": True, "World": True, "Test": True}

    def test_find_spelling_errors_cache_records_misspelled_words_too(self, spellchecker_controller, mocker) -> None:
        """The cache stores both hits and misses, so a repeated misspelling is still cached."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.side_effect = lambda word: word != "Wrld"
        spellchecker_controller.dictionary = mock_dictionary

        errors = spellchecker_controller.find_spelling_errors("Wrld Wrld Wrld")

        assert errors == ["Wrld", "Wrld", "Wrld"]
        mock_dictionary.check.assert_called_once_with("Wrld")


class TestSpellCheckerControllerQualityEvaluation:
    """Tests for the `evaluate_text_quality`/`build_quality_findings` split (PERF-006, ARC-017 Phase 3 Port 8)."""

    @pytest.fixture
    def mock_dictionary_manager(self, mocker):
        """Create a mock DictionaryManager for testing."""
        return mocker.MagicMock(spec=DictionaryManager)

    @pytest.fixture
    def spellchecker_controller(self, mock_dictionary_manager) -> SpellCheckerController:
        """Create SpellCheckerController instance for testing."""
        return SpellCheckerController(mock_dictionary_manager)

    def test_evaluate_text_quality_returns_signals_only(self, spellchecker_controller, mocker) -> None:
        """`evaluate_text_quality` is row-independent: no column/row/sheet arguments."""
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.check.side_effect = lambda word: word != "Wrld"
        spellchecker_controller.dictionary = mock_dictionary

        has_multiple_spaces, spelling_errors = spellchecker_controller.evaluate_text_quality("Hello  Wrld")

        assert has_multiple_spaces is True
        assert spelling_errors == ["Wrld"]

    def test_build_quality_findings_builds_row_specific_findings(self, spellchecker_controller) -> None:
        """`build_quality_findings` renders precomputed signals for a specific row."""
        findings = spellchecker_controller.build_quality_findings(True, ["Wrld"], "column1", 2)

        assert findings == [
            (2, "column1", "multiple_spaces", None),
            (2, "column1", "misspelled_words", ["Wrld"]),
        ]

    def test_build_quality_findings_no_issues_returns_empty_list(self, spellchecker_controller) -> None:
        """`build_quality_findings` returns no findings when both signals are clean."""
        findings = spellchecker_controller.build_quality_findings(False, [], "column1", 0)

        assert findings == []
