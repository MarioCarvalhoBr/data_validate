#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
File structure validator module for validating input folder structure and file presence.

This module provides validation functionality to ensure that the input directory contains
all required files, does not contain unexpected files or folders, and handles file conflicts
between different formats (e.g., .xlsx and .csv).
"""

import os
from typing import List, Dict, Any, Tuple

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import SpDescription
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class FileStructureValidator(BaseValidator):
    """
    Validates the structure of files in the input folder.

    This validator ensures that:
    - The input directory is not empty
    - All required files are present
    - No unexpected files or folders exist
    - No conflicting file formats exist (e.g., both .xlsx and .csv with same name)

    Attributes
    ----------
    context : DataModelsContext
        Context containing configuration, file system utilities, and data arguments.
    errors : List[str]
        Accumulated list of validation errors.
    warnings : List[str]
        Accumulated list of validation warnings.
    dir_files : List[str]
        List of file names in the input directory.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the file structure validator.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models and configuration.
        validation_reports : ModelListReport
            Report aggregator for collecting validation results.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            validation_reports=validation_reports,
            type_class=SpDescription,
            **kwargs,
        )

        self.context: DataModelsContext = data_models_context
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.dir_files: List[str] = os.listdir(self.context.data_args.data_file.input_folder)

        self._prepare_statement()
        self.run()

    def _prepare_statement(self) -> None:
        """
        Prepare validation statements.

        This method is currently a placeholder for future initialization logic
        that may be needed before running validations.
        """
        pass

    def check_empty_directory(self) -> Tuple[bool, List[str]]:
        """
        Check if the input directory is empty.

        Validates that the input directory contains at least one file or folder.
        An empty directory is considered a validation error.

        Returns
        -------
        Tuple[bool, List[str]]
            A tuple containing:
                - bool: True if validation passed (directory not empty), False otherwise
                - List[str]: List of error messages (empty if directory not empty)
        """
        local_errors = []
        is_empty, message = self.context.fs_utils.check_directory_is_empty(self.context.data_args.data_file.input_folder)
        if is_empty:
            local_errors.append(
                self.context.language_manager.text(
                    "validator_structure_error_empty_directory",
                    dir_path=self.context.data_args.data_file.input_folder,
                )
            )
        return not local_errors, local_errors

    def check_not_expected_files_in_folder_root(self) -> Tuple[bool, List[str]]:
        """
        Check for unexpected folders or files in the input directory.

        Validates that:
        - Files are not placed inside a single subdirectory
        - Only expected files exist in the root directory
        - No unexpected folders exist
        - All files match either expected or optional file patterns

        Returns
        -------
        Tuple[bool, List[str]]
            A tuple containing:
                - bool: True if validation passed (no unexpected files), False otherwise
                - List[str]: List of error messages for each unexpected file or folder
        """
        local_errors = []
        expected_files: Dict[str, List[str]] = self.context.config.spreadsheet_info.EXPECTED_FILES
        optional_files: Dict[str, List[str]] = self.context.config.spreadsheet_info.OPTIONAL_FILES

        if len(self.dir_files) == 1:
            dir_path = os.path.join(self.context.data_args.data_file.input_folder, self.dir_files[0])
            is_dir, _ = self.context.fs_utils.check_directory_exists(dir_path)
            if is_dir:
                local_errors.append(self.context.language_manager.text("validator_structure_error_files_not_in_folder"))
                return not local_errors, local_errors

        for file_name in self.dir_files:
            file_path = os.path.join(self.context.data_args.data_file.input_folder, file_name)
            is_file, _ = self.context.fs_utils.check_file_exists(file_path)
            if not is_file:
                local_errors.append(self.context.language_manager.text("validator_structure_error_unexpected_folder").format(file_name=file_name))
                continue

            file_base, file_ext = os.path.splitext(file_name)

            if file_base in expected_files and file_ext in expected_files[file_base]:
                continue
            if file_base in optional_files and file_ext in optional_files[file_base]:
                continue

            local_errors.append(self.context.language_manager.text("validator_structure_error_unexpected_file").format(file_name=file_name))

        return not local_errors, local_errors

    def check_expected_files_in_folder_root(self) -> Tuple[bool, List[str]]:
        """
        Check if all expected files are present in the input directory.

        Validates that all required files defined in the configuration are present
        in the root directory, accepting any of the allowed file extensions
        (.xlsx or .csv) for each file.

        Returns
        -------
        Tuple[bool, List[str]]
            A tuple containing:
                - bool: True if validation passed (all expected files present), False otherwise
                - List[str]: List of error messages for each missing file
        """
        local_errors = []
        expected_files: Dict[str, List[str]] = self.context.config.spreadsheet_info.EXPECTED_FILES

        for file_base, extensions in expected_files.items():
            file_found = False
            for ext in extensions:
                file_path = os.path.join(self.context.data_args.data_file.input_folder, f"{file_base}{ext}")
                is_file, _ = self.context.fs_utils.check_file_exists(file_path)
                if is_file:
                    file_found = True
                    break
            if not file_found:
                local_errors.append(self.context.language_manager.text("validator_structure_error_missing_file").format(file_base=file_base))
        return not local_errors, local_errors

    def check_ignored_files_in_folder_root(self) -> Tuple[bool, List[str]]:
        """
        Check for files that will be ignored due to format conflicts.

        Validates that there are no conflicting file formats in the root folder.
        When both .xlsx and .csv files exist with the same base name, this creates
        ambiguity in which file to use and is considered an error.

        Returns
        -------
        Tuple[bool, List[str]]
            A tuple containing:
                - bool: True if validation passed (no conflicting files), False otherwise
                - List[str]: List of error messages for each file with conflicting formats
        """
        local_errors = []
        file_groups = {}

        for file_name in self.dir_files:
            file_base, file_ext = os.path.splitext(file_name)
            if file_ext in [".xlsx", ".csv"]:
                if file_base not in file_groups:
                    file_groups[file_base] = []
                file_groups[file_base].append(file_ext)

        for file_base, extensions in file_groups.items():
            if ".xlsx" in extensions and ".csv" in extensions:
                local_errors.append(self.context.language_manager.text("validator_structure_error_conflicting_files").format(file_base=file_base))

        return not local_errors, local_errors

    def validate_all_general_structure(self) -> Tuple[List[str], List[str]]:
        """
        Perform all validation checks on the input folder structure.

        Executes a comprehensive set of structural validations including:
        - Empty directory check
        - Unexpected files and folders check
        - Expected files presence check
        - Conflicting file formats check

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Accumulated list of all validation errors
                - List[str]: Empty list (no warnings generated by this method)

        Notes
        -----
        All errors from individual checks are aggregated into a single error list.
        """
        all_errors = [
            [self.check_empty_directory()],
            [self.check_not_expected_files_in_folder_root()],
            [self.check_expected_files_in_folder_root()],
            [self.check_ignored_files_in_folder_root()],
        ]
        for check in all_errors:
            is_valid, errors = check[0]
            if not is_valid:
                self.errors.extend(errors)

        return self.errors, []

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all file structure validations.

        Orchestrates the validation process by executing all structural checks
        and building reports based on the validation results.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        Validation results are aggregated into reports via the `build_reports()` method
        and tagged with the file structure validation identifier (NamesEnum.FS).
        """
        validations = [
            (self.validate_all_general_structure, NamesEnum.FS.value),
        ]

        self.build_reports(validations)

        return self._errors, self._warnings
