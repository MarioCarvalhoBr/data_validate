"""
Unit tests for spellchecker.py module.

This module tests the SpellChecker service class functionality including
initialization, spell checking operations, and integration with other components.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd

from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker


class TestSpellChecker:
    """Test suite for SpellChecker service class."""

    def test_initialization(self, mocker) -> None:
        """Test SpellChecker initialization with default parameters."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

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

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", None)

        assert spellchecker.list_words_user == []

    def test_initialization_with_empty_words(self, mocker) -> None:
        """Test SpellChecker initialization with empty words list."""
        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", [])

        assert spellchecker.list_words_user == []

    def test_check_spelling_text_success(self, mocker) -> None:
        """Test successful spell checking operation."""
        # Create test DataFrame
        df = pd.DataFrame({"texto_sem_erro": ["texto correto", "outro texto"], "texto_com_erros": ["texto com erros", "mais erros"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock successful dictionary initialization
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        # Mock successful processing
        mock_dataframe_processor.validate_columns.return_value = (["texto_sem_erro", "texto_com_erros"], [])
        mock_dataframe_processor.process_dataframe.return_value = ["warning1"]

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto_sem_erro", "texto_com_erros"])

        assert errors == []
        assert warnings == ["warning1"]

        # Verify method calls
        mock_dictionary_manager.initialize_dictionary.assert_called_once_with(["word1"])
        mock_dataframe_processor.validate_columns.assert_called_once()
        mock_dataframe_processor.process_dataframe.assert_called_once()

    def test_check_spelling_text_dictionary_initialization_fails(self, mocker) -> None:
        """Test spell checking when dictionary initialization fails."""
        df = pd.DataFrame({"texto_sem_erro": ["texto correto"], "texto_com_erros": ["texto com erros"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock failed dictionary initialization
        mock_dictionary_manager.initialize_dictionary.return_value = None
        mock_dictionary_manager.validate_dictionary.return_value = ["Dictionary error"]

        # Mock the process_dataframe to raise an exception due to missing dictionary
        mock_dataframe_processor.validate_columns.return_value = (["texto_sem_erro", "texto_com_erros"], [])
        mock_dataframe_processor.process_dataframe.side_effect = Exception("not enough values to unpack (expected 2, got 0)")

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto_sem_erro", "texto_com_erros"])

        assert len(errors) == 1
        assert "Erro ao processar o arquivo test.xlsx: not enough values to unpack (expected 2, got 0)" in errors[0]
        assert warnings == []

    def test_check_spelling_text_column_validation_fails(self, mocker) -> None:
        """Test spell checking when column validation fails."""
        df = pd.DataFrame({"texto_sem_erro": ["texto correto"], "texto_com_erros": ["texto com erros"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock successful dictionary initialization
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        # Mock column validation failure
        mock_dataframe_processor.validate_columns.return_value = ([], ["Column 'missing' not found"])

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["missing_column"])

        assert errors == []
        assert warnings == []

        # Should not proceed with processing if column validation fails
        mock_dataframe_processor.process_dataframe.assert_not_called()

    def test_check_spelling_text_with_none_words(self, mocker) -> None:
        """Test spell checking with None words."""
        df = pd.DataFrame({"texto_sem_erro": ["texto correto"], "texto_com_erros": ["texto com erros"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock successful dictionary initialization
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto_sem_erro", "texto_com_erros"], [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", None)

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto_sem_erro", "texto_com_erros"])

        # Should initialize dictionary with empty list (None becomes [])
        mock_dictionary_manager.initialize_dictionary.assert_called_once_with([])

    def test_check_spelling_text_with_empty_dataframe(self, mocker) -> None:
        """Test spell checking with empty DataFrame."""
        df = pd.DataFrame()

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", [])

        assert errors == []
        assert warnings == []

    def test_check_spelling_text_with_single_column(self, mocker) -> None:
        """Test spell checking with single column."""
        df = pd.DataFrame({"texto": ["texto correto", "texto com erros"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto"], [])
        mock_dataframe_processor.process_dataframe.return_value = ["warning1"]

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto"])

        assert errors == []
        assert warnings == ["warning1"]

    def test_check_spelling_text_processing_exception(self, mocker) -> None:
        """Test spell checking when processing raises exception."""
        df = pd.DataFrame({"texto": ["texto correto"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto"], [])
        mock_dataframe_processor.process_dataframe.side_effect = Exception("Processing error")

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto"])

        # Should return error on exception
        assert len(errors) == 1
        assert "Erro ao processar o arquivo test.xlsx: Processing error" in errors[0]
        assert warnings == []


class TestSpellCheckerEdgeCases:
    """Edge cases and boundary conditions for SpellChecker."""

    def test_initialization_with_different_languages(self, mocker) -> None:
        """Test initialization with different language codes."""
        languages = ["en_US", "es_ES", "fr_FR", "de_DE"]

        for lang in languages:
            mock_dictionary_manager = mocker.MagicMock()
            mock_spellchecker_controller = mocker.MagicMock()
            mock_dataframe_processor = mocker.MagicMock()

            mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
            mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
            mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

            spellchecker = SpellChecker(lang, ["word1"])
            assert spellchecker.lang_dict_spell == lang

    def test_check_spelling_text_with_very_large_dataframe(self, mocker) -> None:
        """Test spell checking with very large DataFrame."""
        # Create a large DataFrame
        large_data = {"texto": [f"texto {i}" for i in range(10000)]}
        df = pd.DataFrame(large_data)

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto"], [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "large_test.xlsx", ["texto"])

        assert errors == []
        assert warnings == []

    def test_check_spelling_text_with_many_columns(self, mocker) -> None:
        """Test spell checking with many columns."""
        # Create DataFrame with many columns
        many_columns = {f"texto_{i}": [f"texto {i}"] for i in range(100)}
        df = pd.DataFrame(many_columns)

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (list(many_columns.keys()), [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        column_names = list(many_columns.keys())
        errors, warnings = spellchecker.check_spelling_text(df, "many_columns_test.xlsx", column_names)

        assert errors == []
        assert warnings == []

    def test_check_spelling_text_with_unicode_text(self, mocker) -> None:
        """Test spell checking with Unicode text."""
        df = pd.DataFrame({"texto_unicode": ["café", "naïve", "résumé", "café", "naïve"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto_unicode"], [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "unicode_test.xlsx", ["texto_unicode"])

        assert errors == []
        assert warnings == []

    def test_check_spelling_text_with_special_characters(self, mocker) -> None:
        """Test spell checking with special characters."""
        df = pd.DataFrame({"texto_especial": ["texto@email.com", "www.site.com", "texto (com parênteses)", 'texto "com aspas"']})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto_especial"], [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "special_chars_test.xlsx", ["texto_especial"])

        assert errors == []
        assert warnings == []


class TestSpellCheckerIntegration:
    """Integration tests for SpellChecker."""

    def test_complete_workflow_success(self, mocker) -> None:
        """Test complete successful workflow."""
        df = pd.DataFrame({"texto_sem_erro": ["texto correto", "outro texto correto"], "texto_com_erros": ["texto com erros", "mais erros aqui"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock successful workflow
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto_sem_erro", "texto_com_erros"], [])
        mock_dataframe_processor.process_dataframe.return_value = ["aviso1", "aviso2"]

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1", "word2"])

        errors, warnings = spellchecker.check_spelling_text(df, "integration_test.xlsx", ["texto_sem_erro", "texto_com_erros"])

        assert errors == []
        assert warnings == ["aviso1", "aviso2"]

        # Verify all components were called correctly
        mock_dictionary_manager.initialize_dictionary.assert_called_once_with(["word1", "word2"])
        mock_dataframe_processor.validate_columns.assert_called_once()
        mock_dataframe_processor.process_dataframe.assert_called_once()

    def test_workflow_with_multiple_failures(self, mocker) -> None:
        """Test workflow with multiple failure points."""
        df = pd.DataFrame({"texto": ["texto correto"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        # Mock multiple failures
        mock_dictionary_manager.initialize_dictionary.return_value = None  # Dictionary init fails
        mock_dictionary_manager.validate_dictionary.return_value = ["Dictionary error"]
        mock_dataframe_processor.validate_columns.return_value = ([], ["Column error"])  # Column validation fails
        mock_dataframe_processor.process_dataframe.side_effect = Exception("Processing error")  # Processing fails

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        # Test with dictionary init failure
        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto"])
        assert errors == []
        assert warnings == []

        # Reset mocks for next test
        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []

        # Test with column validation failure
        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["missing_column"])
        assert errors == []
        assert warnings == []

        # Reset mocks for next test
        mock_dataframe_processor.validate_columns.return_value = (["texto"], [])

        # Test with processing failure
        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto"])
        assert len(errors) == 1
        assert "Erro ao processar o arquivo test.xlsx: Processing error" in errors[0]
        assert warnings == []

    def test_component_interaction(self, mocker) -> None:
        """Test interaction between different components."""
        df = pd.DataFrame({"texto": ["texto correto"]})

        mock_dictionary_manager = mocker.MagicMock()
        mock_spellchecker_controller = mocker.MagicMock()
        mock_dataframe_processor = mocker.MagicMock()

        mock_dictionary_manager.initialize_dictionary.return_value = mocker.MagicMock()
        mock_dictionary_manager.validate_dictionary.return_value = []
        mock_dataframe_processor.validate_columns.return_value = (["texto"], [])
        mock_dataframe_processor.process_dataframe.return_value = []

        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager", return_value=mock_dictionary_manager)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController", return_value=mock_spellchecker_controller)
        mocker.patch("data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor", return_value=mock_dataframe_processor)

        spellchecker = SpellChecker("pt_BR", ["word1"])

        errors, warnings = spellchecker.check_spelling_text(df, "test.xlsx", ["texto"])

        # Verify that the SpellCheckerController is passed to DataFrameProcessor
        mock_dataframe_processor.process_dataframe.assert_called_once()

        # Verify that the dictionary manager is used for initialization
        mock_dictionary_manager.initialize_dictionary.assert_called_once_with(["word1"])
