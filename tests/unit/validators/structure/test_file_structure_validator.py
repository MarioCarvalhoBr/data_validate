#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for FileStructureValidator (BUG-026)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.base.file_system_utils import FileSystemUtils
from data_validate.validators.structure.file_structure_validator import FileStructureValidator


def _build_data_models_context(
    mocker,
    input_folder: Path,
    expected_files: dict[str, list[str]],
    optional_files: dict[str, list[str]] | None = None,
):
    """Build a mocked `DataModelContext` wired for `FileStructureValidator`.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    input_folder : Path
        Real, on-disk directory the validator will `os.listdir` and probe
        with a real `FileSystemUtils` instance.
    expected_files : dict[str, list[str]]
        Stand-in for `SpreadsheetInfo.EXPECTED_FILES`.
    optional_files : dict[str, list[str]] | None
        Stand-in for `SpreadsheetInfo.OPTIONAL_FILES`.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` whose `.context` carries a real
        `FileSystemUtils` (so the boolean file/dir checks reflect the real
        filesystem) and a mocked `language_manager.text` that returns the
        message key unchanged, so assertions can target the key/kwargs used
        instead of a fully rendered pt-BR/en-US sentence.
    """
    description_model = mocker.MagicMock()
    description_model.filename = "descricao.csv"
    description_raw_data = pd.DataFrame({"codigo": [1]})
    description_model.data_loader_model.raw_data = description_raw_data
    # `BaseValidator` reads the model's own working frame (`.frame`), not
    # `data_loader_model.raw_data` (BUG-003, see `SpModelABC.frame`).
    description_model.frame = description_raw_data

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.return_value = description_model
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }
    data_models_context.context.data_args.data_file.input_folder = str(input_folder)
    data_models_context.context.config.spreadsheet_info.EXPECTED_FILES = expected_files
    data_models_context.context.config.spreadsheet_info.OPTIONAL_FILES = optional_files or {}
    data_models_context.context.file_system_utils = FileSystemUtils()
    data_models_context.context.language_manager.text = mocker.MagicMock(side_effect=lambda key, **kwargs: key)

    return data_models_context


def _build_validator(mocker, data_models_context) -> FileStructureValidator:
    """Instantiate a `FileStructureValidator` (construction triggers `run()`, ARC-001)."""
    return FileStructureValidator(data_models_context=data_models_context, validation_reports=ValidationReport())


class TestFileStructureValidatorInstanceState:
    """Regression tests for BUG-026: duplicate `errors`/`warnings` instance state."""

    def test_validator_has_no_duplicate_errors_warnings_attributes(self, mocker, tmp_path):
        """`errors`/`warnings` must not exist as separate instance attributes any more."""
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "composicao.csv").touch()
        (tmp_path / "valores.csv").touch()
        (tmp_path / "referencia_temporal.csv").touch()
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={
                "descricao": [".csv"],
                "composicao": [".csv"],
                "valores": [".csv"],
                "referencia_temporal": [".csv"],
            },
        )

        validator = _build_validator(mocker, data_models_context)

        assert not hasattr(validator, "errors")
        assert not hasattr(validator, "warnings")

    def test_validate_all_general_structure_is_idempotent(self, mocker, tmp_path):
        """Calling `validate_all_general_structure` twice must not duplicate messages."""
        (tmp_path / "unexpected.txt").touch()
        (tmp_path / "descricao.csv").touch()
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={"descricao": [".csv"]},
        )

        validator = _build_validator(mocker, data_models_context)

        first_errors, first_warnings = validator.validate_all_general_structure()
        second_errors, second_warnings = validator.validate_all_general_structure()

        assert first_errors == second_errors
        assert first_warnings == second_warnings == []
        assert first_errors.count("validator_structure_error_unexpected_file") == 1


class TestFileStructureValidatorChecks:
    """Message-key-level regression coverage for each structural check."""

    def test_empty_directory_reports_empty_directory_and_missing_files(self, mocker, tmp_path):
        """An empty directory reports itself empty and every expected file missing."""
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={"descricao": [".csv"], "composicao": [".csv"]},
        )

        validator = _build_validator(mocker, data_models_context)

        assert validator._errors == [
            "validator_structure_error_empty_directory",
            "validator_structure_error_missing_file",
            "validator_structure_error_missing_file",
        ]

    def test_unexpected_file_is_reported_once(self, mocker, tmp_path):
        """A file that matches no expected/optional pattern is reported as unexpected."""
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "unexpected.txt").touch()
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={"descricao": [".csv"]},
        )

        validator = _build_validator(mocker, data_models_context)

        assert validator._errors == ["validator_structure_error_unexpected_file"]

    def test_missing_required_file_is_reported(self, mocker, tmp_path):
        """A required file absent from the directory is reported as missing."""
        (tmp_path / "legenda.csv").touch()
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={"composicao": [".csv"]},
            optional_files={"legenda": [".csv"]},
        )

        validator = _build_validator(mocker, data_models_context)

        assert validator._errors == ["validator_structure_error_missing_file"]

    def test_csv_and_xlsx_conflict_is_reported(self, mocker, tmp_path):
        """Both `.csv` and `.xlsx` present for the same base name is a conflict."""
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "descricao.xlsx").touch()
        data_models_context = _build_data_models_context(
            mocker,
            tmp_path,
            expected_files={"descricao": [".csv", ".xlsx"]},
        )

        validator = _build_validator(mocker, data_models_context)

        assert validator._errors == ["validator_structure_error_conflicting_files"]
