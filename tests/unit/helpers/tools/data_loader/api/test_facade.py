"""
Unit tests for facade.py module.

This module tests the DataLoaderModel and DataLoaderFacade classes functionality
including data model creation, file loading, error handling, and facade operations.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd
from pathlib import Path

from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade


class TestDataLoaderModel:
    """Test suite for DataLoaderModel class."""

    def test_initialization_success(self, mocker) -> None:
        """Test successful DataLoaderModel initialization."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        model = DataLoaderModel(input_folder="/test/folder", path=mock_path, df_data=df_data, read_success=True)

        assert model.input_folder == "/test/folder"
        assert model.path == mock_path
        assert model.df_data.equals(df_data)
        assert model.read_success is True
        assert model.exists_file is True
        assert model.name == "test_file"
        assert model.filename == "test_file.csv"
        assert model.extension == ".csv"
        assert model.header_type == "single"

    def test_initialization_with_double_header(self, mocker) -> None:
        """Test DataLoaderModel initialization with double header DataFrame."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        # Create DataFrame with MultiIndex columns (double header)
        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("A", "col1"), ("B", "col2")])

        model = DataLoaderModel(input_folder="/test/folder", path=mock_path, df_data=df_data, read_success=True)

        assert model.header_type == "double"

    def test_initialization_with_string_path(self, mocker) -> None:
        """Test DataLoaderModel initialization with string path."""
        string_path = "/test/path/file.csv"

        df_data = pd.DataFrame({"col1": [1, 2]})

        model = DataLoaderModel(input_folder="/test/folder", path=Path(string_path), df_data=df_data, read_success=True)

        assert model.path == Path(string_path)
        assert model.exists_file is False  # String path doesn't have exists() method

    def test_initialization_with_failed_read(self, mocker) -> None:
        """Test DataLoaderModel initialization with failed read."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame()

        model = DataLoaderModel(input_folder="/test/folder", path=mock_path, df_data=df_data, read_success=False)

        assert model.read_success is False
        assert model.exists_file is False

    def test_string_representation(self, mocker) -> None:
        """Test string representation of DataLoaderModel."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        model = DataLoaderModel(input_folder="/test/folder", path=mock_path, df_data=df_data, read_success=True)

        str_repr = str(model)

        assert "DataLoaderModel(test_file)" in str_repr
        assert "input_folder: /test/folder" in str_repr
        assert "name: test_file" in str_repr
        assert "filename: test_file.csv" in str_repr
        assert "extension: .csv" in str_repr
        assert "header_type: single" in str_repr
        assert "read_success: True" in str_repr
        assert "exists_file: True" in str_repr


class TestDataLoaderFacade:
    """Test suite for DataLoaderFacade class."""

    def test_initialization(self, mocker) -> None:
        """Test DataLoaderFacade initialization."""
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.FileScanner")
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.Config")

        facade = DataLoaderFacade("/test/input")

        assert facade.input_dir == Path("/test/input")
        assert facade.scanner is not None
        assert facade.config is not None

    def test_load_all_success(self, mocker) -> None:
        """Test successful loading of all files."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = (
            {"file1": Path("/test/file1.csv")},  # files_map
            [Path("/test/file1.qml")],  # qml_files
            [],  # missing_files
        )

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv"), "file2": ("required", "double", "xlsx")}

        # Setup reader mock
        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})

        # Setup strategy mock
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.DoubleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 0
        assert "file1" in data
        assert "file2" in data  # Missing file should be added as empty
        assert "qmls" in data
        assert isinstance(data["file1"], DataLoaderModel)
        assert data["file1"].read_success is True
        assert data["file2"].read_success is False  # Missing file

    def test_load_all_with_file_not_found_error(self, mocker) -> None:
        """Test load_all with FileNotFoundError."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise FileNotFoundError
        mock_reader.read.side_effect = FileNotFoundError("File not found")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Arquivo não encontrado no diretório" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_unicode_decode_error(self, mocker) -> None:
        """Test load_all with UnicodeDecodeError."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise UnicodeDecodeError
        mock_reader.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Erro de codificação do arquivo" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_parser_error(self, mocker) -> None:
        """Test load_all with pandas ParserError."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise ParserError
        mock_reader.read.side_effect = pd.errors.ParserError("Error tokenizing data")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Erro na estrutura da planilha" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_value_error(self, mocker) -> None:
        """Test load_all with ValueError."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise ValueError
        mock_reader.read.side_effect = ValueError("Invalid value")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Erro nos valores da planilha" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_io_error(self, mocker) -> None:
        """Test load_all with IOError."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise IOError
        mock_reader.read.side_effect = IOError("Permission denied")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Erro de entrada/saída ao ler o arquivo" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_general_exception(self, mocker) -> None:
        """Test load_all with general Exception."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader to raise general Exception
        mock_reader.read.side_effect = Exception("Unexpected error")

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 1
        assert "Erro inesperado ao processar o arquivo" in errors[0]
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_with_qml_files(self, mocker) -> None:
        """Test load_all with QML files."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, [Path("/test/file1.qml"), Path("/test/file2.qml")], [])  # qml_files

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv")}

        # Setup reader mock
        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.SingleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 0
        assert "qmls" in data
        assert len(data["qmls"]) == 2
        assert all(isinstance(qml, pd.DataFrame) for qml in data["qmls"])

    def test_load_all_with_double_header_strategy(self, mocker) -> None:
        """Test load_all with double header strategy."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_strategy = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.xlsx")}, [], [])

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "double", "xlsx")}

        # Setup reader mock
        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})

        # Setup mocks
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.DoubleHeaderStrategy", return_value=mock_strategy)
        mocker.patch("data_validate.helpers.tools.data_loader.api.facade.ReaderFactory.get_reader", return_value=mock_reader)

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 0
        assert "file1" in data
        assert data["file1"].read_success is True

    def test_load_all_with_unknown_header_type(self, mocker) -> None:
        """Test load_all with unknown header type (should skip)."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()

        # Setup scanner mock
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.qml")}, [], [])

        # Setup config mock with unknown header type
        mock_config.file_specs = {"file1": ("required", "unknown", "qml")}

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 0
        # file1 should be added as missing since it was skipped
        assert "file1" in data
        assert data["file1"].read_success is False

    def test_load_all_missing_files_handling(self, mocker) -> None:
        """Test load_all handles missing files correctly."""
        # Mock dependencies
        mock_scanner = mocker.MagicMock()
        mock_config = mocker.MagicMock()

        # Setup scanner mock with no files found
        mock_scanner.scan.return_value = ({}, [], [])  # No files found

        # Setup config mock
        mock_config.file_specs = {"file1": ("required", "single", "csv"), "file2": ("optional", "double", "xlsx")}

        # Create facade
        facade = DataLoaderFacade("/test/input")
        facade.scanner = mock_scanner
        facade.config = mock_config

        # Test load_all
        data, errors = facade.load_all

        assert len(errors) == 0
        assert "file1" in data
        assert "file2" in data
        assert data["file1"].read_success is False
        assert data["file2"].read_success is False
        assert data["file1"].path == Path("file1")
        assert data["file2"].path == Path("file2")
