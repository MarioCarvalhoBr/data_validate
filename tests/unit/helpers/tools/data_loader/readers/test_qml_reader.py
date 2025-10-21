"""
Unit tests for qml_reader.py module.

This module tests the QMLReader class functionality including
QML file reading and text content retrieval.
"""

from pathlib import Path

from data_validate.helpers.tools.data_loader.readers.qml_reader import QMLReader


class TestQMLReader:
    """Test suite for QMLReader class."""

    def test_initialization(self, mocker) -> None:
        """Test QMLReader initialization."""
        file_path = Path("test.qml")
        header_strategy = mocker.MagicMock()

        reader = QMLReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy == header_strategy

    def test_read_file_returns_text_content(self, mocker) -> None:
        """Test that read_file returns text content of QML file."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML file content"

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert result == "QML file content"
        mock_path.read_text.assert_called_once()

    def test_read_file_with_string_path(self, mocker) -> None:
        """Test reading QML file with string path."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML content"

        # Mock Path constructor to return our mock
        mocker.patch("pathlib.Path", return_value=mock_path)

        header_strategy = mocker.MagicMock()
        reader = QMLReader(Path("test.qml"), header_strategy)

        # Mock the file_path attribute to use our mock
        reader.file_path = mock_path

        result = reader._read_file()

        assert result == "QML content"
        mock_path.read_text.assert_called_once()

    def test_read_file_with_path_object(self, mocker) -> None:
        """Test reading QML file with Path object."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML content from Path object"

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert result == "QML content from Path object"
        mock_path.read_text.assert_called_once()

    def test_read_file_returns_string(self, mocker) -> None:
        """Test that read_file returns a string."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML file content"

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert isinstance(result, str)
        assert result == "QML file content"

    def test_read_file_with_empty_content(self, mocker) -> None:
        """Test reading QML file with empty content."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = ""

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert result == ""
        mock_path.read_text.assert_called_once()

    def test_read_file_with_multiline_content(self, mocker) -> None:
        """Test reading QML file with multiline content."""
        # Mock file path
        multiline_content = """<?xml version="1.0" encoding="UTF-8"?>
<qgis>
  <pipe>
    <rasterrenderer>
    </rasterrenderer>
  </pipe>
</qgis>"""
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = multiline_content

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert result == multiline_content
        mock_path.read_text.assert_called_once()

    def test_read_file_ignores_header_strategy(self, mocker) -> None:
        """Test that read_file ignores header strategy (QML files don't have headers)."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML content"

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        # Header strategy should not be used for QML files
        header_strategy.get_header.assert_not_called()
        assert result == "QML content"

    def test_read_file_with_unicode_content(self, mocker) -> None:
        """Test reading QML file with unicode content."""
        # Mock file path
        unicode_content = "QML content with unicode: 中文, émojis 🎉"
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = unicode_content

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        result = reader._read_file()

        assert result == unicode_content
        mock_path.read_text.assert_called_once()

    def test_read_file_calls_read_text_once(self, mocker) -> None:
        """Test that read_file calls read_text exactly once."""
        # Mock file path
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "QML content"

        header_strategy = mocker.MagicMock()
        reader = QMLReader(mock_path, header_strategy)

        reader._read_file()

        # Should call read_text exactly once
        assert mock_path.read_text.call_count == 1
