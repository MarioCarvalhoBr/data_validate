#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import os
from typing import List, Dict, Any, Tuple

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import SpDescription
from data_validate.validators.spreadsheets.base.validator_model_abc import ValidatorModelABC


class ValidatorStructureFiles(ValidatorModelABC):
    """
    A class to validate the structure of files in a given input folder.

    Attributes:
        context (GeneralContext): The context containing configuration and file system utilities.
        errors (List[str]): List of validation errors.
        warnings (List[str]): List of validation warnings.
        dir_files (List[str]): List of files in the input directory.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpDescription,
            **kwargs,
        )

        """
        Initialize the ValidatorStructureFiles class.

        Args:
            context: GeneralContext: The context containing configuration and file system utilities.
        """
        self.context = data_models_context

        self.errors = []
        self.warnings = []
        self.dir_files = os.listdir(self.context.data_args.data_file.input_folder)

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        pass

    def check_empty_directory(self) -> tuple[bool, List[str]]:
        """
        Check if the input directory is empty.

        Returns:
            bool: True if the directory is empty, False otherwise.
        """
        local_errors = []
        is_empty, message = self.context.fs_utils.check_directory_is_empty(self.context.data_args.data_file.input_folder)
        if is_empty:
            local_errors.append(
                self.context.lm.text(
                    "validator_structure_error_empty_directory",
                    dir_path=self.context.data_args.data_file.input_folder,
                )
            )
        return not local_errors, local_errors

    def check_not_expected_files_in_folder_root(self) -> tuple[bool, List[str]]:
        """
        Check for unexpected folders or files in the input directory.
        """
        local_errors = []
        expected_files: Dict[str, List[str]] = self.context.config.spreadsheet_info.EXPECTED_FILES
        optional_files: Dict[str, List[str]] = self.context.config.spreadsheet_info.OPTIONAL_FILES

        if len(self.dir_files) == 1:
            dir_path = os.path.join(self.context.data_args.data_file.input_folder, self.dir_files[0])
            is_dir, _ = self.context.fs_utils.check_directory_exists(dir_path)
            if is_dir:
                local_errors.append(self.context.lm.text("validator_structure_error_files_not_in_folder"))
                return not local_errors, local_errors

        for file_name in self.dir_files:
            file_path = os.path.join(self.context.data_args.data_file.input_folder, file_name)
            is_file, _ = self.context.fs_utils.check_file_exists(file_path)
            if not is_file:
                local_errors.append(self.context.lm.text("validator_structure_error_unexpected_folder").format(file_name=file_name))
                continue

            file_base, file_ext = os.path.splitext(file_name)

            if file_base in expected_files and file_ext in expected_files[file_base]:
                continue
            if file_base in optional_files and file_ext in optional_files[file_base]:
                continue

            local_errors.append(self.context.lm.text("validator_structure_error_unexpected_file").format(file_name=file_name))

        return not local_errors, local_errors

    def check_expected_files_in_folder_root(self) -> tuple[bool, List[str]]:
        """
        Check if all expected files are present in the input directory.
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
                local_errors.append(self.context.lm.text("validator_structure_error_missing_file").format(file_base=file_base))
        return not local_errors, local_errors

    def check_ignored_files_in_folder_root(self) -> tuple[bool, List[str]]:
        """
        Check for files that will be ignored in the root folder.
        Emit an error if both .xlsx and .csv files with the same name exist.
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
                local_errors.append(self.context.lm.text("validator_structure_error_conflicting_files").format(file_base=file_base))

        return not local_errors, local_errors

    def validate_all_general_structure(self) -> Tuple[List[str], List[str]]:
        """
        Perform all validation checks on the input folder.

        Returns:
            List[str]: A list of validation errors.
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
        """Runs all content validations for SpValue."""

        validations = [
            (self.validate_all_general_structure, NamesEnum.FS.value),
        ]

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
