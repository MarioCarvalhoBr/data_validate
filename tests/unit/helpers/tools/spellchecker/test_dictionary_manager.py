"""
Unit tests for dictionary_manager.py module.

This module tests the DictionaryManager class functionality including
dictionary initialization, validation, word loading, and cleanup operations.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import os
import tempfile
from pathlib import Path


from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager


class TestDictionaryManager:
    """Test suite for DictionaryManager core functionality."""

    def test_initialization(self, mocker) -> None:
        """Test DictionaryManager initialization."""
        mock_broker = mocker.MagicMock()
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")

        assert manager.lang_dict_spell == "pt_BR"
        assert manager.dictionary is None
        assert manager.broker is None
        assert manager._errors == []
        assert isinstance(manager.path_dictionary, Path)

    def test_setup_paths(self, mocker) -> None:
        """Test path setup and environment variable configuration."""
        # Clear os.environ before creating manager
        original_env = os.environ.copy()
        os.environ.clear()

        try:
            manager = DictionaryManager("pt_BR")

            # Check that ENCHANT_CONFIG_DIR is set
            assert "ENCHANT_CONFIG_DIR" in os.environ
            assert str(manager.path_dictionary) == os.environ["ENCHANT_CONFIG_DIR"]
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_validate_dictionary_exists(self, mocker) -> None:
        """Test dictionary validation when dictionary exists."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.return_value = True
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert errors == []
        mock_broker.dict_exists.assert_called_once_with("pt_BR")

    def test_validate_dictionary_not_exists(self, mocker) -> None:
        """Test dictionary validation when dictionary does not exist."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.return_value = False
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert len(errors) == 1
        assert "Dicionário pt_BR não encontrado" in errors[0]

    def test_validate_dictionary_broker_exception(self, mocker) -> None:
        """Test dictionary validation when broker raises exception."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.side_effect = Exception("Broker error")
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert len(errors) == 1
        assert "Erro ao verificar dicionário: Broker error" in errors[0]

    def test_initialize_dictionary_success(self, mocker) -> None:
        """Test successful dictionary initialization."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        # Mock the _load_extra_words method
        mocker.patch.object(manager, "_load_extra_words")

        result = manager.initialize_dictionary(["word1", "word2"])

        assert result == mock_dictionary
        assert manager.dictionary == mock_dictionary
        mock_broker.request_dict.assert_called_once_with("pt_BR")
        mock_dictionary.add.assert_any_call("word1")
        mock_dictionary.add.assert_any_call("word2")

    def test_initialize_dictionary_with_comment_words(self, mocker) -> None:
        """Test dictionary initialization with comment words (starting with #)."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        manager.initialize_dictionary(["word1", "#comment", "word2"])

        # Should only add non-comment words
        mock_dictionary.add.assert_any_call("word1")
        mock_dictionary.add.assert_any_call("word2")
        # Should not add comment word - check that it wasn't called with comment
        calls = mock_dictionary.add.call_args_list
        comment_calls = [call for call in calls if call[0][0] == "#comment"]
        assert len(comment_calls) == 0

    def test_initialize_dictionary_with_empty_words(self, mocker) -> None:
        """Test dictionary initialization with empty words."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        manager.initialize_dictionary(["word1", "", "word2"])

        # Should only add non-empty words
        mock_dictionary.add.assert_any_call("word1")
        mock_dictionary.add.assert_any_call("word2")
        # Should not add empty word - check that it wasn't called with empty string
        calls = mock_dictionary.add.call_args_list
        empty_calls = [call for call in calls if call[0][0] == ""]
        assert len(empty_calls) == 0

    def test_initialize_dictionary_broker_not_initialized(self, mocker) -> None:
        """Test dictionary initialization when broker is not initialized."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        # Don't set manager.broker

        mocker.patch.object(manager, "_load_extra_words")

        result = manager.initialize_dictionary(["word1"])

        assert result == mock_dictionary
        # Should create broker if not exists
        mock_broker.request_dict.assert_called_once_with("pt_BR")

    def test_initialize_dictionary_exception(self, mocker) -> None:
        """Test dictionary initialization when exception occurs."""
        mock_broker = mocker.MagicMock()
        mock_broker.request_dict.side_effect = Exception("Dictionary error")
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        result = manager.initialize_dictionary(["word1"])

        assert result is None
        assert len(manager._errors) == 1
        assert "Erro ao inicializar dicionário pt_BR: Dictionary error" in manager._errors[0]

    def test_load_extra_words_file_exists(self, mocker) -> None:
        """Test loading extra words when file exists."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        # Mock file content
        file_content = "word1\nword2\n#comment\n\nword3\n"

        # Create a proper mock for open that supports context manager
        mock_file = mocker.mock_open(read_data=file_content)
        mocker.patch("builtins.open", mock_file)
        mocker.patch.object(Path, "exists", return_value=True)

        manager._load_extra_words()

        # Should add non-comment, non-empty words
        mock_dictionary.add.assert_any_call("word1")
        mock_dictionary.add.assert_any_call("word2")
        mock_dictionary.add.assert_any_call("word3")
        # Should not add comment or empty lines - check that they weren't called
        calls = mock_dictionary.add.call_args_list
        comment_calls = [call for call in calls if call[0][0] == "#comment"]
        empty_calls = [call for call in calls if call[0][0] == ""]
        assert len(comment_calls) == 0
        assert len(empty_calls) == 0

    def test_load_extra_words_file_not_exists(self, mocker) -> None:
        """Test loading extra words when file does not exist."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        mocker.patch.object(Path, "exists", return_value=False)
        manager._load_extra_words()

        assert len(manager._errors) == 1
        assert "Arquivo extra-words.dic não encontrado" in manager._errors[0]
        mock_dictionary.add.assert_not_called()

    def test_load_extra_words_file_read_error(self, mocker) -> None:
        """Test loading extra words when file read fails."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        mocker.patch.object(Path, "exists", return_value=True)
        mocker.patch("builtins.open", side_effect=IOError("File read error"))
        manager._load_extra_words()

        assert len(manager._errors) == 1
        assert "Aviso: Não foi possível carregar palavras extras: File read error" in manager._errors[0]

    def test_clean_temporary_files_success(self, mocker) -> None:
        """Test successful cleanup of temporary files."""
        mock_dictionary = mocker.MagicMock()
        mock_broker = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary
        manager.broker = mock_broker

        # Mock file operations
        mock_path = mocker.MagicMock()
        mock_path.exists.return_value = True
        mock_path.unlink.return_value = None

        mocker.patch.object(Path, "__new__", return_value=mock_path)
        manager.clean_temporary_files()

        # Should cleanup dictionary and broker
        assert manager.dictionary is None
        assert manager.broker is None
        # Should attempt to remove temporary files
        assert mock_path.unlink.call_count >= 2  # .dic and .exc files

    def test_clean_temporary_files_dictionary_cleanup_error(self, mocker) -> None:
        """Test cleanup when dictionary cleanup fails."""
        manager = DictionaryManager("pt_BR")

        # Create a mock dictionary that raises an exception when accessed
        mock_dictionary = mocker.MagicMock()
        mock_dictionary.__bool__ = mocker.MagicMock(side_effect=Exception("Cleanup error"))
        manager.dictionary = mock_dictionary
        manager.broker = mocker.MagicMock()

        manager.clean_temporary_files()

        # Should handle cleanup error gracefully
        assert len(manager._errors) == 1
        assert "Warning: Could not cleanup Enchant resources: Cleanup error" in manager._errors[0]

    def test_clean_temporary_files_file_removal_error(self, mocker) -> None:
        """Test cleanup when file removal fails."""
        mock_dictionary = mocker.MagicMock()
        mock_broker = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary
        manager.broker = mock_broker

        # Mock file operations to raise exception
        mock_path = mocker.MagicMock()
        mock_path.exists.return_value = True
        mock_path.unlink.side_effect = OSError("Permission denied")

        mocker.patch.object(Path, "__new__", return_value=mock_path)
        manager.clean_temporary_files()

        # Should handle file removal error gracefully
        assert len(manager._errors) == 2  # One for each file
        assert "Warning: Could not remove temporary file" in manager._errors[0]

    def test_destructor_cleanup(self, mocker) -> None:
        """Test that destructor calls cleanup."""
        manager = DictionaryManager("pt_BR")

        # Create a proper mock for the method
        mock_cleanup = mocker.patch.object(manager, "clean_temporary_files")

        # Call __del__ directly to test it
        manager.__del__()

        # Verify cleanup was called
        mock_cleanup.assert_called_once()


class TestDictionaryManagerEdgeCases:
    """Edge cases and boundary conditions for DictionaryManager."""

    def test_initialization_with_different_languages(self, mocker) -> None:
        """Test initialization with different language codes."""
        languages = ["en_US", "es_ES", "fr_FR", "de_DE"]

        for lang in languages:
            manager = DictionaryManager(lang)
            assert manager.lang_dict_spell == lang

    def test_initialize_dictionary_with_none_words(self, mocker) -> None:
        """Test dictionary initialization with None words list."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        result = manager.initialize_dictionary(None)

        # When None is passed, it should raise an exception in the for loop
        assert result is None
        assert len(manager._errors) == 1
        assert "Erro ao inicializar dicionário pt_BR" in manager._errors[0]

    def test_initialize_dictionary_with_very_long_word_list(self, mocker) -> None:
        """Test dictionary initialization with very long word list."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        # Create a large word list
        large_word_list = [f"word{i}" for i in range(10000)]

        result = manager.initialize_dictionary(large_word_list)

        assert result == mock_dictionary
        assert mock_dictionary.add.call_count == 10000

    def test_load_extra_words_empty_file(self, mocker) -> None:
        """Test loading extra words from empty file."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        # Create proper mock for open
        mock_file = mocker.mock_open(read_data="")
        mocker.patch("builtins.open", mock_file)
        mocker.patch.object(Path, "exists", return_value=True)

        manager._load_extra_words()

        # Should not add any words
        mock_dictionary.add.assert_not_called()

    def test_load_extra_words_file_with_only_comments(self, mocker) -> None:
        """Test loading extra words from file with only comments."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        file_content = "# This is a comment\n# Another comment\n\n# Empty line above"

        # Create proper mock for open
        mock_file = mocker.mock_open(read_data=file_content)
        mocker.patch("builtins.open", mock_file)
        mocker.patch.object(Path, "exists", return_value=True)

        manager._load_extra_words()

        # Should not add any words
        mock_dictionary.add.assert_not_called()

    def test_clean_temporary_files_no_files_exist(self, mocker) -> None:
        """Test cleanup when no temporary files exist."""
        manager = DictionaryManager("pt_BR")

        # Mock file operations - files don't exist
        mock_path = mocker.MagicMock()
        mock_path.exists.return_value = False

        mocker.patch.object(Path, "__new__", return_value=mock_path)
        manager.clean_temporary_files()

        # Should not attempt to remove files
        mock_path.unlink.assert_not_called()

    def test_multiple_initialization_attempts(self, mocker) -> None:
        """Test multiple dictionary initialization attempts."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        # Initialize multiple times
        result1 = manager.initialize_dictionary(["word1"])
        result2 = manager.initialize_dictionary(["word2"])

        assert result1 == mock_dictionary
        assert result2 == mock_dictionary
        # Should call request_dict multiple times
        assert mock_broker.request_dict.call_count == 2


class TestDictionaryManagerIntegration:
    """Integration tests for DictionaryManager."""

    def test_complete_workflow(self, mocker) -> None:
        """Test complete workflow from initialization to cleanup."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.dict_exists.return_value = True
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("data_validate.helpers.tools.spellchecker.dictionary_manager.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")

        # Step 1: Validate dictionary
        errors = manager.validate_dictionary()
        assert errors == []

        # Step 2: Initialize dictionary
        mocker.patch.object(manager, "_load_extra_words")
        result = manager.initialize_dictionary(["word1", "word2"])
        assert result == mock_dictionary

        # Step 3: Cleanup
        mocker.patch.object(Path, "__new__", return_value=mocker.MagicMock())
        manager.clean_temporary_files()

        assert manager.dictionary is None
        assert manager.broker is None

    def test_path_handling_with_real_paths(self, mocker) -> None:
        """Test path handling with real path operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the path to point to our temp directory
            temp_path = Path(temp_dir)

            mocker.patch.object(Path, "resolve", return_value=temp_path)
            mocker.patch.object(Path, "parents", return_value=[temp_path, temp_path, temp_path, temp_path])
            mocker.patch.object(Path, "__truediv__", return_value=temp_path / "static" / "dictionaries")
            DictionaryManager("pt_BR")

            # Should set up paths correctly
            assert "ENCHANT_CONFIG_DIR" in os.environ
