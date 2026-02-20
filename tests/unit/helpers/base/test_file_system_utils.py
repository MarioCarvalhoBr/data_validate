#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
import pytest

from data_validate.helpers.base.file_system_utils import FileSystemUtils


class TestFileSystemUtils:
    """Test suite for FileSystemUtils core functionality."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.lm = mocker.MagicMock()
        # Setup default mock returns for language manager
        fs_utils.lm.text.return_value = "mocked_message"
        return fs_utils

    @pytest.fixture
    def temp_file(self) -> Generator[str, None, None]:
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("Test content for encoding detection")
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
        assert fs_utils.lm == mock_instance

    def test_detect_encoding_success(self, fs_utils: FileSystemUtils, temp_file: str, mocker) -> None:
        """Test successful encoding detection."""
        mock_detect = mocker.patch("chardet.detect")
        mock_detect.return_value = {"encoding": "utf-8"}

        success, result = fs_utils.detect_encoding(temp_file)

        assert success is True
        assert result == "utf-8"

    def test_detect_encoding_empty_file_path(self, fs_utils: FileSystemUtils) -> None:
        """Test detect_encoding with empty file path."""
        fs_utils.lm.text.return_value = "empty_path_error"

        success, result = fs_utils.detect_encoding("")

        assert success is False
        assert result == "empty_path_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_path_empty")

    def test_detect_encoding_file_not_found(self, fs_utils: FileSystemUtils) -> None:
        """Test detect_encoding with non-existent file."""
        fs_utils.lm.text.return_value = "file_not_found_error"
        non_existent_file = "/path/that/does/not/exist.txt"

        success, result = fs_utils.detect_encoding(non_existent_file)

        assert success is False
        assert result == "file_not_found_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_not_found", filename=os.path.basename(non_existent_file))

    def test_detect_encoding_path_not_file(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test detect_encoding with directory path instead of file."""
        fs_utils.lm.text.return_value = "path_not_file_error"

        success, result = fs_utils.detect_encoding(temp_dir)

        assert success is False
        assert result == "path_not_file_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_file", path=temp_dir)

    def test_detect_encoding_chardet_returns_none(self, fs_utils: FileSystemUtils, temp_file: str, mocker) -> None:
        """Test detect_encoding when chardet returns None encoding."""
        fs_utils.lm.text.return_value = "encoding_failed_error"

        mock_detect = mocker.patch("chardet.detect")
        mock_detect.return_value = {"encoding": None}

        success, result = fs_utils.detect_encoding(temp_file)

        assert success is False
        assert result == "encoding_failed_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_encoding_failed")

    def test_detect_encoding_os_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test detect_encoding with OS error during file reading."""
        fs_utils.lm.text.return_value = "os_error_message"

        # Mock os.path.exists and os.path.isfile to return True, then raise OSError on open
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("builtins.open", side_effect=OSError("Permission denied"))

        success, result = fs_utils.detect_encoding("file.txt")

        assert success is False
        assert result == "os_error_message"
        fs_utils.lm.text.assert_called_with("fs_utils_error_encoding_os", error="Permission denied")

    def test_detect_encoding_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test detect_encoding with unexpected exception."""
        fs_utils.lm.text.return_value = "unexpected_error_message"

        # Mock os.path.exists and os.path.isfile to return True, then raise ValueError on open
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("builtins.open", side_effect=ValueError("Unexpected error"))

        success, result = fs_utils.detect_encoding("file.txt")

        assert success is False
        assert result == "unexpected_error_message"
        fs_utils.lm.text.assert_called_with("fs_utils_error_unexpected", error="Unexpected error")

    def test_detect_encoding_custom_num_bytes(self, fs_utils: FileSystemUtils, temp_file: str, mocker) -> None:
        """Test detect_encoding with custom num_bytes parameter."""
        mock_detect = mocker.patch("chardet.detect")
        mock_detect.return_value = {"encoding": "utf-8"}

        mock_file = mocker.patch("builtins.open", mocker.mock_open(read_data=b"test data"))
        success, result = fs_utils.detect_encoding(temp_file, num_bytes=512)

        assert success is True
        # Verify that read was called with custom num_bytes
        mock_file.return_value.read.assert_called_with(512)

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

    def test_remove_file_success(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test successful file removal."""
        fs_utils.lm.text.return_value = "file_removed_success"

        success, message = fs_utils.remove_file(temp_file)

        assert success is True
        assert message == "file_removed_success"
        assert not os.path.exists(temp_file)
        fs_utils.lm.text.assert_called_with("fs_utils_success_file_removed", filename=os.path.basename(temp_file))

    def test_remove_file_empty_path(self, fs_utils: FileSystemUtils) -> None:
        """Test remove_file with empty file path."""
        fs_utils.lm.text.return_value = "empty_path_error"

        success, message = fs_utils.remove_file("")

        assert success is False
        assert message == "empty_path_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_path_empty")

    def test_remove_file_not_found(self, fs_utils: FileSystemUtils) -> None:
        """Test remove_file with non-existent file."""
        fs_utils.lm.text.return_value = "file_not_found_info"
        non_existent_file = "/path/that/does/not/exist.txt"

        success, message = fs_utils.remove_file(non_existent_file)

        assert success is True  # Returns True for non-existent files
        assert message == "file_not_found_info"
        fs_utils.lm.text.assert_called_with("fs_utils_info_file_not_found", filename=os.path.basename(non_existent_file))

    def test_remove_file_path_not_file(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test remove_file with directory path instead of file."""
        fs_utils.lm.text.return_value = "path_not_file_error"

        success, message = fs_utils.remove_file(temp_dir)

        assert success is False
        assert message == "path_not_file_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_file", path=temp_dir)

    def test_remove_file_os_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test remove_file with OSError."""
        fs_utils.lm.text.return_value = "remove_file_os_error"

        mocker.patch("os.remove", side_effect=OSError("Permission denied"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

        success, message = fs_utils.remove_file("/some/file.txt")

        assert success is False
        assert message == "remove_file_os_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_remove_file_os", error="Permission denied")

    def test_remove_file_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test remove_file with unexpected exception."""
        fs_utils.lm.text.return_value = "unexpected_error"

        mocker.patch("os.remove", side_effect=ValueError("Unexpected error"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

        success, message = fs_utils.remove_file("/some/file.txt")

        assert success is False
        assert message == "unexpected_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_unexpected", error="Unexpected error")

    def test_create_directory_success(self, fs_utils: FileSystemUtils) -> None:
        """Test successful directory creation."""
        fs_utils.lm.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            new_dir = os.path.join(temp_parent, "new_directory")

            success, message = fs_utils.create_directory(new_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(new_dir)
            fs_utils.lm.text.assert_called_with("fs_utils_success_dir_created", dir_name=new_dir)

    def test_create_directory_empty_name(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with empty directory name."""
        fs_utils.lm.text.return_value = "empty_dir_path_error"

        success, message = fs_utils.create_directory("")

        assert success is False
        assert message == "empty_dir_path_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_path_empty")

    def test_create_directory_already_exists(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test create_directory with existing directory."""
        fs_utils.lm.text.return_value = "directory_exists_info"

        success, message = fs_utils.create_directory(temp_dir)

        assert success is True
        assert message == "directory_exists_info"
        fs_utils.lm.text.assert_called_with("fs_utils_info_dir_exists", dir_name=temp_dir)

    def test_create_directory_path_exists_not_dir(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test create_directory when path exists but is not a directory."""
        fs_utils.lm.text.return_value = "path_not_dir_error"

        success, message = fs_utils.create_directory(temp_file)

        assert success is False
        assert message == "path_not_dir_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_dir", path=temp_file)

    def test_create_directory_os_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test create_directory with OSError."""
        fs_utils.lm.text.return_value = "create_dir_os_error"

        mocker.patch("os.makedirs", side_effect=OSError("Permission denied"))
        mocker.patch("os.path.exists", return_value=False)

        success, message = fs_utils.create_directory("/some/directory")

        assert success is False
        assert message == "create_dir_os_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_create_dir_os", error="Permission denied")

    def test_create_directory_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test create_directory with unexpected exception."""
        fs_utils.lm.text.return_value = "unexpected_error"

        mocker.patch("os.makedirs", side_effect=ValueError("Unexpected error"))
        mocker.patch("os.path.exists", return_value=False)

        success, message = fs_utils.create_directory("/some/directory")

        assert success is False
        assert message == "unexpected_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_unexpected", error="Unexpected error")

    def test_check_file_exists_success(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test check_file_exists with existing file."""
        exists, messages = fs_utils.check_file_exists(temp_file)

        assert exists is True
        assert messages == []

    def test_check_file_exists_empty_path(self, fs_utils: FileSystemUtils) -> None:
        """Test check_file_exists with empty file path."""
        fs_utils.lm.text.return_value = "empty_path_error"

        exists, messages = fs_utils.check_file_exists("")

        assert exists is False
        assert messages == ["empty_path_error"]
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_path_empty")

    def test_check_file_exists_file_not_found(self, fs_utils: FileSystemUtils) -> None:
        """Test check_file_exists with non-existent file."""
        fs_utils.lm.text.return_value = "file_not_found_error"
        non_existent_file = "/path/that/does/not/exist.txt"

        exists, messages = fs_utils.check_file_exists(non_existent_file)

        assert exists is False
        assert messages == ["file_not_found_error"]
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_not_found", filename=os.path.basename(non_existent_file))

    def test_check_file_exists_path_not_file(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test check_file_exists with directory path instead of file."""
        fs_utils.lm.text.return_value = "path_not_file_error"

        exists, messages = fs_utils.check_file_exists(temp_dir)

        assert exists is False
        assert messages == ["path_not_file_error"]
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_file", path=temp_dir)

    def test_check_file_exists_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test check_file_exists with unexpected exception."""
        fs_utils.lm.text.return_value = "file_check_fail_error"

        mocker.patch("os.path.exists", side_effect=ValueError("Unexpected error"))

        exists, messages = fs_utils.check_file_exists("/some/file.txt")

        assert exists is False
        assert messages == ["file_check_fail_error"]
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_check_fail", error="Unexpected error")

    def test_check_directory_exists_success(self, fs_utils: FileSystemUtils, temp_dir: str) -> None:
        """Test check_directory_exists with existing directory."""
        exists, message = fs_utils.check_directory_exists(temp_dir)

        assert exists is True
        assert message == ""

    def test_check_directory_exists_empty_path(self, fs_utils: FileSystemUtils) -> None:
        """Test check_directory_exists with empty directory path."""
        fs_utils.lm.text.return_value = "empty_dir_path_error"

        exists, message = fs_utils.check_directory_exists("")

        assert exists is False
        assert message == "empty_dir_path_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_path_empty")

    def test_check_directory_exists_dir_not_found(self, fs_utils: FileSystemUtils) -> None:
        """Test check_directory_exists with non-existent directory."""
        fs_utils.lm.text.return_value = "dir_not_found_error"
        non_existent_dir = "/path/that/does/not/exist"

        exists, message = fs_utils.check_directory_exists(non_existent_dir)

        assert exists is False
        assert message == "dir_not_found_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_not_found", dir_path=non_existent_dir)

    def test_check_directory_exists_path_not_dir(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test check_directory_exists with file path instead of directory."""
        fs_utils.lm.text.return_value = "path_not_dir_error"

        exists, message = fs_utils.check_directory_exists(temp_file)

        assert exists is False
        assert message == "path_not_dir_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_dir", path=temp_file)

    def test_check_directory_exists_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test check_directory_exists with unexpected exception."""
        fs_utils.lm.text.return_value = "dir_check_fail_error"

        mocker.patch("os.path.exists", side_effect=ValueError("Unexpected error"))

        exists, message = fs_utils.check_directory_exists("/some/directory")

        assert exists is False
        assert message == "dir_check_fail_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_check_fail", error="Unexpected error")

    def test_check_directory_is_empty_true(self, fs_utils: FileSystemUtils) -> None:
        """Test check_directory_is_empty with empty directory."""
        fs_utils.lm.text.return_value = "dir_empty_message"

        with tempfile.TemporaryDirectory() as empty_dir:
            is_empty, message = fs_utils.check_directory_is_empty(empty_dir)

            assert is_empty is True
            assert message == "dir_empty_message"
            fs_utils.lm.text.assert_called_with("fs_utils_error_dir_empty", dir_path=empty_dir)

    def test_check_directory_is_empty_false(self, fs_utils: FileSystemUtils, temp_dir: str, temp_file: str) -> None:
        """Test check_directory_is_empty with non-empty directory."""
        fs_utils.lm.text.return_value = "dir_not_empty_message"

        # Create a file in the temp_dir to make it non-empty
        file_in_dir = os.path.join(temp_dir, "test_file.txt")
        with open(file_in_dir, "w") as f:
            f.write("test content")

        is_empty, message = fs_utils.check_directory_is_empty(temp_dir)

        assert is_empty is False
        assert message == "dir_not_empty_message"
        fs_utils.lm.text.assert_called_with("fs_utils_info_dir_not_empty", dir_path=temp_dir)

    def test_check_directory_is_empty_dir_not_found(self, fs_utils: FileSystemUtils) -> None:
        """Test check_directory_is_empty with non-existent directory."""
        fs_utils.lm.text.return_value = "dir_not_found_error"
        non_existent_dir = "/path/that/does/not/exist"

        is_empty, message = fs_utils.check_directory_is_empty(non_existent_dir)

        assert is_empty is False
        assert message == "dir_not_found_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_not_found", dir_path=non_existent_dir)

    def test_check_directory_is_empty_path_not_dir(self, fs_utils: FileSystemUtils, temp_file: str) -> None:
        """Test check_directory_is_empty with file path instead of directory."""
        fs_utils.lm.text.return_value = "path_not_dir_error"

        is_empty, message = fs_utils.check_directory_is_empty(temp_file)

        assert is_empty is False
        assert message == "path_not_dir_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_path_not_dir", path=temp_file)

    def test_check_directory_is_empty_unexpected_error(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test check_directory_is_empty with unexpected exception."""
        fs_utils.lm.text.return_value = "dir_check_fail_error"

        mocker.patch("os.path.exists", side_effect=ValueError("Unexpected error"))

        is_empty, message = fs_utils.check_directory_is_empty("/some/directory")

        assert is_empty is False
        assert message == "dir_check_fail_error"
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_check_fail", error="Unexpected error")


class TestFileSystemUtilsDataDrivenTests:
    """Data-driven tests for FileSystemUtils using pytest parameterization."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.lm = mocker.MagicMock()
        fs_utils.lm.text.return_value = "mocked_message"
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

    @pytest.mark.parametrize(
        "encoding_result,expected_success,expected_encoding",
        [
            ({"encoding": "utf-8"}, True, "utf-8"),
            ({"encoding": "latin-1"}, True, "latin-1"),
            ({"encoding": "ascii"}, True, "ascii"),
            ({"encoding": "cp1252"}, True, "cp1252"),
            ({"encoding": None}, False, "mocked_message"),
            ({}, False, "mocked_message"),
        ],
    )
    def test_detect_encoding_various_results(
        self, fs_utils: FileSystemUtils, encoding_result: Dict[str, Any], expected_success: bool, expected_encoding: str, mocker
    ) -> None:
        """Test detect_encoding with various chardet results."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = encoding_result

            success, result = fs_utils.detect_encoding(temp_file_path)

            assert success == expected_success
            assert result == expected_encoding
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.parametrize(
        "exception_type,exception_message,expected_lm_call",
        [
            (OSError, "Permission denied", "fs_utils_error_encoding_os"),
            (OSError, "Input/output error", "fs_utils_error_encoding_os"),
            (ValueError, "Invalid value", "fs_utils_error_unexpected"),
            (RuntimeError, "Runtime error", "fs_utils_error_unexpected"),
        ],
    )
    def test_detect_encoding_exception_handling(
        self, fs_utils: FileSystemUtils, exception_type: type, exception_message: str, expected_lm_call: str, mocker
    ) -> None:
        """Test detect_encoding exception handling with various exception types."""
        # Mock os.path.exists and os.path.isfile to return True, then raise exception on open
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("builtins.open", side_effect=exception_type(exception_message))

        success, result = fs_utils.detect_encoding("file.txt")

        assert success is False
        assert result == "mocked_message"
        fs_utils.lm.text.assert_called_with(expected_lm_call, error=exception_message)

    @pytest.mark.parametrize(
        "num_bytes_value",
        [512, 1024, 2048, 4096, 8192],
    )
    def test_detect_encoding_various_num_bytes(self, fs_utils: FileSystemUtils, num_bytes_value: int, mocker) -> None:
        """Test detect_encoding with various num_bytes values."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content for encoding detection")
            temp_file_path = temp_file.name

        try:
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = {"encoding": "utf-8"}

            mock_file = mocker.patch("builtins.open", mocker.mock_open(read_data=b"test data"))
            success, result = fs_utils.detect_encoding(temp_file_path, num_bytes=num_bytes_value)

            assert success is True
            mock_file.return_value.read.assert_called_with(num_bytes_value)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestFileSystemUtilsEdgeCases:
    """Edge cases and boundary condition tests for FileSystemUtils."""

    @pytest.fixture
    def fs_utils(self, mocker) -> FileSystemUtils:
        """Create FileSystemUtils instance for testing."""
        mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
        fs_utils = FileSystemUtils()
        fs_utils.lm = mocker.MagicMock()
        fs_utils.lm.text.return_value = "mocked_message"
        return fs_utils

    def test_detect_encoding_very_small_file(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test detect_encoding with very small file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("x")  # Single character
            temp_file_path = temp_file.name

        try:
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = {"encoding": "utf-8"}

            success, result = fs_utils.detect_encoding(temp_file_path)

            assert success is True
            assert result == "utf-8"
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_detect_encoding_empty_file(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test detect_encoding with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            # Create empty file
            temp_file_path = temp_file.name

        try:
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = {"encoding": "ascii"}

            success, result = fs_utils.detect_encoding(temp_file_path)

            assert success is True
            assert result == "ascii"
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_detect_encoding_binary_file(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test detect_encoding with binary file."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
            temp_file.write(b"\x89PNG\r\n\x1a\n")  # PNG file signature
            temp_file_path = temp_file.name

        try:
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = {"encoding": "utf-8"}

            success, result = fs_utils.detect_encoding(temp_file_path)

            assert success is True
            assert result == "utf-8"
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_create_directory_nested_path(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with nested directory structure."""
        fs_utils.lm.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            nested_dir = os.path.join(temp_parent, "level1", "level2", "level3")

            success, message = fs_utils.create_directory(nested_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(nested_dir)

    def test_create_directory_with_special_characters(self, fs_utils: FileSystemUtils) -> None:
        """Test create_directory with special characters in directory name."""
        fs_utils.lm.text.return_value = "directory_created_success"

        with tempfile.TemporaryDirectory() as temp_parent:
            special_dir = os.path.join(temp_parent, "test-dir_with.special@chars")

            success, message = fs_utils.create_directory(special_dir)

            assert success is True
            assert message == "directory_created_success"
            assert os.path.isdir(special_dir)

    def test_remove_file_readonly_file(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test remove_file with read-only file (simulated with OSError)."""
        fs_utils.lm.text.return_value = "remove_file_os_error"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Simulate read-only file by patching os.remove to raise OSError
            mocker.patch("os.remove", side_effect=OSError("Operation not permitted"))

            success, message = fs_utils.remove_file(temp_file_path)

            assert success is False
            assert message == "remove_file_os_error"
        finally:
            # Cleanup - remove the file if it still exists
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_check_directory_is_empty_with_hidden_files(self, fs_utils: FileSystemUtils) -> None:
        """Test check_directory_is_empty with hidden files."""
        fs_utils.lm.text.return_value = "dir_not_empty_message"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create hidden file
            hidden_file = os.path.join(temp_dir, ".hidden_file")
            with open(hidden_file, "w") as f:
                f.write("hidden content")

            is_empty, message = fs_utils.check_directory_is_empty(temp_dir)

            assert is_empty is False
            assert message == "dir_not_empty_message"

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
        fs_utils.lm = mocker.MagicMock()
        fs_utils.lm.text.return_value = "mocked_message"
        return fs_utils

    def test_complete_file_workflow(self, fs_utils: FileSystemUtils, mocker) -> None:
        """Test complete workflow: create file, check exists, detect encoding, remove file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_file.txt")

            # Create file
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("Test content with UTF-8 encoding: áéíóú")

            # Check file exists
            exists, messages = fs_utils.check_file_exists(test_file)
            assert exists is True
            assert messages == []

            # Detect encoding
            mock_detect = mocker.patch("chardet.detect")
            mock_detect.return_value = {"encoding": "utf-8"}
            success, encoding = fs_utils.detect_encoding(test_file)
            assert success is True
            assert encoding == "utf-8"

            # Remove file
            fs_utils.lm.text.return_value = "file_removed_success"
            success, message = fs_utils.remove_file(test_file)
            assert success is True
            assert not os.path.exists(test_file)

    def test_complete_directory_workflow(self, fs_utils: FileSystemUtils) -> None:
        """Test complete workflow: create directory, check exists, check empty, populate, check not empty."""
        with tempfile.TemporaryDirectory() as temp_parent:
            test_dir = os.path.join(temp_parent, "test_directory")

            # Create directory
            fs_utils.lm.text.return_value = "directory_created_success"
            success, message = fs_utils.create_directory(test_dir)
            assert success is True
            assert os.path.isdir(test_dir)

            # Check directory exists
            exists, message = fs_utils.check_directory_exists(test_dir)
            assert exists is True
            assert message == ""

            # Check directory is empty
            fs_utils.lm.text.return_value = "dir_empty_message"
            is_empty, message = fs_utils.check_directory_is_empty(test_dir)
            assert is_empty is True

            # Add file to directory
            test_file = os.path.join(test_dir, "content.txt")
            with open(test_file, "w") as f:
                f.write("directory content")

            # Check directory is not empty
            fs_utils.lm.text.return_value = "dir_not_empty_message"
            is_empty, message = fs_utils.check_directory_is_empty(test_dir)
            assert is_empty is False

    def test_error_recovery_workflow(self, fs_utils: FileSystemUtils) -> None:
        """Test workflow with error scenarios and recovery."""
        # Test with non-existent file
        non_existent = "/path/that/does/not/exist.txt"

        # Check file exists - should fail
        fs_utils.lm.text.return_value = "file_not_found_error"
        exists, messages = fs_utils.check_file_exists(non_existent)
        assert exists is False
        assert len(messages) == 1

        # Try to remove non-existent file - should succeed (no-op)
        fs_utils.lm.text.return_value = "file_not_found_info"
        success, message = fs_utils.remove_file(non_existent)
        assert success is True  # Remove returns True for non-existent files

        # Try to detect encoding - should fail
        fs_utils.lm.text.return_value = "file_not_found_error"
        success, result = fs_utils.detect_encoding(non_existent)
        assert success is False

    def test_multilingual_message_integration(self, fs_utils: FileSystemUtils) -> None:
        """Test that language manager is properly called with correct keys."""
        # Test various operations to ensure lm.text is called with correct keys

        # Empty path test
        fs_utils.lm.text.reset_mock()
        fs_utils.detect_encoding("")
        fs_utils.lm.text.assert_called_with("fs_utils_error_file_path_empty")

        # Non-existent file test
        fs_utils.lm.text.reset_mock()
        fs_utils.remove_file("/non/existent/file.txt")
        fs_utils.lm.text.assert_called_with("fs_utils_info_file_not_found", filename="file.txt")

        # Empty directory name test
        fs_utils.lm.text.reset_mock()
        fs_utils.create_directory("")
        fs_utils.lm.text.assert_called_with("fs_utils_error_dir_path_empty")

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
