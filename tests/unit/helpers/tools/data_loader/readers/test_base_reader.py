"""
Unit tests for base_reader.py module.

This module tests the BaseReader abstract class functionality including
initialization and template method pattern.
"""

import pytest
from pathlib import Path
from data_validate.helpers.tools.data_loader.readers.base_reader import BaseReader


class ConcreteReader(BaseReader):
    """Concrete implementation of BaseReader for testing."""

    def _read_file(self):
        return "test_data"


class TestBaseReader:
    """Test suite for BaseReader class."""

    def test_initialization(self, mocker) -> None:
        """Test BaseReader initialization."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        reader = ConcreteReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy == header_strategy

    def test_read_calls_read_file(self, mocker) -> None:
        """Test that read method calls _read_file."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        reader = ConcreteReader(file_path, header_strategy)
        result = reader.read()

        assert result == "test_data"

    def test_read_file_is_abstract(self, mocker) -> None:
        """Test that _read_file is abstract and must be implemented."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        # Cannot instantiate BaseReader directly
        with pytest.raises(TypeError):
            BaseReader(file_path, header_strategy)

    def test_initialization_with_string_path(self, mocker) -> None:
        """Test BaseReader initialization with string path."""
        file_path = "test.csv"
        header_strategy = mocker.MagicMock()

        reader = ConcreteReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy == header_strategy

    def test_initialization_with_none_strategy(self) -> None:
        """Test BaseReader initialization with None strategy."""
        file_path = Path("test.csv")
        header_strategy = None

        reader = ConcreteReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy is None

    def test_read_returns_abstract_method_result(self, mocker) -> None:
        """Test that read method returns the result of _read_file."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        reader = ConcreteReader(file_path, header_strategy)
        result = reader.read()

        # Should return the result from the concrete _read_file implementation
        assert result == "test_data"

    def test_template_method_pattern(self, mocker) -> None:
        """Test that BaseReader follows template method pattern."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        reader = ConcreteReader(file_path, header_strategy)

        # The read method should delegate to _read_file
        # This is the template method pattern
        result = reader.read()
        assert result is not None
