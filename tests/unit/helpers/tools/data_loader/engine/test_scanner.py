"""
Unit tests for scanner.py module.

This module tests the FileScanner class functionality including
directory scanning, file detection, and missing file identification.

BUG-018/ARC-003: `FileScanner` no longer reads the deleted `data_loader.common.config.Config`
singleton; every test below constructs it with an explicit `sheet_specs`/`extensions` pair (real
`SheetSpec` fixtures, not mocks of a config object) instead of patching `Config`.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from pathlib import Path

from data_validate.helpers.tools.data_loader.engine.scanner import FileScanner
from data_validate.specs.sheet_specs import ColumnKind, ColumnSpec, HeaderLayout, SheetSpec

_DEFAULT_EXTENSIONS = (".csv", ".xlsx")


def _sheet_spec(name: str, required: bool) -> SheetSpec:
    """Build a minimal `SheetSpec` fixture; only `required` matters to `FileScanner`."""
    return SheetSpec(
        name=name,
        required=required,
        header=HeaderLayout.SINGLE,
        columns=(ColumnSpec(name="id", dtype="int", kind=ColumnKind.REQUIRED),),
        description="Fixture sheet for scanner tests.",
    )


class TestFileScanner:
    """Test suite for FileScanner class."""

    def test_initialization(self) -> None:
        """Test FileScanner initialization."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        directory = Path("/test/dir")
        scanner = FileScanner(directory, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        assert scanner.dir == directory
        assert scanner.sheet_specs == sheet_specs
        assert scanner.extensions == _DEFAULT_EXTENSIONS

    def test_initialization_defaults_to_sheet_specs_registry(self) -> None:
        """Without explicit args, FileScanner reads the real SHEET_SPECS/ALLOWED_EXTENSIONS."""
        from data_validate.specs.sheet_specs import ALLOWED_EXTENSIONS, SHEET_SPECS

        scanner = FileScanner(Path("/test/dir"))

        assert scanner.sheet_specs == SHEET_SPECS
        assert scanner.extensions == ALLOWED_EXTENSIONS

    def test_scan_finds_csv_files(self, mocker) -> None:
        """Test scan finds CSV files correctly."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_file
        assert len(ignored) == 0
        assert len(missing) == 0

    def test_scan_finds_xlsx_files(self, mocker) -> None:
        """Test scan finds XLSX files correctly."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".xlsx"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_file
        assert len(ignored) == 0
        assert len(missing) == 0

    def test_scan_ignores_qml_files(self, mocker) -> None:
        """BUG-015: `.qml` is not in `ALLOWED_EXTENSIONS`, so a `.qml` file is skipped entirely."""
        sheet_specs = {"file1": _sheet_spec("file1", required=False)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".qml"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert "file1" not in found
        assert len(ignored) == 0
        assert len(missing) == 0  # non-required file, absence is not "missing"

    def test_scan_prefers_csv_over_xlsx(self, mocker) -> None:
        """Test scan prefers CSV files over XLSX files, and records the losing path."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_csv = mocker.MagicMock()
        mock_csv.stem = "file1"
        mock_csv.suffix = ".csv"
        mock_xlsx = mocker.MagicMock()
        mock_xlsx.stem = "file1"
        mock_xlsx.suffix = ".xlsx"
        mock_dir.iterdir.return_value = [mock_csv, mock_xlsx]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_csv  # Should prefer CSV
        assert ignored["file1"] == mock_xlsx  # BUG-015: losing path is recorded, not dropped
        assert len(missing) == 0

    def test_scan_replaces_xlsx_with_csv(self, mocker) -> None:
        """Test scan replaces XLSX with CSV when CSV is found later, tracking the ignored xlsx."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_xlsx = mocker.MagicMock()
        mock_xlsx.stem = "file1"
        mock_xlsx.suffix = ".xlsx"
        mock_csv = mocker.MagicMock()
        mock_csv.stem = "file1"
        mock_csv.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_xlsx, mock_csv]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_csv  # Should be replaced with CSV
        assert ignored["file1"] == mock_xlsx
        assert len(missing) == 0

    def test_scan_ignores_unknown_files(self, mocker) -> None:
        """Test scan ignores files not in sheet_specs."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "unknown_file"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert len(found) == 0
        assert len(ignored) == 0
        assert "file1" in missing  # Required file is missing

    def test_scan_ignores_unsupported_extensions(self, mocker) -> None:
        """Test scan ignores files with unsupported extensions."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".txt"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert len(found) == 0
        assert len(ignored) == 0
        assert "file1" in missing

    def test_scan_identifies_missing_required_files(self, mocker) -> None:
        """Test scan identifies missing required files."""
        sheet_specs = {
            "file1": _sheet_spec("file1", required=True),
            "file2": _sheet_spec("file2", required=False),
            "file3": _sheet_spec("file3", required=True),
        }

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert "file1" in found
        assert "file2" not in found
        assert "file3" not in found
        assert len(ignored) == 0
        assert "file3" in missing
        assert "file2" not in missing

    def test_scan_handles_case_insensitive_extensions(self, mocker) -> None:
        """Test scan handles case insensitive extensions."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".CSV"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_file
        assert len(ignored) == 0
        assert len(missing) == 0

    def test_scan_empty_directory(self, mocker) -> None:
        """Test scan with empty directory."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_dir.iterdir.return_value = []

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert len(found) == 0
        assert len(ignored) == 0
        assert "file1" in missing

    def test_scan_two_non_csv_duplicates_keeps_first_and_ignores_second(self, mocker) -> None:
        """Neither duplicate is CSV: the first file found is kept, the second is ignored."""
        sheet_specs = {"file1": _sheet_spec("file1", required=True)}

        mock_dir = mocker.MagicMock()
        mock_xlsx_1 = mocker.MagicMock()
        mock_xlsx_1.stem = "file1"
        mock_xlsx_1.suffix = ".xlsx"
        mock_xlsx_2 = mocker.MagicMock()
        mock_xlsx_2.stem = "file1"
        mock_xlsx_2.suffix = ".xlsx"
        mock_dir.iterdir.return_value = [mock_xlsx_1, mock_xlsx_2]

        scanner = FileScanner(mock_dir, sheet_specs=sheet_specs, extensions=_DEFAULT_EXTENSIONS)

        found, ignored, missing = scanner.scan()

        assert found["file1"] == mock_xlsx_1
        assert ignored["file1"] == mock_xlsx_2
