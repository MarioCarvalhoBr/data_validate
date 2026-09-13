"""
Unit tests for facade.py module.

This module tests the LoadedSheet and DataLoaderFacade classes functionality
including data model creation, file loading, error handling, and facade operations.

ARC-009/BUG-018/BUG-015: `DataLoaderFacade` no longer reads the deleted
`data_loader.common.config.Config` singleton; header layout and CSV separator come from
`data_validate.specs.sheet_specs.SHEET_SPECS`, patched per test via `mocker.patch(
"...facade.SHEET_SPECS", ...)` instead of mocking a `Config` instance. `load()` is the real method
under test; `load_all` is covered separately as a deprecated, warning-emitting alias. The `"qmls"`
key and its QML-specific tests are deleted along with `.qml` support (BUG-015).
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd
import pytest
from pathlib import Path

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet, DataLoaderFacade, LoadResult
from data_validate.specs.sheet_specs import ColumnKind, ColumnSpec, HeaderLayout, SheetSpec

FACADE_MODULE = "data_validate.helpers.tools.data_loader.api.facade"


def _fake_spec(name: str, header: HeaderLayout, csv_separator: str = "|", required: bool = True) -> SheetSpec:
    """Build a minimal `SheetSpec` fixture for facade tests."""
    return SheetSpec(
        name=name,
        required=required,
        header=header,
        columns=(ColumnSpec(name="id", dtype="int", kind=ColumnKind.REQUIRED),),
        description="Fixture sheet for facade tests.",
        csv_separator=csv_separator,
    )


class TestLoadedSheet:
    """Test suite for LoadedSheet class."""

    def test_initialization_success(self, mocker) -> None:
        """Test successful LoadedSheet initialization."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        model = LoadedSheet(input_folder="/test/folder", path=mock_path, raw_data=df_data, is_read_successful=True)

        assert model.input_folder == "/test/folder"
        assert model.path == mock_path
        assert model.raw_data.equals(df_data)
        assert model.is_read_successful is True
        assert model.does_file_exist is True
        assert model.name == "test_file"
        assert model.filename == "test_file.csv"
        assert model.extension == ".csv"
        assert model.header_type == "single"

    def test_initialization_with_double_header(self, mocker) -> None:
        """Test LoadedSheet initialization with double header DataFrame."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        # Create DataFrame with MultiIndex columns (double header)
        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        df_data.columns = pd.MultiIndex.from_tuples([("A", "col1"), ("B", "col2")])

        model = LoadedSheet(input_folder="/test/folder", path=mock_path, raw_data=df_data, is_read_successful=True)

        assert model.header_type == "double"

    def test_initialization_with_string_path(self, mocker) -> None:
        """Test LoadedSheet initialization with string path."""
        string_path = "/test/path/file.csv"

        df_data = pd.DataFrame({"col1": [1, 2]})

        model = LoadedSheet(
            input_folder="/test/folder", path=Path(string_path), raw_data=df_data, is_read_successful=True
        )

        assert model.path == Path(string_path)
        assert model.does_file_exist is False  # String path doesn't have exists() method

    def test_initialization_with_failed_read(self, mocker) -> None:
        """Test LoadedSheet initialization with failed read."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame()

        model = LoadedSheet(input_folder="/test/folder", path=mock_path, raw_data=df_data, is_read_successful=False)

        assert model.is_read_successful is False
        assert model.does_file_exist is False

    def test_string_representation(self, mocker) -> None:
        """Test string representation of LoadedSheet."""
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stem = "test_file"
        mock_path.name = "test_file.csv"
        mock_path.suffix = ".csv"

        df_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        model = LoadedSheet(input_folder="/test/folder", path=mock_path, raw_data=df_data, is_read_successful=True)

        str_repr = str(model)

        assert "LoadedSheet(test_file)" in str_repr
        assert "input_folder: /test/folder" in str_repr
        assert "name: test_file" in str_repr
        assert "filename: test_file.csv" in str_repr
        assert "extension: .csv" in str_repr
        assert "header_type: single" in str_repr
        assert "is_read_successful: True" in str_repr
        assert "does_file_exist: True" in str_repr


