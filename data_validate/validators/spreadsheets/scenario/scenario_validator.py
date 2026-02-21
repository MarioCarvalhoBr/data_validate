#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Scenario spreadsheet validator module.

This module validates scenario data including punctuation rules for descriptions,
and unique value constraints for scenario identifiers and symbols.
"""

from typing import List, Tuple, Dict, Any

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.common.validation.character_processing import CharacterProcessing

from data_validate.models import SpScenario
from data_validate.validators.spreadsheets.base.validator_model_abc import ValidatorModelABC


class SpScenarioValidator(ValidatorModelABC):
    """
    Validates Scenario spreadsheet content.

    This validator performs comprehensive checks on scenario data including:
    - Punctuation validation for name and description fields
    - Unique value constraints for name and symbol columns

    Notes
    -----
    Inherits validation infrastructure from ValidatorModelABC including column
    existence checks and report generation capabilities.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the Scenario validator.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models and configuration.
        report_list : ModelListReport
            Report aggregator for collecting validation results.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpScenario,
            **kwargs,
        )

        # Run pipeline
        self.run()

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        """
        Validate punctuation rules for scenario fields.

        Ensures that:
        - Name fields do not end with punctuation
        - Description fields end with a period (.)

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: Warning messages for punctuation violations

        Notes
        -----
        - COLUMN_NAME: Must not end with punctuation
        - COLUMN_DESCRIPTION: Must end with a period
        - Missing columns generate warnings rather than errors
        """
        warnings = []

        columns_dont_punctuation = [SpScenario.RequiredColumn.COLUMN_NAME.name]
        columns_must_end_with_dot = [SpScenario.RequiredColumn.COLUMN_DESCRIPTION.name]

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

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        """
        Validate uniqueness of scenario identifiers.

        Ensures that all values in the name and symbol columns are unique across
        the entire scenario dataset to prevent duplicate scenario definitions.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for duplicate values
                - List[str]: Empty list (no warnings generated)

        Notes
        -----
        Validates uniqueness for:
        - COLUMN_NAME: Scenario names must be unique
        - COLUMN_SYMBOL: Scenario symbols must be unique
        """
        errors = []

        columns_to_check = [
            SpScenario.RequiredColumn.COLUMN_NAME.name,
            SpScenario.RequiredColumn.COLUMN_SYMBOL.name,
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
        Execute all scenario validations.

        Orchestrates the execution of all scenario validators including:
        - Punctuation validation for names and descriptions
        - Unique value validation for names and symbols

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        All validations are skipped if the scenario dataframe is empty.
        Results are aggregated into reports via `build_reports()`.
        """

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_SCEN.value),
            (self.validate_unique_values, NamesEnum.UVR_SCEN.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
