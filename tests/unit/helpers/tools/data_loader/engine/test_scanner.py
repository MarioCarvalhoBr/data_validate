"""
Unit tests for scanner.py module.

This module tests the FileScanner class functionality including
directory scanning, file detection, and missing file identification.
"""

from pathlib import Path

from data_validate.helpers.tools.data_loader.engine.scanner import FileScanner


class TestFileScanner:
    """Test suite for FileScanner class."""

    def test_initialization(self, mocker) -> None:
        """Test FileScanner initialization."""
        mock_config = mocker.patch("data_validate.helpers.tools.data_loader.engine.scanner.Config")
        mock_config.return_value.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.return_value.extensions = [".csv", ".xlsx", ".qml"]

        directory = Path("/test/dir")
        scanner = FileScanner(directory)

        assert scanner.dir == directory
        assert scanner.config is not None

    def test_scan_finds_csv_files(self, mocker) -> None:
        """Test scan finds CSV files correctly."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with CSV file
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert found["file1"] == mock_file
        assert len(qmls) == 0
        assert len(missing) == 0

    def test_scan_finds_xlsx_files(self, mocker) -> None:
        """Test scan finds XLSX files correctly."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "xlsx")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with XLSX file
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".xlsx"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert found["file1"] == mock_file
        assert len(qmls) == 0
        assert len(missing) == 0

    def test_scan_finds_qml_files(self, mocker) -> None:
        """Test scan finds QML files correctly."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": (False, "single", "qml")}  # Use False for non-required QML files
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with QML file
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".qml"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" not in found  # QML files go to qmls list
        assert len(qmls) == 1
        assert qmls[0] == mock_file
        assert len(missing) == 0  # Non-required files don't appear in missing

    def test_scan_prefers_csv_over_xlsx(self, mocker) -> None:
        """Test scan prefers CSV files over XLSX files."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with both CSV and XLSX files
        mock_dir = mocker.MagicMock()
        mock_csv = mocker.MagicMock()
        mock_csv.stem = "file1"
        mock_csv.suffix = ".csv"
        mock_xlsx = mocker.MagicMock()
        mock_xlsx.stem = "file1"
        mock_xlsx.suffix = ".xlsx"
        mock_dir.iterdir.return_value = [mock_csv, mock_xlsx]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert found["file1"] == mock_csv  # Should prefer CSV
        assert len(qmls) == 0
        assert len(missing) == 0

    def test_scan_replaces_xlsx_with_csv(self, mocker) -> None:
        """Test scan replaces XLSX with CSV when CSV is found later."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with XLSX first, then CSV
        mock_dir = mocker.MagicMock()
        mock_xlsx = mocker.MagicMock()
        mock_xlsx.stem = "file1"
        mock_xlsx.suffix = ".xlsx"
        mock_csv = mocker.MagicMock()
        mock_csv.stem = "file1"
        mock_csv.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_xlsx, mock_csv]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert found["file1"] == mock_csv  # Should be replaced with CSV
        assert len(qmls) == 0
        assert len(missing) == 0

    def test_scan_ignores_unknown_files(self, mocker) -> None:
        """Test scan ignores files not in file_specs."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with unknown file
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "unknown_file"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert len(found) == 0
        assert len(qmls) == 0
        assert "file1" in missing  # Required file is missing

    def test_scan_ignores_unsupported_extensions(self, mocker) -> None:
        """Test scan ignores files with unsupported extensions."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with unsupported extension
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".txt"  # Unsupported extension
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert len(found) == 0
        assert len(qmls) == 0
        assert "file1" in missing  # Required file is missing

    def test_scan_identifies_missing_required_files(self, mocker) -> None:
        """Test scan identifies missing required files."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {
            "file1": (True, "single", "csv"),  # Required file
            "file2": (False, "single", "csv"),  # Optional file
            "file3": (True, "single", "csv"),  # Required file
        }
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with only one required file
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".csv"
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert "file2" not in found  # Optional file
        assert "file3" not in found  # Required file
        assert len(qmls) == 0
        assert "file3" in missing  # Only required missing files
        assert "file2" not in missing  # Optional files not in missing

    def test_scan_handles_case_insensitive_extensions(self, mocker) -> None:
        """Test scan handles case insensitive extensions."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with uppercase extension
        mock_dir = mocker.MagicMock()
        mock_file = mocker.MagicMock()
        mock_file.stem = "file1"
        mock_file.suffix = ".CSV"  # Uppercase extension
        mock_dir.iterdir.return_value = [mock_file]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert "file1" in found
        assert found["file1"] == mock_file
        assert len(qmls) == 0
        assert len(missing) == 0

    def test_scan_empty_directory(self, mocker) -> None:
        """Test scan with empty directory."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": ("required", "single", "csv")}
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock empty directory
        mock_dir = mocker.MagicMock()
        mock_dir.iterdir.return_value = []

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert len(found) == 0
        assert len(qmls) == 0
        assert "file1" in missing

    def test_scan_multiple_qml_files(self, mocker) -> None:
        """Test scan with multiple QML files."""
        # Mock config
        mock_config = mocker.MagicMock()
        mock_config.file_specs = {"file1": (False, "single", "qml"), "file2": (False, "single", "qml")}  # Non-required QML files
        mock_config.extensions = [".csv", ".xlsx", ".qml"]

        # Mock directory with multiple QML files
        mock_dir = mocker.MagicMock()
        mock_qml1 = mocker.MagicMock()
        mock_qml1.stem = "file1"
        mock_qml1.suffix = ".qml"
        mock_qml2 = mocker.MagicMock()
        mock_qml2.stem = "file2"
        mock_qml2.suffix = ".qml"
        mock_dir.iterdir.return_value = [mock_qml1, mock_qml2]

        scanner = FileScanner(mock_dir)
        scanner.config = mock_config

        found, qmls, missing = scanner.scan()

        assert len(found) == 0
        assert len(qmls) == 2
        assert mock_qml1 in qmls
        assert mock_qml2 in qmls
        assert len(missing) == 0  # Non-required files don't appear in missing
