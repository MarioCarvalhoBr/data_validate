#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Abstract base class for spreadsheet model validators.

This module provides the foundational validator class that all specific spreadsheet
validators inherit from. It establishes the contract for validation logic, error reporting,
and integration with the validation pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Tuple, Callable

import pandas as pd
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing

from data_validate.models.sp_model_abc import SpModelABC


class BaseValidator(ABC):
    """
    Abstract base class for all spreadsheet model validators.

    This class provides the foundation for all specific validators (e.g., Description,
    Value, Legend validators). It handles common validation tasks such as column existence
    checks, text length validation, and report generation.

    Attributes
    ----------
    _data_models_context : DataModelsContext
        Context containing all loaded spreadsheet models and configuration.
    _report_list : ValidationReport
        Aggregator for collecting and organizing validation results.
    _type_class : Type[SpModelABC]
        The model class type this validator is responsible for validating.
    _data_model : SpModelABC
        The specific model instance being validated.
    _filename : str
        Name of the file being validated.
    _dataframe : pd.DataFrame
        DataFrame containing the data to validate.
    TITLES_INFO : Dict[str, str]
        Mapping of validation types to human-readable titles.
    _errors : List[str]
        Accumulated list of validation errors.
    _warnings : List[str]
        Accumulated list of validation warnings.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ValidationReport,
        type_class: Type[SpModelABC],
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the validator with context, report aggregator, and model class.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models, configuration, and utilities.
        validation_reports : ValidationReport
            Report aggregator for collecting validation results.
        type_class : Type[SpModelABC]
            The specific model class type this validator will validate.
        **kwargs : Dict[str, Any]
            Additional keyword arguments for future extensibility.
        """
        # SETUP
        self._data_models_context = data_models_context
        self._report_list = validation_reports
        self._type_class = type_class

        # UNPACK DATA
        self._data_model = self._data_models_context.get_instance_of(self._type_class)
        self._filename = self._data_model.filename if self._data_model else "Unknown"
        self._dataframe = self._data_model.data_loader_model.raw_data.copy() if self._data_model else pd.DataFrame({})
        self.TITLES_INFO = self._data_models_context.config.get_verify_names()

        # LIST OF ERRORS AND WARNINGS
        self._errors: List[str] = []
        self._warnings: List[str] = []

        self.initialize()

    def initialize(self) -> None:
        """
        Initialize additional validator-specific setup.

        This method is called after __init__ and can be overridden by subclasses
        to perform custom initialization logic. The default implementation does nothing.
        """
        pass

    def check_columns_in_models_dataframes(
        self,
        required_columns: Dict[str, List[str]],
        model_dataframes: Dict[str, pd.DataFrame],
    ) -> List[str]:
        """
        Check if required columns exist in the provided dataframes for different models.

        Validates that all specified columns exist in their corresponding model dataframes.
        This is useful for cross-model validations where multiple spreadsheet models need
        to be checked for column presence.

        Args
        ----
        required_columns : Dict[str, List[str]]
            Dictionary where keys are model names and values are lists of required column names.
        model_dataframes : Dict[str, pd.DataFrame]
            Dictionary where keys are model names and values are their corresponding DataFrames.

        Returns
        -------
        List[str]
            List of error messages for missing columns. Empty list if all columns exist.
        """
        errors = []

        # Check if columns exist
        for model_name, columns in required_columns.items():
            dataframe: pd.DataFrame = model_dataframes[model_name]
            if dataframe is not None:
                for column in columns:
                    exists_column, error_msg = self.column_exists(dataframe, model_name, column)
                    if not exists_column:
                        errors.append(error_msg)

        return errors

    def column_exists(self, dataframe: pd.DataFrame, filename: str, column: str) -> Tuple[bool, str]:
        """
        Check if a column exists in a given DataFrame.

        This is a convenience wrapper around DataFrameProcessing.column_exists that can be
        used to validate column presence in any DataFrame-filename pair.

        Args
        ----
        dataframe : pd.DataFrame
            The DataFrame to check for column existence.
        filename : str
            Name of the file for error message generation.
        column : str
            Name of the column to check for.

        Returns
        -------
        Tuple[bool, str]
            A tuple containing:
                - bool: True if column exists, False otherwise
                - str: Error message if column doesn't exist, empty string otherwise
        """
        exists, msg_error_column = DataFrameProcessing.column_exists(dataframe, filename, column)
        return exists, msg_error_column

    def _column_exists(self, column: str) -> Tuple[bool, str]:
        """
        Check if a column exists in the validator's internal DataFrame.

        This method validates column presence in the DataFrame currently being validated
        by this validator instance (self._dataframe).

        Args
        ----
        column : str
            Name of the column to check for.

        Returns
        -------
        Tuple[bool, str]
            A tuple containing:
                - bool: True if column exists, False otherwise
                - str: Error message if column doesn't exist, empty string otherwise
        """
        exists, msg_error_column = DataFrameProcessing.column_exists(self._dataframe, self._filename, column)
        return exists, msg_error_column

    def _column_exists_dataframe(self, dataframe: pd.DataFrame, column: str) -> Tuple[bool, str]:
        """
        Check if a column exists in a specified DataFrame.

        This method validates column presence in a given DataFrame using the
        validator's filename for error message generation.

        Args
        ----
        dataframe : pd.DataFrame
            The DataFrame to check for column existence.
        column : str
            Name of the column to check for.

        Returns
        -------
        Tuple[bool, str]
            A tuple containing:
                - bool: True if column exists, False otherwise
                - str: Error message if column doesn't exist, empty string otherwise
        """
        exists, msg_error_column = DataFrameProcessing.column_exists(dataframe, self._filename, column)
        return exists, msg_error_column

    def _check_text_length(self, column: str, max_len: int) -> Tuple[List[str], List[str]]:
        """
        Validate text length in a column of the validator's DataFrame.

        Checks that all text values in the specified column do not exceed the maximum
        allowed length. Violations are reported as warnings.

        Args
        ----
        column : str
            Name of the column to validate for text length.
        max_len : int
            Maximum allowed length for text values in the column.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for text exceeding max_len
        """
        warnings = []
        __, warnings_text_length = DataFrameProcessing.check_dataframe_text_length(
            dataframe=self._dataframe,
            file_name=self._filename,
            column=column,
            max_length=max_len,
        )
        warnings.extend(warnings_text_length)
        return [], warnings

    def set_not_executed(self, validations: List[Tuple[Callable, str]]) -> None:
        """
        Mark validations as not executed in the report list.

        This is a placeholder method for a future feature that will allow marking
        certain validations as intentionally skipped or not executed.

        Args
        ----
        validations : List[Tuple[Callable, str]]
            List of validation tuples containing (validation_function, report_key).

        Notes
        -----
        This method is currently not implemented and serves as a placeholder for
        future functionality.
        """
        pass
        """
        # FUTURE FEATURE: Implement a method to mark validations as not executed in the report list.
        for _, report_key in validations:
            self._report_list.set_not_executed(self.validation_titles[report_key])
        """

    def build_reports(self, validations: List[Tuple[Callable, str]]) -> None:
        """
        Execute validations and build reports from results.

        Orchestrates the execution of multiple validation functions, collecting their
        errors and warnings, and aggregating them into structured reports. If any
        validation raises an exception, it is caught and reported as an error.

        Args
        ----
        validations : List[Tuple[Callable, str]]
            List of tuples containing (validation_function, report_key). Each validation
            function should return Tuple[List[str], List[str]] representing (errors, warnings).

        Notes
        -----
        - Each validation function is executed sequentially
        - Exceptions during validation are caught and reported as errors
        - Results are extended to both the report list and internal error/warning lists
        - Report keys are used to categorize validation results by type
        """
        for func, report_key in validations:
            try:
                errors, warnings = func()
                if errors or warnings:
                    self._report_list.extend(self.TITLES_INFO[report_key], errors=errors, warnings=warnings)
                self._errors.extend(errors)
                self._warnings.extend(warnings)
            except Exception as e:
                self._report_list.extend(
                    self.TITLES_INFO[report_key],
                    errors=[f"Exception validation in file during {func.__name__}: {str(e)}"],
                    warnings=[],
                )

    @abstractmethod
    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all validations for the specific model type.

        This abstract method must be implemented by all concrete validator subclasses
        to define their specific validation pipeline. It should orchestrate the execution
        of all validation checks appropriate for the model being validated.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        Implementations should call `build_reports()` with their validation functions
        and return the accumulated errors and warnings.
        """
        pass

    @abstractmethod
    def _prepare_statement(self) -> None:
        """
        Prepare initial validation statements and setup.

        This abstract method must be implemented by concrete validator subclasses to
        perform any necessary initialization or preparation before running validations.
        This may include loading additional data, preparing validation contexts, or
        setting up internal state.

        Notes
        -----
        This method is typically called during validator initialization or before
        the validation pipeline begins execution.
        """
        pass
