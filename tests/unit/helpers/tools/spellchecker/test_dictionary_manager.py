"""
Unit tests for dictionary_manager.py module.

This module tests the DictionaryManager class functionality including
dictionary initialization, validation, word loading, and cleanup operations.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import os
import subprocess
import sys
from pathlib import Path

import pytest

from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager

# TST-007: the availability probe (and the resulting skip) is centralised in
# `tests/conftest.py`'s `enchant_pt_br_available()` /
# `pytest_collection_modifyitems` hook, shared with `tests/e2e/test_golden.py`.
# The `@pytest.mark.requires_enchant` marker on `TestDictionaryManagerRealEnchant` below is all
# that is needed here; no local probe/skipif duplication.


class TestDictionaryManager:
    """Test suite for DictionaryManager core functionality."""

    def test_initialization(self, mocker) -> None:
        """Test DictionaryManager initialization."""
        mock_broker = mocker.MagicMock()
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")

        assert manager.lang_dict_spell == "pt_BR"
        assert manager.dictionary is None
        assert manager.broker is None
        assert manager._errors == []
        assert isinstance(manager.path_dictionary, Path)

    def test_initialization_does_not_mutate_environment(self, mocker) -> None:
        """Constructing a DictionaryManager must not touch `ENCHANT_CONFIG_DIR` (SEC-007).

        The old `_setup_paths` set the environment variable for the whole
        process as soon as the manager was built; the fix scopes that
        mutation to the individual calls that actually need it
        (`validate_dictionary`/`initialize_dictionary`) and restores the
        previous value afterwards, so construction alone must be a no-op on
        `os.environ`.
        """
        mock_broker = mocker.MagicMock()
        mocker.patch("enchant.Broker", return_value=mock_broker)

        before = os.environ.copy()
        DictionaryManager("pt_BR")

        assert os.environ == before

    def test_enchant_config_dir_scope_restores_previous_value(self, mocker) -> None:
        """`_enchant_config_dir_scope` must restore a pre-existing `ENCHANT_CONFIG_DIR`."""
        manager = DictionaryManager("pt_BR")
        mocker.patch.object(manager, "_ensure_enchant_session_dir", return_value=Path("/tmp/fake-session-dir"))

        os.environ["ENCHANT_CONFIG_DIR"] = "/some/previous/value"
        try:
            with manager._enchant_config_dir_scope():
                assert os.environ["ENCHANT_CONFIG_DIR"] == "/tmp/fake-session-dir"
            assert os.environ["ENCHANT_CONFIG_DIR"] == "/some/previous/value"
        finally:
            os.environ.pop("ENCHANT_CONFIG_DIR", None)

    def test_enchant_config_dir_scope_restores_absence(self, mocker) -> None:
        """`_enchant_config_dir_scope` must remove the variable if it was unset before."""
        manager = DictionaryManager("pt_BR")
        mocker.patch.object(manager, "_ensure_enchant_session_dir", return_value=Path("/tmp/fake-session-dir"))

        os.environ.pop("ENCHANT_CONFIG_DIR", None)
        with manager._enchant_config_dir_scope():
            assert os.environ["ENCHANT_CONFIG_DIR"] == "/tmp/fake-session-dir"

        assert "ENCHANT_CONFIG_DIR" not in os.environ

    def test_validate_dictionary_exists(self, mocker) -> None:
        """Test dictionary validation when dictionary exists."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.return_value = True
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert errors == []
        mock_broker.dict_exists.assert_called_once_with("pt_BR")

    def test_validate_dictionary_not_exists(self, mocker) -> None:
        """Test dictionary validation when dictionary does not exist."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.return_value = False
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert len(errors) == 1
        assert "Dicionário pt_BR não encontrado" in errors[0]

    def test_validate_dictionary_broker_exception(self, mocker) -> None:
        """Test dictionary validation when broker raises exception."""
        mock_broker = mocker.MagicMock()
        mock_broker.dict_exists.side_effect = Exception("Broker error")
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        errors = manager.validate_dictionary()

        assert len(errors) == 1
        assert "Erro ao verificar dicionário: Broker error" in errors[0]

    def test_initialize_dictionary_success(self, mocker) -> None:
        """Test successful dictionary initialization."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        # Mock the _load_extra_words method
        mocker.patch.object(manager, "_load_extra_words")

        result = manager.initialize_dictionary(["word1", "word2"])

        assert result == mock_dictionary
        assert manager.dictionary == mock_dictionary
        mock_broker.request_dict.assert_called_once_with("pt_BR")
        # Session-only words (BUG-022): never persisted with `add()`.
        mock_dictionary.add_to_session.assert_any_call("word1")
        mock_dictionary.add_to_session.assert_any_call("word2")
        mock_dictionary.add.assert_not_called()

    def test_initialize_dictionary_with_comment_words(self, mocker) -> None:
        """Test dictionary initialization with comment words (starting with #)."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        manager.initialize_dictionary(["word1", "#comment", "word2"])

        # Should only add non-comment words
        mock_dictionary.add_to_session.assert_any_call("word1")
        mock_dictionary.add_to_session.assert_any_call("word2")
        # Should not add comment word - check that it wasn't called with comment
        calls = mock_dictionary.add_to_session.call_args_list
        comment_calls = [call for call in calls if call[0][0] == "#comment"]
        assert len(comment_calls) == 0

    def test_initialize_dictionary_with_empty_words(self, mocker) -> None:
        """Test dictionary initialization with empty words."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        manager.initialize_dictionary(["word1", "", "word2"])

        # Should only add non-empty words
        mock_dictionary.add_to_session.assert_any_call("word1")
        mock_dictionary.add_to_session.assert_any_call("word2")
        # Should not add empty word - check that it wasn't called with empty string
        calls = mock_dictionary.add_to_session.call_args_list
        empty_calls = [call for call in calls if call[0][0] == ""]
        assert len(empty_calls) == 0

    def test_initialize_dictionary_broker_not_initialized(self, mocker) -> None:
        """Test dictionary initialization when broker is not initialized."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("enchant.Broker", return_value=mock_broker)

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
        mocker.patch("enchant.Broker", return_value=mock_broker)

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

        # Should add non-comment, non-empty words to the session word list only.
        mock_dictionary.add_to_session.assert_any_call("word1")
        mock_dictionary.add_to_session.assert_any_call("word2")
        mock_dictionary.add_to_session.assert_any_call("word3")
        # Should not add comment or empty lines - check that they weren't called
        calls = mock_dictionary.add_to_session.call_args_list
        comment_calls = [call for call in calls if call[0][0] == "#comment"]
        empty_calls = [call for call in calls if call[0][0] == ""]
        assert len(comment_calls) == 0
        assert len(empty_calls) == 0
        mock_dictionary.add.assert_not_called()

    def test_load_extra_words_file_not_exists(self, mocker) -> None:
        """Test loading extra words when file does not exist."""
        mock_dictionary = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary

        mocker.patch.object(Path, "exists", return_value=False)
        manager._load_extra_words()

        assert len(manager._errors) == 1
        assert "Arquivo extra-words.dic não encontrado" in manager._errors[0]
        mock_dictionary.add_to_session.assert_not_called()

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

    def test_clean_temporary_files_releases_dictionary_and_broker(self, mocker) -> None:
        """Test that cleanup drops the dictionary/broker references.

        Replaces the old `test_clean_temporary_files_success`: there are no
        `.dic`/`.exc` files to delete any more (BUG-022, SEC-007), so this
        only asserts the reference-dropping half of the old behaviour.
        """
        mock_dictionary = mocker.MagicMock()
        mock_broker = mocker.MagicMock()

        manager = DictionaryManager("pt_BR")
        manager.dictionary = mock_dictionary
        manager.broker = mock_broker

        manager.clean_temporary_files()

        assert manager.dictionary is None
        assert manager.broker is None

    def test_clean_temporary_files_removes_session_directory(self, mocker) -> None:
        """Test that cleanup discards the session-scoped Enchant config directory.

        Replaces the old file-deletion assertions: instead of removing
        predictable `.dic`/`.exc` files from the package directory, cleanup
        now removes the whole ephemeral session directory Enchant was
        pointed at (SEC-007).
        """
        manager = DictionaryManager("pt_BR")
        session_dir = manager._ensure_enchant_session_dir()

        assert session_dir.exists()

        manager.clean_temporary_files()

        assert not session_dir.exists()
        assert manager._enchant_session_dir is None

    def test_clean_temporary_files_always_drops_references(self, mocker) -> None:
        """SEC-004: `clean_temporary_files` unconditionally assigns `None`, which cannot
        raise — there is no longer a broad `except Exception` fallback to test."""
        manager = DictionaryManager("pt_BR")
        manager.dictionary = mocker.MagicMock()
        manager.broker = mocker.MagicMock()

        manager.clean_temporary_files()

        assert manager.dictionary is None
        assert manager.broker is None
        assert manager._errors == []

    def test_clean_temporary_files_without_session_directory_is_a_no_op(self) -> None:
        """Test that cleanup tolerates a manager that never created a session directory."""
        manager = DictionaryManager("pt_BR")

        manager.clean_temporary_files()

        assert manager._enchant_session_dir is None


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
        mocker.patch("enchant.Broker", return_value=mock_broker)

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
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")
        manager.broker = mock_broker

        mocker.patch.object(manager, "_load_extra_words")

        # Create a large word list
        large_word_list = [f"word{i}" for i in range(10000)]

        result = manager.initialize_dictionary(large_word_list)

        assert result == mock_dictionary
        assert mock_dictionary.add_to_session.call_count == 10000

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
        mock_dictionary.add_to_session.assert_not_called()

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
        mock_dictionary.add_to_session.assert_not_called()

    def test_multiple_initialization_attempts(self, mocker) -> None:
        """Test multiple dictionary initialization attempts."""
        mock_broker = mocker.MagicMock()
        mock_dictionary = mocker.MagicMock()
        mock_broker.request_dict.return_value = mock_dictionary
        mocker.patch("enchant.Broker", return_value=mock_broker)

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
        mocker.patch("enchant.Broker", return_value=mock_broker)

        manager = DictionaryManager("pt_BR")

        # Step 1: Validate dictionary
        errors = manager.validate_dictionary()
        assert errors == []

        # Step 2: Initialize dictionary
        mocker.patch.object(manager, "_load_extra_words")
        result = manager.initialize_dictionary(["word1", "word2"])
        assert result == mock_dictionary

        # Step 3: Cleanup
        manager.clean_temporary_files()

        assert manager.dictionary is None
        assert manager.broker is None
        assert manager._enchant_session_dir is None

    def test_path_handling_with_real_paths(self) -> None:
        """Test that `path_dictionary` resolves to the real bundled dictionaries folder."""
        manager = DictionaryManager("pt_BR")

        assert manager.path_dictionary.name == "dictionaries"
        assert manager.path_dictionary.is_dir()
        assert (manager.path_dictionary / "hunspell").is_dir()
        # Construction alone must not touch the environment (SEC-007).
        assert "ENCHANT_CONFIG_DIR" not in os.environ or manager._enchant_session_dir is None


class TestDictionaryManagerRealEnchant:
    """Regression tests against the real Enchant/hunspell backend (SEC-007, BUG-022).

    These prove the bundled `pt_BR` dictionary still resolves through the
    session-scoped `ENCHANT_CONFIG_DIR`, that session words are usable
    without ever touching disk, and that two managers in the same process
    are fully isolated from each other. They are skipped (not failed) when
    the native libenchant/hunspell backend is unavailable.
    """

    @pytest.mark.requires_enchant
    def test_session_word_is_checkable(self) -> None:
        manager = DictionaryManager("pt_BR")
        try:
            dictionary = manager.initialize_dictionary(["palavraz"])
            assert dictionary is not None
            assert dictionary.check("palavraz") is True
        finally:
            manager.clean_temporary_files()

    @pytest.mark.requires_enchant
    def test_environment_is_unchanged_after_full_lifecycle(self) -> None:
        before = os.environ.copy()

        manager = DictionaryManager("pt_BR")
        manager.initialize_dictionary(["palavraz"])
        manager.validate_dictionary()
        manager.clean_temporary_files()

        assert os.environ == before

    @pytest.mark.requires_enchant
    def test_no_file_created_under_package_dictionaries_directory(self) -> None:
        manager = DictionaryManager("pt_BR")
        before_listing = sorted(p.name for p in manager.path_dictionary.iterdir())

        manager.initialize_dictionary(["palavraz"])
        manager.validate_dictionary()
        manager.clean_temporary_files()

        after_listing = sorted(p.name for p in manager.path_dictionary.iterdir())
        assert after_listing == before_listing

    @pytest.mark.requires_enchant
    def test_two_managers_do_not_interfere(self) -> None:
        manager_one = DictionaryManager("pt_BR")
        manager_two = DictionaryManager("pt_BR")
        try:
            dictionary_one = manager_one.initialize_dictionary(["palavraumexclusivo"])
            dictionary_two = manager_two.initialize_dictionary(["outrapalavraz"])

            assert dictionary_one.check("palavraumexclusivo") is True
            assert dictionary_two.check("palavraumexclusivo") is False

            assert dictionary_two.check("outrapalavraz") is True
            assert dictionary_one.check("outrapalavraz") is False
        finally:
            manager_one.clean_temporary_files()
            manager_two.clean_temporary_files()


class TestLazyEnchantImport:
    """PERF-008: `enchant` must not be imported by merely importing this module.

    `enchant` (the pyenchant/libenchant native backend) is a heavy/optional
    dependency needed only when a dictionary is actually validated or
    initialized; constructing a `DictionaryManager` or importing this module
    must not pay its import cost.
    """

    def test_module_import_does_not_import_enchant(self) -> None:
        """Importing the module alone, in a fresh subprocess, must not import `enchant`."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                "import data_validate.helpers.tools.spellchecker.dictionary_manager; "
                "import sys; "
                "assert 'enchant' not in sys.modules, sys.modules.keys()",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr

    def test_construction_does_not_import_enchant(self) -> None:
        """Constructing a `DictionaryManager` alone must not import `enchant` either."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                "from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager; "
                "DictionaryManager('pt_BR'); "
                "import sys; "
                "assert 'enchant' not in sys.modules, sys.modules.keys()",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
