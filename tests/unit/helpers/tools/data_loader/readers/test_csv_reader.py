"""
Unit tests for csv_reader.py module.

This module tests the CSVReader class functionality including
CSV file reading, header processing, and separator handling.

BUG-018: `CSVReader` no longer reads the deleted `data_loader.common.config.Config` singleton to
guess a separator from the file stem; every test below passes `sep` explicitly to the constructor,
mirroring how `DataLoaderFacade` derives it from the sheet's `SheetSpec.csv_separator`.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import numpy as np
import pandas as pd
from pathlib import Path

from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader, _drop_trailing_blank_rows
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

    def test_initialization_defaults_separator_to_protocol_pipe(self, mocker) -> None:
        """Without an explicit `sep`, the reader defaults to the protocol's `|` (BUG-018)."""
        reader = CSVReader(Path("test.csv"), mocker.MagicMock())

        assert reader.sep == "|"

    def test_initialization_stores_explicit_separator(self, mocker) -> None:
        """An explicit `sep` (as the facade passes from `SheetSpec.csv_separator`) is stored."""
        reader = CSVReader(Path("test.csv"), mocker.MagicMock(), sep=";")

        assert reader.sep == ";"

    def test_read_file_single_header(self, mocker) -> None:
        """Test reading CSV file with single header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        # Mock pandas read_csv
        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mocker.patch("pandas.read_csv", return_value=expected_df)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=",")

        result = reader._read_file()

        assert result.equals(expected_df)
        mock_strategy.get_header.assert_called_once_with(file_path)

    def test_read_file_double_header_strategy(self, mocker) -> None:
        """Test reading CSV file with double header strategy."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]

        # Create DataFrame with MultiIndex columns
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "col1"), ("", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=",")

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

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=";")

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

        expected_df = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy)

        reader._read_file()

        # Check that pandas.read_csv was called with the default (protocol) separator
        mock_read_csv.assert_called_once()
        call_args = mock_read_csv.call_args
        assert call_args[1]["sep"] == "|"

    def test_read_file_double_header_fills_unnamed_columns(self, mocker) -> None:
        """Test that double header strategy fills unnamed columns correctly."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]

        # Create DataFrame with MultiIndex columns containing unnamed columns
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"], "col3": ["x", "y"]})
        df_data.columns = pd.MultiIndex.from_tuples([("Group1", "col1"), ("Unnamed: 1_level_0", "col2"), ("", "col3")])

        mocker.patch("pandas.read_csv", return_value=df_data)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=",")

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

        # Create DataFrame with MultiIndex columns where first column is empty string
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("", "col1"), ("Group1", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=",")

        result = reader._read_file()

        # Check that NaN first column was replaced with default name
        level0_values = result.columns.get_level_values(0)
        assert level0_values[0] == "Unnamed: 0_level_0"

    def test_read_file_double_header_handles_empty_string_first_column(self, mocker) -> None:
        """Test that double header strategy handles empty string in first column."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock(spec=DoubleHeaderStrategy)
        mock_strategy.get_header.return_value = [0, 1]

        # Create DataFrame with MultiIndex columns where first column is empty string
        df_data = pd.DataFrame({"col1": ["1", "2"], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("", "col1"), ("Group1", "col2")])

        mocker.patch("pandas.read_csv", return_value=df_data)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=",")

        result = reader._read_file()

        # Check that empty string first column was replaced with default name
        level0_values = result.columns.get_level_values(0)
        assert level0_values[0] == "Unnamed: 0_level_0"

    def test_read_file_passes_correct_parameters_to_pandas(self, mocker) -> None:
        """Test that read_file passes correct parameters to pandas.read_csv."""
        # Mock dependencies
        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0

        expected_df = pd.DataFrame({"col1": ["1", "2"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)

        file_path = Path("test.csv")
        reader = CSVReader(file_path, mock_strategy, sep=";")

        reader._read_file()

        # Check that pandas.read_csv was called with correct parameters
        mock_read_csv.assert_called_once_with(
            file_path, header=0, sep=";", low_memory=False, dtype=str, skip_blank_lines=False
        )

    def test_read_file_descricao_uses_pipe_separator_from_spec(self, mocker) -> None:
        """`descricao` (per `SHEET_SPECS`) is read with `|`, sourced from the facade, not guessed."""
        from data_validate.specs.sheet_specs import SHEET_SPECS

        mock_strategy = mocker.MagicMock()
        mock_strategy.get_header.return_value = 0
        expected_df = pd.DataFrame({"codigo": ["1"]})
        mock_read_csv = mocker.patch("pandas.read_csv", return_value=expected_df)

        spec = SHEET_SPECS["descricao"]
        reader = CSVReader(Path("descricao.csv"), mock_strategy, sep=spec.csv_separator)
        reader._read_file()

        assert spec.csv_separator == "|"
        mock_read_csv.assert_called_once_with(
            Path("descricao.csv"), header=0, sep="|", low_memory=False, dtype=str, skip_blank_lines=False
        )


class TestDropTrailingBlankRows:
    """Unit tests for the BUG-029 trailing-blank-row trimming helper."""

    def test_empty_frame_is_returned_unchanged(self) -> None:
        """An already-empty frame is returned as-is."""
        df = pd.DataFrame()

        result = _drop_trailing_blank_rows(df)

        assert result is df

    def test_frame_with_no_blank_rows_is_unchanged(self) -> None:
        """A frame with no fully-NaN row at all is returned unchanged."""
        df = pd.DataFrame({"a": ["x", "y"], "b": ["1", "2"]})

        result = _drop_trailing_blank_rows(df)

        pd.testing.assert_frame_equal(result, df)

    def test_trailing_blank_rows_are_dropped(self) -> None:
        """One or more fully-NaN rows at the end are trimmed."""
        df = pd.DataFrame({"a": ["x", "y", np.nan, np.nan], "b": ["1", "2", np.nan, np.nan]})

        result = _drop_trailing_blank_rows(df)

        assert result.shape == (2, 2)
        assert result["a"].tolist() == ["x", "y"]

    def test_interior_blank_row_is_preserved(self) -> None:
        """A fully-NaN row that is not at the end is left untouched."""
        df = pd.DataFrame({"a": ["x", np.nan, "y"], "b": ["1", np.nan, "2"]})

        result = _drop_trailing_blank_rows(df)

        assert result.shape == (3, 2)
        assert pd.isna(result.loc[1, "a"])

    def test_all_blank_frame_becomes_empty(self) -> None:
        """A frame that is fully blank end to end is trimmed down to zero rows."""
        df = pd.DataFrame({"a": [np.nan, np.nan], "b": [np.nan, np.nan]})

        result = _drop_trailing_blank_rows(df)

        assert result.shape == (0, 2)

    def test_partially_blank_trailing_row_is_kept(self) -> None:
        """A trailing row with at least one non-NaN cell is not dropped."""
        df = pd.DataFrame({"a": ["x", "y"], "b": ["1", np.nan]})

        result = _drop_trailing_blank_rows(df)

        assert result.shape == (2, 2)