class TestDataLoaderModelDeprecatedAlias:
    """ARC-009/ARC-013: `DataLoaderModel` is kept one release as a plain alias for `LoadedSheet`."""

    def test_data_loader_model_is_the_same_object_as_loaded_sheet(self) -> None:
        """The alias is the identical class object, not a subclass or wrapper."""
        from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel

        assert DataLoaderModel is LoadedSheet


class TestDataLoaderFacade:
    """Test suite for DataLoaderFacade class."""

    @pytest.fixture(autouse=True)
    def _mock_small_file_stat(self, mocker) -> None:
        """Patch `Path.stat()` to report a small size (SEC-003).

        Every test below builds real (non-existent) `Path` objects for scanner results; without
        this, `path.stat()` (added by SEC-003's file-size guard) would raise `FileNotFoundError`
        before `reader.read()` is ever reached. Tests that specifically exercise the size limit
        override this patch within their own body.
        """
        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10))

    def test_initialization(self, mocker) -> None:
        """Test DataLoaderFacade initialization."""
        mocker.patch(f"{FACADE_MODULE}.FileScanner")

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)

        assert facade.input_dir == Path("/test/input")
        assert facade.scanner is not None

    def test_load_returns_load_result(self, mocker) -> None:
        """`load()` returns a `LoadResult`, reads every declared sheet and fills in missing ones."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {
            "file1": _fake_spec("file1", HeaderLayout.SINGLE),
            "file2": _fake_spec("file2", HeaderLayout.DOUBLE),
        }
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert isinstance(result, LoadResult)
        assert result.errors == []
        assert "file1" in result.models
        assert "file2" in result.models  # Missing file added as empty
        assert "qmls" not in result.models  # BUG-015: no QML concept left
        assert isinstance(result.models["file1"], LoadedSheet)
        assert result.models["file1"].is_read_successful is True
        assert result.models["file2"].is_read_successful is False  # Missing file

    def test_load_uses_separator_from_spec(self, mocker) -> None:
        """`ReaderFactory.get_reader` is called with the sheet's own `csv_separator` (BUG-018)."""
        mock_scanner = mocker.MagicMock()
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE, csv_separator=";")}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader = mocker.MagicMock()
        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})
        mock_get_reader = mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        facade.load()

        _, kwargs = mock_get_reader.call_args
        assert kwargs["sep"] == ";"

    def test_load_descricao_real_spec_uses_pipe_separator(self, mocker) -> None:
        """The real `descricao` entry of `SHEET_SPECS` declares `|` (BUG-018 regression guard)."""
        from data_validate.specs.sheet_specs import SHEET_SPECS

        mock_scanner = mocker.MagicMock()
        mock_scanner.scan.return_value = ({"descricao": Path("/test/descricao.csv")}, {}, [])

        mock_reader = mocker.MagicMock()
        mock_reader.read.return_value = pd.DataFrame({"codigo": [1]})
        mock_get_reader = mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        facade.load()

        assert SHEET_SPECS["descricao"].csv_separator == "|"
        _, kwargs = mock_get_reader.call_args
        assert kwargs["sep"] == "|"

    def test_load_uses_double_header_strategy_from_spec(self, mocker) -> None:
        """A sheet declared with `HeaderLayout.DOUBLE` gets a `DoubleHeaderStrategy`."""
        mock_scanner = mocker.MagicMock()
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.xlsx")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.DOUBLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_strategy = mocker.MagicMock()
        mocker.patch(f"{FACADE_MODULE}.DoubleHeaderStrategy", return_value=mock_strategy)

        mock_reader = mocker.MagicMock()
        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})
        mock_get_reader = mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert result.errors == []
        assert result.models["file1"].is_read_successful is True
        mock_get_reader.assert_called_once_with(Path("/test/file1.xlsx"), mock_strategy, sep="|")

    def test_load_with_file_not_found_error(self, mocker) -> None:
        """Test load with FileNotFoundError."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = FileNotFoundError("File not found")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert "Arquivo não encontrado no diretório" in result.errors[0]
        assert "file1" in result.models
        assert result.models["file1"].is_read_successful is False

    def test_load_with_unicode_decode_error(self, mocker) -> None:
        """Test load with UnicodeDecodeError."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert "Erro de codificação do arquivo" in result.errors[0]
        assert "file1" in result.models
        assert result.models["file1"].is_read_successful is False

    def test_load_with_parser_error(self, mocker) -> None:
        """Test load with pandas ParserError."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = pd.errors.ParserError("Error tokenizing data")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert "Erro na estrutura da planilha" in result.errors[0]
        assert "file1" in result.models
        assert result.models["file1"].is_read_successful is False

    def test_load_with_value_error(self, mocker) -> None:
        """Test load with ValueError."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = ValueError("Invalid value")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert "Erro nos valores da planilha" in result.errors[0]
        assert "file1" in result.models
        assert result.models["file1"].is_read_successful is False

    def test_load_with_io_error(self, mocker) -> None:
        """Test load with IOError."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = IOError("Permission denied")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert "Erro de entrada/saída ao ler o arquivo" in result.errors[0]
        assert "file1" in result.models
        assert result.models["file1"].is_read_successful is False

    def test_load_with_general_exception_propagates(self, mocker) -> None:
        """SEC-004: `load()` no longer has a final `except Exception` fallback -- a reader failure
        that isn't one of the specific expected types propagates out of `load()` instead of being
        downgraded to a per-file error message (it reaches `main()`'s boundary, exit code 2)."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.side_effect = RuntimeError("Unexpected error")
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        with pytest.raises(RuntimeError, match="Unexpected error"):
            facade.load()

    def test_load_missing_files_handling(self, mocker) -> None:
        """Test load handles missing files correctly."""
        mock_scanner = mocker.MagicMock()

        mock_scanner.scan.return_value = ({}, {}, [])  # No files found
        fake_specs = {
            "file1": _fake_spec("file1", HeaderLayout.SINGLE, required=True),
            "file2": _fake_spec("file2", HeaderLayout.DOUBLE, required=False),
        }
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        result = facade.load()

        assert result.errors == []
        assert "file1" in result.models
        assert "file2" in result.models
        assert result.models["file1"].is_read_successful is False
        assert result.models["file2"].is_read_successful is False
        assert result.models["file1"].path == Path("file1")
        assert result.models["file2"].path == Path("file2")


class TestDataLoaderFacadeLoadAllDeprecation:
    """`load_all` stays available for one release, but only as a deprecated wrapper (ARC-009)."""

    @pytest.fixture(autouse=True)
    def _mock_small_file_stat(self, mocker) -> None:
        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10))

    def test_load_all_emits_deprecation_warning(self, mocker) -> None:
        """Accessing `load_all` warns `DeprecationWarning` naming the replacement."""
        mock_scanner = mocker.MagicMock()
        mock_scanner.scan.return_value = ({}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        with pytest.warns(DeprecationWarning, match="load_all is deprecated"):
            _ = facade.load_all

    def test_load_all_returns_models_and_errors_tuple(self, mocker) -> None:
        """`load_all` still returns the historical `(models, errors)` tuple shape."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mock_reader.read.return_value = pd.DataFrame({"col1": [1, 2]})
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key)
        facade.scanner = mock_scanner

        with pytest.warns(DeprecationWarning):
            data, errors = facade.load_all

        assert errors == []
        assert isinstance(data, dict)
        assert data["file1"].is_read_successful is True


class TestDataLoaderFacadeSizeLimits:
    """SEC-003: `DataLoaderFacade.load()` enforces file-size and sheet-shape limits."""

    def test_default_construction_uses_pt_br_message_catalog_fallback(self) -> None:
        """`translate=None` falls back to a real `pt_BR` `MessageCatalog`, not a bare string."""
        facade = DataLoaderFacade("/test/input")

        assert facade._translate("loader_error_file_too_large", filename="x.csv", size_mb="1", limit_mb="1") == (
            "x.csv: O arquivo excede o tamanho máximo permitido (1 MB > 1 MB) e não será lido."
        )

    def test_default_limits_match_application_config_values(self) -> None:
        """Without an explicit `limits` tuple, the facade falls back to the SEC-003 defaults."""
        facade = DataLoaderFacade("/test/input")

        assert facade._max_file_bytes == 100 * 1024 * 1024
        assert facade._max_sheet_rows == 1_000_000
        assert facade._max_sheet_columns == 5_000

    def test_translate_callable_is_used_verbatim(self, mocker) -> None:
        """An explicit `translate` callable is stored and used as-is (no `MessageCatalog` built)."""
        recorded_calls = []

        def _record_translate(key: str, **params: object) -> str:
            recorded_calls.append((key, params))
            return f"<{key}>"

        mock_scanner = mocker.MagicMock()
        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10 * 1024 * 1024 * 1024))

        facade = DataLoaderFacade("/test/input", translate=_record_translate, limits=(1, 1_000_000, 5_000))
        facade.scanner = mock_scanner

        result = facade.load()

        assert result.errors == ["<loader_error_file_too_large>"]
        assert recorded_calls[0][0] == "loader_error_file_too_large"
        assert recorded_calls[0][1]["filename"] == "file1.csv"
        assert result.models["file1"].is_read_successful is False

    def test_file_exceeding_max_bytes_is_not_read_and_reports_error(self, mocker) -> None:
        """A file above `limits[0]` is never handed to the reader; the error names the file."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=1024))
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade(
            "/test/input", translate=lambda key, **params: key.format(**params), limits=(100, 1_000_000, 5_000)
        )
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert result.errors[0] == "loader_error_file_too_large"
        mock_reader.read.assert_not_called()
        assert result.models["file1"].is_read_successful is False
        assert result.models["file1"].raw_data.empty

    def test_file_within_max_bytes_is_read_normally(self, mocker) -> None:
        """A file at or below the byte limit is read as usual (no false positive)."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)
        mock_reader.read.return_value = pd.DataFrame({"col1": ["1", "2"]})

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=100))
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key, limits=(100, 1_000_000, 5_000))
        facade.scanner = mock_scanner

        result = facade.load()

        assert result.errors == []
        assert result.models["file1"].is_read_successful is True
        mock_reader.read.assert_called_once()

    def test_sheet_exceeding_max_rows_is_dropped_and_reports_error(self, mocker) -> None:
        """A frame read successfully but with too many rows is treated as unread."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)
        mock_reader.read.return_value = pd.DataFrame({"col1": ["1", "2", "3"]})

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10))
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade(
            "/test/input", translate=lambda key, **params: key.format(**params), limits=(1_000_000, 2, 5_000)
        )
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert result.errors[0] == "loader_error_sheet_too_big"
        assert result.models["file1"].is_read_successful is False
        assert result.models["file1"].raw_data.empty

    def test_sheet_exceeding_max_columns_is_dropped_and_reports_error(self, mocker) -> None:
        """A frame read successfully but with too many columns is treated as unread."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)
        mock_reader.read.return_value = pd.DataFrame({"a": ["1"], "b": ["2"], "c": ["3"]})

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10))
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade(
            "/test/input", translate=lambda key, **params: key.format(**params), limits=(1_000_000, 1_000_000, 2)
        )
        facade.scanner = mock_scanner

        result = facade.load()

        assert len(result.errors) == 1
        assert result.errors[0] == "loader_error_sheet_too_big"
        assert result.models["file1"].is_read_successful is False

    def test_sheet_within_limits_is_read_normally(self, mocker) -> None:
        """A frame within both the row and column limits is read as usual (no false positive)."""
        mock_scanner = mocker.MagicMock()
        mock_reader = mocker.MagicMock()

        mock_scanner.scan.return_value = ({"file1": Path("/test/file1.csv")}, {}, [])
        fake_specs = {"file1": _fake_spec("file1", HeaderLayout.SINGLE)}
        mocker.patch(f"{FACADE_MODULE}.SHEET_SPECS", fake_specs)
        mock_reader.read.return_value = pd.DataFrame({"col1": ["1", "2"]})

        mocker.patch.object(Path, "stat", return_value=mocker.MagicMock(st_size=10))
        mocker.patch(f"{FACADE_MODULE}.ReaderFactory.get_reader", return_value=mock_reader)

        facade = DataLoaderFacade("/test/input", translate=lambda key, **params: key, limits=(1_000_000, 100, 100))
        facade.scanner = mock_scanner

        result = facade.load()

        assert result.errors == []
        assert result.models["file1"].is_read_successful is True
