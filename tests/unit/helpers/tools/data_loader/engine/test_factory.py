"""
Unit tests for factory.py module.

This module tests the ReaderFactory class functionality including
reader creation for different file types and error handling.
"""

import pytest
from pathlib import Path

from data_validate.helpers.tools.data_loader.engine.factory import ReaderFactory
from data_validate.helpers.tools.data_loader.common.exceptions import ReaderNotFoundError


class TestReaderFactory:
    """Test suite for ReaderFactory class."""

    def test_get_reader_csv_file(self, mocker) -> None:
        """Test get_reader creates CSVReader for CSV files."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.csv")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader
        assert isinstance(reader, CSVReader)

    def test_get_reader_xlsx_file(self, mocker) -> None:
        """Test get_reader creates ExcelReader for XLSX files."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.xlsx")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.excel_reader import ExcelReader
        assert isinstance(reader, ExcelReader)

    def test_get_reader_qml_file(self, mocker) -> None:
        """Test get_reader creates QMLReader for QML files."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.qml")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.qml_reader import QMLReader
        assert isinstance(reader, QMLReader)

    def test_get_reader_uppercase_extension(self, mocker) -> None:
        """Test get_reader handles uppercase extensions."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.CSV")  # Uppercase extension
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader
        assert isinstance(reader, CSVReader)

    def test_get_reader_unsupported_extension(self, mocker) -> None:
        """Test get_reader raises ReaderNotFoundError for unsupported extensions."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.txt")  # Unsupported extension
        
        with pytest.raises(ReaderNotFoundError) as exc_info:
            ReaderFactory.get_reader(file_path, mock_strategy)
        
        assert "Nenhum leitor para extensão '.txt'" in str(exc_info.value)

    def test_get_reader_no_extension(self, mocker) -> None:
        """Test get_reader raises ReaderNotFoundError for files without extension."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test")  # No extension
        
        with pytest.raises(ReaderNotFoundError) as exc_info:
            ReaderFactory.get_reader(file_path, mock_strategy)
        
        assert "Nenhum leitor para extensão ''" in str(exc_info.value)

    def test_get_reader_passes_strategy_to_reader(self, mocker) -> None:
        """Test get_reader passes header strategy to reader constructor."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("test.csv")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        # Verify that the reader was created with the correct strategy
        assert reader.header_strategy == mock_strategy

    def test_registry_contains_expected_readers(self) -> None:
        """Test that registry contains expected reader mappings."""
        expected_extensions = [".csv", ".xlsx", ".qml"]
        
        for ext in expected_extensions:
            assert ext in ReaderFactory._registry
            assert ReaderFactory._registry[ext] is not None

    def test_get_reader_with_path_object(self, mocker) -> None:
        """Test get_reader works with Path objects."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("/absolute/path/to/test.csv")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader
        assert isinstance(reader, CSVReader)

    def test_get_reader_with_relative_path(self, mocker) -> None:
        """Test get_reader works with relative paths."""
        mock_strategy = mocker.MagicMock()
        
        file_path = Path("relative/path/test.xlsx")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)
        
        from data_validate.helpers.tools.data_loader.readers.excel_reader import ExcelReader
        assert isinstance(reader, ExcelReader)
