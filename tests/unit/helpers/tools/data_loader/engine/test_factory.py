"""
Unit tests for factory.py module.

This module tests the ReaderFactory class functionality including
reader creation for different file types and error handling.

BUG-015: `.qml`/`QMLReader` were removed (ADR-0003); `test_get_reader_qml_file` and the `.qml`
entry in `test_registry_contains_expected_readers` are deleted along with them.
BUG-018: `ReaderFactory.get_reader` now takes an explicit `sep` and passes it only to `CSVReader`.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

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

    def test_get_reader_csv_file_uses_default_separator(self, mocker) -> None:
        """Without an explicit `sep`, CSVReader gets the protocol default `|` (BUG-018)."""
        mock_strategy = mocker.MagicMock()

        reader = ReaderFactory.get_reader(Path("test.csv"), mock_strategy)

        assert reader.sep == "|"

    def test_get_reader_csv_file_passes_explicit_separator(self, mocker) -> None:
        """`sep` from the caller (the sheet's `SheetSpec.csv_separator`) reaches `CSVReader`."""
        mock_strategy = mocker.MagicMock()

        reader = ReaderFactory.get_reader(Path("test.csv"), mock_strategy, sep=";")

        assert reader.sep == ";"

    def test_get_reader_xlsx_file(self, mocker) -> None:
        """Test get_reader creates ExcelReader for XLSX files."""
        mock_strategy = mocker.MagicMock()

        file_path = Path("test.xlsx")
        reader = ReaderFactory.get_reader(file_path, mock_strategy)

        from data_validate.helpers.tools.data_loader.readers.excel_reader import ExcelReader

        assert isinstance(reader, ExcelReader)

    def test_get_reader_xlsx_file_ignores_sep(self, mocker) -> None:
        """`sep` is meaningless for XLSX and is not passed to `ExcelReader`'s constructor."""
        mock_strategy = mocker.MagicMock()

        reader = ReaderFactory.get_reader(Path("test.xlsx"), mock_strategy, sep=";")

        assert not hasattr(reader, "sep")

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

    def test_get_reader_qml_extension_is_no_longer_supported(self, mocker) -> None:
        """BUG-015: `.qml` was removed from the registry along with `QMLReader`."""
        mock_strategy = mocker.MagicMock()

        with pytest.raises(ReaderNotFoundError) as exc_info:
            ReaderFactory.get_reader(Path("test.qml"), mock_strategy)

        assert "Nenhum leitor para extensão '.qml'" in str(exc_info.value)

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
        expected_extensions = [".csv", ".xlsx"]

        assert set(ReaderFactory._registry) == set(expected_extensions)
        for ext in expected_extensions:
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
