#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""Unit tests for `FileSystemUtils`.

`detect_encoding`, `remove_file`, `check_file_exists`, `check_directory_exists`, and
`check_directory_is_empty` had zero production callers and were removed as dead code; their
tests were removed with them. Only `get_last_directory_name` and `create_directory` remain.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from data_validate.helpers.base.file_system_utils import FileSystemUtils


class TestFileSystemUtils:
    """Test suite for FileSystemUtils core functionality."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.language_manager = mocker.MagicMock()
        # Setup default mock returns for language manager
        fs_utils.language_manager.text.return_value = "mocked_message"
        return fs_utils

    @pytest.fixture
    def temp_file(self) -> Generator[str, None, None]:
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("Test content")
            temp_file_path = temp_file.name

        yield temp_file_path

        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_init_creates_language_manager(self, mocker) -> None:
        """Test that __init__ creates LanguageManager instance."""
        mock_lm = mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        mock_instance = mocker.MagicMock()
        mock_lm.return_value = mock_instance

        fs_utils = FileSystemUtils()

        mock_lm.assert_called_once()
        assert fs_utils.language_manager == mock_instance

    def test_init_uses_injected_language_manager(self, mocker) -> None:
        """ARC-002/BUG-004/BUG-023: an injected `language_manager` is used as-is, no new instance built."""
        mock_lm = mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        shared_language_manager = mocker.MagicMock()

        fs_utils = FileSystemUtils(language_manager=shared_language_manager)

        mock_lm.assert_not_called()
        assert fs_utils.language_manager is shared_language_manager

    def test_get_last_directory_name_basic_path(self, fs_utils: FileSystemUtils) -> None:
        """Test get_last_directory_name with basic path."""
        result = fs_utils.get_last_directory_name("/path/to/directory")
        assert result == "directory"

    def test_get_last_directory_name_single_name(self, fs_utils: FileSystemUtils) -> None:
        """Test get_last_directory_name with single directory name."""
        result = fs_utils.get_last_directory_name("folder")
        assert result == "folder"

    def test_get_last_directory_name_with_trailing_slash(self, fs_utils: FileSystemUtils) -> None:
        """Test get_last_directory_name with trailing slash."""
        result = fs_utils.get_last_directory_name("/path/to/directory/")
        assert result == "directory"

    def test_create_directory_success(self, fs_utils: FileSystemUtils) -> None:
        """Test successful directory creation."""
        fs_utils.language_manager.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            new_dir = os.path.join(temp_parent, "new_directory")

            success, message = fs_utils.create_directory(new_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(new_dir)
            fs_utils.language_manager.text.assert_called_with("fs_utils_success_dir_created", dir_name=new_dir)

    def test_create_directory_empty_name(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with empty directory name."""
        fs_utils.language_manager.text.return_value = "empty_dir_path_error"

        success, message = fs_utils.create_directory("")

        assert success is False
        assert message == "empty_dir_path_error"
        fs_utils.language_manager.text.assert_called_with("fs_utils_error_dir_path_empty")

    def test_create_directory_already_exists(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test create_directory with existing directory."""
        fs_utils.language_manager.text.return_value = "directory_exists_info"

        success, message = fs_utils.create_directory(temp_dir)

        assert success is True
        assert message == "directory_exists_info"
        fs_utils.language_manager.text.assert_called_with("fs_utils_info_dir_exists", dir_name=temp_dir)

    def test_create_directory_path_exists_not_dir(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test create_directory when path exists but is not a directory."""
        fs_utils.language_manager.text.return_value = "path_not_dir_error"

        success, message = fs_utils.create_directory(temp_file)

        assert success is False
        assert message == "path_not_dir_error"
        fs_utils.language_manager.text.assert_called_with("fs_utils_error_path_not_dir", path=temp_file)

    def test_create_directory_os_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test create_directory with OSError."""
        fs_utils.language_manager.text.return_value = "create_dir_os_error"

        mocker.patch("os.makedirs", side_effect=OSError("Permission denied"))
        mocker.patch("os.path.exists", return_value=False)

        success, message = fs_utils.create_directory("/some/directory")

        assert success is False
        assert message == "create_dir_os_error"
        fs_utils.language_manager.text.assert_called_with("fs_utils_error_create_dir_os", error="Permission denied")

    def test_create_directory_unexpected_error_propagates(self, fs_utils: FileSystemUtils, mocker) -> None:
        """SEC-004: `create_directory` only catches `OSError` -- a non-OSError failure propagates."""
        mocker.patch("os.makedirs", side_effect=ValueError("Unexpected error"))
        mocker.patch("os.path.exists", return_value=False)

        with pytest.raises(ValueError, match="Unexpected error"):
            fs_utils.create_directory("/some/directory")


class TestFileSystemUtilsDataDrivenTests:
    """Data-driven tests for FileSystemUtils using pytest parameterization."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.language_manager = mocker.MagicMock()
        fs_utils.language_manager.text.return_value = "mocked_message"
        return fs_utils

    @pytest.mark.parametrize(
        "path,expected_name",
        [
            ("/path/to/directory", "directory"),
            ("/root", "root"),
            ("single_folder", "single_folder"),
            ("/path/to/folder/", "folder"),
            ("../relative/path", "path"),
            ("./current/folder", "folder"),
            ("/", ""),
            ("", ""),
        ],
    )
    def test_get_last_directory_name_variations(self, fs_utils: FileSystemUtils, path: str, expected_name: str) -> None:
        """Test get_last_directory_name with various path formats."""
        result = fs_utils.get_last_directory_name(path)
        assert result == expected_name


class TestFileSystemUtilsEdgeCases:
    """Edge cases and boundary condition tests for FileSystemUtils."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.language_manager = mocker.MagicMock()
        fs_utils.language_manager.text.return_value = "mocked_message"
        return fs_utils

    def test_create_directory_nested_path(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with nested directory structure."""
        fs_utils.language_manager.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            nested_dir = os.path.join(temp_parent, "level1", "level2", "level3")

            success, message = fs_utils.create_directory(nested_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(nested_dir)

    def test_create_directory_with_special_characters(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with special characters in directory name."""
        fs_utils.language_manager.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            special_dir = os.path.join(temp_parent, "test-dir_with.special@chars")

            success, message = fs_utils.create_directory(special_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(special_dir)

    def test_pathlib_integration(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test that get_last_directory_name properly uses pathlib.Path."""
        mock_path = mocker.patch("data_validate.helpers.base.file_system_utils.Path")
        mock_instance = mocker.MagicMock()
        mock_instance.name = "test_directory"
        mock_path.return_value = mock_instance

        result = fs_utils.get_last_directory_name("/some/path/test_directory")

        mock_path.assert_called_once_with("/some/path/test_directory")
        assert result == "test_directory"


class TestFileSystemUtilsIntegration:
    """Integration tests for FileSystemUtils complete workflows."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.language_manager = mocker.MagicMock()
        fs_utils.language_manager.text.return_value = "mocked_message"
        return fs_utils

    def test_multilingual_message_integration(self, fs_utils: FileSystemUtils) -> None:
        """Test that language manager is properly called with correct keys."""
        # Empty directory name test
        fs_utils.language_manager.text.reset_mock()
        fs_utils.create_directory("")
        fs_utils.language_manager.text.assert_called_with("fs_utils_error_dir_path_empty")

    def test_cross_platform_path_handling(self, fs_utils: FileSystemUtils) -> None:
        """Test that file system operations work with different path formats."""
        # Test with different path separators and formats
        paths_to_test = [
            "/unix/style/path",
            "relative/path",
            "./current/directory",
            "../parent/directory",
        ]

        for path in paths_to_test:
            # get_last_directory_name should work with all path formats
            result = fs_utils.get_last_directory_name(path)
            assert isinstance(result, str)

            # Path operations should handle different formats gracefully
            expected_basename = os.path.basename(path.rstrip("/"))
            if expected_basename:
                assert result == expected_basename or result == Path(path).name
