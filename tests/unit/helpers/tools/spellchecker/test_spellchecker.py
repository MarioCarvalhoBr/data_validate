"""
Unit tests for spellchecker.py module.

This module tests the SpellChecker service class construction and collaborator wiring.
`check_spelling_text` (the legacy string-returning API) was deleted as dead production code
(ARC-005/SEC-004, Phase 5): only `check_spelling_text_structured` is called by
`rules/spell.py`; see `test_check_spelling_text_structured` below for its coverage.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd

from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker, SpellingFinding


class TestSpellChecker:
    """Test suite for SpellChecker service class construction."""

    def test_initialization(self, mocker) -> None:
        """Test SpellChecker initialization with default parameters."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mock_spellchecker_controller,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mock_dataframe_processor,
        )

        spellchecker = SpellChecker("pt_BR", ["word1", "word2"])

        assert spellchecker.lang_dict_spell == "pt_BR"
        assert spellchecker.list_words_user == ["word1", "word2"]
        assert spellchecker.dictionary_manager == mock_dictionary_manager
        assert spellchecker.spell_checker_controller == mock_spellchecker_controller
        assert spellchecker.df_processor == mock_dataframe_processor

    def test_initialization_with_none_words(self, mocker) -> None:
        """Test SpellChecker initialization with None words."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mock_spellchecker_controller,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mock_dataframe_processor,
        )

        spellchecker = SpellChecker("pt_BR", None)

        assert spellchecker.list_words_user == []

    def test_initialization_with_empty_words(self, mocker) -> None:
        """Test SpellChecker initialization with empty words list."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mock_spellchecker_controller,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mock_dataframe_processor,
        )

        spellchecker = SpellChecker("pt_BR", [])

        assert spellchecker.list_words_user == []

    def test_initialization_collects_dictionary_validation_errors(self, mocker) -> None:
        """`_prepare_statement` surfaces `validate_dictionary`'s errors on `errors_dictionary`."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = ["Dictionary error"]

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mocker.MagicMock()
        )

        spellchecker = SpellChecker("pt_BR", ["word1"])

        assert spellchecker.errors_dictionary == ["Dictionary error"]

    def test_clean_files_generated_delegates_to_dictionary_manager(self, mocker) -> None:
        """`clean_files_generated` forwards to the dictionary manager's own cleanup."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mocker.MagicMock()
        )

        spellchecker = SpellChecker("pt_BR", ["word1"])
        spellchecker.clean_files_generated()

        mock_dictionary_manager.clean_temporary_files.assert_called_once()


class TestSpellCheckerEdgeCases:
    """Edge cases and boundary conditions for SpellChecker construction."""

    def test_initialization_with_different_languages(self, mocker) -> None:
        """Test initialization with different language codes."""
        languages = ["en_US", "es_ES", "fr_FR", "de_DE"]

        for lang in languages:
            mock_dictionary_manager = mocker.MagicMock()
            mock_spellchecker_controller = mocker.MagicMock()
            mock_dataframe_processor = mocker.MagicMock()

            mocker.patch(
                "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
                return_value=mock_dictionary_manager,
            )
            mocker.patch(
                "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
                return_value=mock_spellchecker_controller,
            )
            mocker.patch(
                "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
                return_value=mock_dataframe_processor,
            )

            spellchecker = SpellChecker(lang, ["word1"])
            assert spellchecker.lang_dict_spell == lang


class TestCheckSpellingTextStructured:
    """Test suite for `check_spelling_text_structured` — the live production API."""

    def test_empty_dataframe_returns_no_findings(self, mocker) -> None:
        mock_dictionary_manager = mocker.MagicMock()
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mocker.MagicMock()
        )

        spellchecker = SpellChecker("pt_BR", [])

        findings, error = spellchecker.check_spelling_text_structured(pd.DataFrame(), [])

        assert findings == ()
        assert error is None

    def test_processing_error_is_reported_not_raised(self, mocker) -> None:
        """SPELL-005's deliberate broad catch: any processing failure returns as `error`."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor = mocker.MagicMock()
        mock_dataframe_processor.find_quality_findings.side_effect = ValueError("boom")

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mock_dataframe_processor,
        )

        spellchecker = SpellChecker("pt_BR", [])

        findings, error = spellchecker.check_spelling_text_structured(pd.DataFrame({"texto": ["a"]}), ["texto"])

        assert findings == ()
        assert error == "boom"

    def test_findings_are_wrapped_as_spelling_finding(self, mocker) -> None:
        mock_dictionary_manager = mocker.MagicMock()
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor = mocker.MagicMock()
        mock_dataframe_processor.find_quality_findings.return_value = [(0, "texto", "misspelled_words", ["erro"])]

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mock_dictionary_manager,
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mock_dataframe_processor,
        )

        spellchecker = SpellChecker("pt_BR", [])

        findings, error = spellchecker.check_spelling_text_structured(pd.DataFrame({"texto": ["erro"]}), ["texto"])

        assert error is None
        assert findings == (SpellingFinding(row_index=0, column="texto", kind="misspelled_words", words=("erro",)),)
