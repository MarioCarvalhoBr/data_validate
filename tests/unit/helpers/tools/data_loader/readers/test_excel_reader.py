"""
Unit tests for excel_reader.py module.

This module tests the ExcelReader class functionality including
Excel file reading and header processing.
"""

import pandas as pd
from pathlib import Path

from data_validate.helpers.tools.data_loader.readers.excel_reader import ExcelReader


class TestExcelReader:
    """Test suite for ExcelReader class."""

    def test_initialization(self, mocker) -> None:
        """Test ExcelReader initialization."""
        file_path = Path("test.xlsx")
        header_strategy = mocker.MagicMock()

        reader = ExcelReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy == header_strategy

    def test_read_file_single_header(self, mocker) -> None:
        """Test reading Excel file with single header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        # Mock pandas read_excel
        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        result = reader._read_file()

        assert result.equals(expected_df)
        mock_strategy.get_header.assert_called_once_with(file_path)

    def test_read_file_double_header(self, mocker) -> None:
        """Test reading Excel file with double header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = [0, 1]

        # Mock pandas read_excel
        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        result = reader._read_file()

        assert result.equals(expected_df)
        mock_strategy.get_header.assert_called_once_with(file_path)

    def test_read_file_passes_correct_parameters_to_pandas(self, mocker) -> None:
        """Test that read_file passes correct parameters to pandas.read_excel."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_excel = mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_excel was called with correct parameters
        mock_read_excel.assert_called_once_with(file_path, header=0, dtype=str, engine="calamine")

    def test_read_file_with_list_header(self, mocker) -> None:
        """Test reading Excel file with list header (double header)."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = [0, 1]

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_excel = mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_excel was called with list header
        mock_read_excel.assert_called_once_with(file_path, header=[0, 1], dtype=str, engine="calamine")

    def test_read_file_with_none_header(self, mocker) -> None:
        """Test reading Excel file with None header."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = None

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_excel = mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_excel was called with None header
        mock_read_excel.assert_called_once_with(file_path, header=None, dtype=str, engine="calamine")

    def test_read_file_returns_dataframe(self, mocker) -> None:
        """Test that read_file returns a pandas DataFrame."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        result = reader._read_file()

        assert isinstance(result, pd.DataFrame)
        assert result.equals(expected_df)

    def test_read_file_with_string_path(self, mocker) -> None:
        """Test reading Excel file with string path."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_excel = mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = "test.xlsx"
        reader = ExcelReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_excel was called with string path
        mock_read_excel.assert_called_once_with(file_path, header=0, dtype=str, engine="calamine")

    def test_read_file_with_absolute_path(self, mocker) -> None:
        """Test reading Excel file with absolute path."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_excel = mocker.patch("pandas.read_excel", return_value=expected_df)

        file_path = Path("/absolute/path/test.xlsx")
        reader = ExcelReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_excel was called with absolute path
        mock_read_excel.assert_called_once_with(file_path, header=0, dtype=str, engine="calamine")
