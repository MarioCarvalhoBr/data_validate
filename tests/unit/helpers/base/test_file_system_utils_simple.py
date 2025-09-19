from unittest.mock import patch
from data_validate.helpers.base.file_system_utils import FileSystemUtils


def test_simple():
    """Simple test to check if test collection works."""
    assert True


class TestFileSystemUtils:
    """Simple test class."""

    def test_init(self):
        """Test initialization."""
        with patch("data_validate.helpers.base.file_system_utils.LanguageManager"):
            fs_utils = FileSystemUtils()
            assert fs_utils is not None
