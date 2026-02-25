#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Temporal Reference spreadsheet validator module.

This module validates temporal reference data including punctuation rules,
reference year validation, and unique value constraints for temporal metadata.
"""

from typing import List, Tuple, Dict, Any

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.common.validation.character_processing import CharacterProcessing

from data_validate.models import SpTemporalReference
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class SpTemporalReferenceValidator(BaseValidator):
    """
    Validates Temporal Reference spreadsheet content.

    This validator performs comprehensive checks on temporal reference data including:
    - Punctuation validation for description fields
    - Reference year validation (must be future years)
    - Unique value constraints for name and symbol columns

    Notes
    -----
    Inherits validation infrastructure from BaseValidator including column
    existence checks and report generation capabilities.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the Temporal Reference validator.

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
            type_class=SpTemporalReference,
            **kwargs,
        )

        # Run pipeline
        self.run()

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        """
        Validate punctuation rules for temporal reference descriptions.

        Ensures that description fields end with a period (.) as required by
        the data quality standards.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: Warning messages for punctuation violations

        Notes
        -----
        Only the description column is validated for ending punctuation.
        Missing columns generate warnings rather than errors.
        """
        warnings = []

        columns_dont_punctuation = []
        columns_must_end_with_dot = [SpTemporalReference.RequiredColumn.COLUMN_DESCRIPTION.name]

        list_columns = list(columns_dont_punctuation + columns_must_end_with_dot)
        for column in list_columns:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = CharacterProcessing.check_characters_punctuation_rules(
            self._dataframe,
            self._filename,
            columns_dont_punctuation,
            columns_must_end_with_dot,
        )
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_reference_years(self) -> Tuple[List[str], List[str]]:
        """
        Validate that reference years are in the future.

        Checks that all year values in the symbol column (excluding the first row
        which represents the current year) are greater than the configured current
        year. This ensures temporal references only point to future scenarios.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for past years in temporal references
                - List[str]: Empty list (no warnings generated)

        Notes
        -----
        - First row is excluded from validation (represents current year)
        - Years must be greater than config.CURRENT_YEAR
        - Missing symbol column returns errors immediately
        """
        errors = []

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name,
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)
                return errors, []

        # Remove first row: This is actual year
        column_series_symbol = SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.iloc[1:]
        years = column_series_symbol.unique()

        # Check if all years are greater than the current year
        for year in years:
            if int(year) < self._data_models_context.config.CURRENT_YEAR:
                errors.append(f"{self._filename}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.")

        return errors, []

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        """
        Validate uniqueness of name and symbol columns.

        Ensures that all values in the name and symbol columns are unique across
        the entire temporal reference dataset to prevent duplicate temporal references.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for duplicate values
                - List[str]: Empty list (no warnings generated)

        Notes
        -----
        Validates uniqueness for:
        - COLUMN_NAME: Temporal reference names must be unique
        - COLUMN_SYMBOL: Year symbols must be unique
        """
        errors = []

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_NAME.name,
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name,
        ]

        # Check if columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)

        __, unique_errors = DataFrameProcessing.check_dataframe_unique_values(
            dataframe=self._dataframe,
            file_name=self._filename,
            columns_uniques=columns_to_check,
        )
        errors.extend(unique_errors)

        return errors, []

    def _prepare_statement(self) -> None:
        """
        Prepare validation statements.

        This method is currently a placeholder for future initialization logic
        that may be needed before running validations.
        """
        pass

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all temporal reference validations.

        Orchestrates the execution of all temporal reference validators including:
        - Punctuation validation for descriptions
        - Reference year validation (future years only)
        - Unique value validation for names and symbols

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        All validations are skipped if the temporal reference dataframe is empty.
        Results are aggregated into reports via `build_reports()`.
        """

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_TEMP.value),
            (self.validate_reference_years, NamesEnum.YEARS_TEMP.value),
            (self.validate_unique_values, NamesEnum.UVR_TEMP.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
