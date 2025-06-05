#  Copyright (c) 2025.

import pytest
from unittest.mock import patch, mock_open
from data_validate.common.utils.file_system_utils import (
    detect_encoding,
    create_directory,
    check_file_exists,
    check_directory_exists,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_get_text_locale():
    """Mock the get_text_locale function."""
    with patch("data_validate.common.utils.functions_io.get_text_locale") as mock_locale:
        mock_locale.side_effect = lambda key, **kwargs: f"{key} {kwargs}"
        yield mock_locale

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file = tmp_path / "test_file.txt"
    file.write_text("This is a test file.")
    return file

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    return dir_path

# =============================================================================
# Tests for detect_encoding
# =============================================================================

def test_detect_encoding_success(temp_file, mock_get_text_locale):
    with open(temp_file, "rb") as f:
        raw_data = f.read()
    with patch("builtins.open", mock_open(read_data=raw_data)), patch("chardet.detect", return_value={"encoding": "utf-8"}):
        success, encoding = detect_encoding(str(temp_file))
        assert success is True
        assert encoding == "utf-8"

@pytest.mark.parametrize("file_path", [None, ""])
def test_detect_encoding_invalid_path(file_path, mock_get_text_locale):
    success, message = detect_encoding(file_path)
    assert success is False
    assert "fs_utils_error_file_path_empty" in message

def test_detect_encoding_file_not_found(mock_get_text_locale):
    success, message = detect_encoding("non_existent_file.txt")
    assert success is False
    assert "fs_utils_error_file_not_found" in message

def test_detect_encoding_not_a_file(temp_dir, mock_get_text_locale):
    success, message = detect_encoding(str(temp_dir))
    assert success is False
    assert "fs_utils_error_path_not_file" in message

def test_detect_encoding_failure(mock_get_text_locale):
    with patch("os.path.isfile", return_value=True), \
         patch("builtins.open", side_effect=OSError("Test error")):
        success, message = detect_encoding("test_file.txt")
        assert success is False
        assert "fs_utils_error_file_not_found {'filename': 'test_file.txt'}" in message

# =============================================================================
# Tests for create_directory
# =============================================================================

def test_create_directory_success(mock_get_text_locale, tmp_path):
    dir_name = str(tmp_path / "new_dir")
    success, message = create_directory(dir_name)
    assert success is True
    assert "fs_utils_success_dir_created" in message

def test_create_directory_already_exists(temp_dir, mock_get_text_locale):
    success, message = create_directory(str(temp_dir))
    assert success is True
    assert "fs_utils_info_dir_exists" in message

def test_create_directory_path_not_dir(mock_get_text_locale, temp_file):
    success, message = create_directory(str(temp_file))
    assert success is False
    assert "fs_utils_error_path_not_dir" in message

def test_create_directory_invalid_path(mock_get_text_locale):
    success, message = create_directory("")
    assert success is False
    assert "fs_utils_error_dir_path_empty" in message

def test_create_directory_os_error_2(mock_get_text_locale):
    with patch("os.makedirs", side_effect=OSError("Test error")):
        success, message = create_directory("invalid_dir")
        assert success is False
        assert "fs_utils_error_create_dir_os" in message

# =============================================================================
# Tests for check_file_exists
# =============================================================================

def test_check_file_exists_success(temp_file, mock_get_text_locale):
    success, errors = check_file_exists(str(temp_file))
    assert success is True
    assert errors == []

def test_check_file_exists_not_found(mock_get_text_locale):
    success, errors = check_file_exists("non_existent_file.txt")
    assert success is False
    assert "fs_utils_error_file_not_found" in errors[0]

def test_check_file_exists_not_a_file(temp_dir, mock_get_text_locale):
    success, errors = check_file_exists(str(temp_dir))
    assert success is False
    assert "fs_utils_error_path_not_file" in errors[0]

def test_check_file_exists_invalid_path(mock_get_text_locale):
    success, errors = check_file_exists("")
    assert success is False
    assert "fs_utils_error_file_path_empty" in errors[0]

# =============================================================================
# Tests for check_directory_exists
# =============================================================================

def test_check_directory_exists_success(temp_dir, mock_get_text_locale):
    success, message = check_directory_exists(str(temp_dir))
    assert success is True
    assert message == ""

def test_check_directory_exists_not_found(mock_get_text_locale):
    success, message = check_directory_exists("non_existent_dir")
    assert success is False
    assert "fs_utils_error_dir_not_found" in message

def test_check_directory_exists_not_a_directory(temp_file, mock_get_text_locale):
    success, message = check_directory_exists(str(temp_file))
    assert success is False
    assert "fs_utils_error_path_not_dir" in message

def test_check_directory_exists_invalid_path(mock_get_text_locale):
    success, message = check_directory_exists("")
    assert success is False
    assert "fs_utils_error_dir_path_empty" in message


# =============================================================================
# Tests for detect_encoding
# =============================================================================

def test_detect_encoding_os_error(mock_get_text_locale):
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("builtins.open", side_effect=OSError("Test OSError")):
        success, message = detect_encoding("test_file.txt")
        assert success is False
        assert "fs_utils_error_encoding_os" in message

def test_detect_encoding_unexpected_error(mock_get_text_locale):
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("builtins.open", side_effect=Exception("Unexpected error")):
        success, message = detect_encoding("test_file.txt")
        assert success is False
        assert "fs_utils_error_unexpected" in message

# =============================================================================
# Tests for create_directory
# =============================================================================

def test_create_directory_os_error(mock_get_text_locale):
    with patch("os.makedirs", side_effect=OSError("Test OSError")):
        success, message = create_directory("invalid_dir")
        assert success is False
        assert "fs_utils_error_create_dir_os" in message

def test_create_directory_unexpected_error(mock_get_text_locale):
    with patch("os.makedirs", side_effect=Exception("Unexpected error")):
        success, message = create_directory("invalid_dir")
        assert success is False
        assert "fs_utils_error_unexpected" in message

# =============================================================================
# Tests for check_file_exists
# =============================================================================

def test_check_file_exists_unexpected_error(mock_get_text_locale):
    with patch("os.path.exists", side_effect=Exception("Unexpected error")):
        success, errors = check_file_exists("test_file.txt")
        assert success is False
        assert "fs_utils_error_file_check_fail" in errors[0]

# =============================================================================
# Tests for check_directory_exists
# =============================================================================

def test_check_directory_exists_unexpected_error(mock_get_text_locale):
    with patch("os.path.exists", side_effect=Exception("Unexpected error")):
        success, message = check_directory_exists("test_dir")
        assert success is False
        assert "fs_utils_error_dir_check_fail" in message

def test_detect_encoding_failed(mock_get_text_locale, temp_file):
    with patch("chardet.detect", return_value={"encoding": None}):
        success, message = detect_encoding(str(temp_file))
        assert success is False
        assert "fs_utils_error_encoding_failed" in message