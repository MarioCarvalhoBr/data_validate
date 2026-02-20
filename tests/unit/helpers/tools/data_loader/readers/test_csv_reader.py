"""
Unit tests for csv_reader.py module.

This module tests the CSVReader class functionality including
CSV file reading, header processing, and separator handling.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd
from pathlib import Path

from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader
from data_validate.helpers.tools.data_loader.strategies.header import DoubleHeaderStrategy


class TestCSVReader:
    """Test suite for CSVReader class."""

    def test_initialization(self, mocker) -> None:
        """Test CSVReader initialization."""
        file_path = Path("test.csv")
        header_strategy = mocker.MagicMock()

        reader = CSVReader(file_path, header_strategy)

        assert reader.file_path == file_path
        assert reader.header_strategy == header_strategy

    def test_read_file_single_header(self, mocker) -> None:
        """Test reading CSV file with single header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "single", ",")}

        # Mock pandas read_csv
        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mocker.patch("pandas.read_csv", return_value=expected_df)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        result = reader._read_file()

        assert result.equals(expected_df)
        mock_strategy.get_header.assert_called_once_with(file_path)

    def test_read_file_double_header_strategy(self, mocker) -> None:
        """Test reading CSV file with double header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "double", ",")}

        # Create DataFrame with MultiIndex columns
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "col1"), ("", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        result = reader._read_file()

        # Check that the result has MultiIndex columns
        assert isinstance(result.columns, pd.MultiIndex)
        # Check that unnamed columns were filled
        assert result.columns.get_level_values(0)[0] == "Unnamed: 0_level_0"

    def test_read_file_custom_separator(self, mocker) -> None:
        """Test reading CSV file with custom separator."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "single", ";")}

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_csv was called with correct separator
        mock_read_csv.assert_called_once()
        call_args = mock_read_csv.call_args
        assert call_args[1]["sep"] == ";"

    def test_read_file_default_separator(self, mocker) -> None:
        """Test reading CSV file with default separator when not specified."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "single", None)}

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_csv was called with default separator
        mock_read_csv.assert_called_once()
        call_args = mock_read_csv.call_args
        assert call_args[1]["sep"] == ","

    def test_read_file_no_file_specs(self, mocker) -> None:
        """Test reading CSV file when file is not in file_specs."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {}  # Empty file_specs

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_csv was called with default separator
        mock_read_csv.assert_called_once()
        call_args = mock_read_csv.call_args
        assert call_args[1]["sep"] == ","

    def test_read_file_double_header_fills_unnamed_columns(self, mocker) -> None:
        """Test that double header strategy fills unnamed columns correctly."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "double", ",")}

        # Create DataFrame with MultiIndex columns containing unnamed columns
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"], "col3": ["x", "y"]})
        df_data.columns = pd.MultiIndex.from_tuples([("Group1", "col1"), ("Unnamed: 1_level_0", "col2"), ("", "col3")])

        mocker.patch("pandas.read_csv", return_value=df_data)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        result = reader._read_file()

        # Check that unnamed columns were filled
        level0_values = result.columns.get_level_values(0)
        assert level0_values[0] == "Group1"  # Should remain unchanged
        assert level0_values[1] == "Group1"  # Should be filled from previous
        assert level0_values[2] == "Group1"  # Should be filled from previous

    def test_read_file_double_header_handles_nan_first_column(self, mocker) -> None:
        """Test that double header strategy handles NaN in first column."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "double", ",")}

        # Create DataFrame with MultiIndex columns where first column is empty string
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("", "col1"), ("Group1", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        result = reader._read_file()

        # Check that NaN first column was replaced with default name
        level0_values = result.columns.get_level_values(0)
        assert level0_values[0] == "Unnamed: 0_level_0"

    def test_read_file_double_header_handles_empty_string_first_column(self, mocker) -> None:
        """Test that double header strategy handles empty string in first column."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "double", ",")}

        # Create DataFrame with MultiIndex columns where first column is empty string
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("", "col1"), ("Group1", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        result = reader._read_file()

        # Check that empty string first column was replaced with default name
        level0_values = result.columns.get_level_values(0)
        assert level0_values[0] == "Unnamed: 0_level_0"

    def test_read_file_passes_correct_parameters_to_pandas(self, mocker) -> None:
        """Test that read_file passes correct parameters to pandas.read_csv."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"test": ("required", "single", ";")}

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)
        mocker.patch("data_validate.helpers.tools.data_loader.readers.csv_reader.Config", return_value=mock_config)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_csv was called with correct parameters
        mock_read_csv.assert_called_once_with(file_path, header=0, sep=";", low_memory=False, dtype=str)
