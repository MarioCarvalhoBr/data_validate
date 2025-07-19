#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any
import pandas as pd

from common.utils.formatting.number_formatting import check_cell
from common.utils.processing.collections_processing import extract_numeric_ids_and_unmatched_strings_from_list, \
    extract_numeric_integer_ids_from_list, find_differences_in_two_set, categorize_strings_by_id_pattern_from_list
from common.utils.validation.value_data_validation import (
    get_filtered_description_dataframe,
    extract_level_one_codes,
    process_invalid_columns,
    validate_scenario_columns_exist,
    prepare_values_dataframe,
    validate_data_values_in_columns
)
from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDescription, SpTemporalReference, SpScenario, SpValue
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC


class SpValueValidator(ValidatorModelABC):
    """
    Validates the content of the SpValue spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_context=data_context, report_list=report_list, type_class=SpValue, **kwargs)

        # Configure
        self.model_sp_value = self._data_model
        self.model_sp_description = self._data_context.get_instance_of(SpDescription)
        self.model_sp_temporal_reference = self._data_context.get_instance_of(SpTemporalReference)
        self.model_sp_scenario = self._data_context.get_instance_of(SpScenario)

        # Run pipeline
        self.run()

    def validate_relation_indicators_in_values(self) -> Tuple[List[str], List[str]]:
        """
        Validate indicator relationships between values and descriptions.

        Returns:
            Tuple of (errors, warnings) lists
        """
        errors, warnings = [], []

        # Get model properties
        exists_scenario = self.model_sp_value.exists_scenario
        list_scenarios = self.model_sp_value.list_scenarios

        # Define required columns for each model
        description_columns = [
            SpDescription.RequiredColumn.COLUMN_CODE.name,
            SpDescription.RequiredColumn.COLUMN_LEVEL.name
        ]

        scenario_columns = [SpScenario.RequiredColumn.COLUMN_SYMBOL.name] if exists_scenario else []

        # Check description columns
        for column in description_columns:
            exists_column, error_msg = self._column_exists_dataframe(
                self.model_sp_description.data_loader_model.df_data, column)
            if not exists_column:
                errors.append(error_msg)

        # Check scenario columns if scenarios exist
        for column in scenario_columns:
            exists_column, error_msg = self._column_exists_dataframe(
                self.model_sp_scenario.data_loader_model.df_data, column)
            if not exists_column:
                errors.append(error_msg)

        if errors:
            return errors, warnings

        # Extract level 1 codes to ignore using generic function
        level_one_codes = extract_level_one_codes(
            self.model_sp_description.df_code_level_cleanned,
            SpDescription.RequiredColumn.COLUMN_CODE.name,
            SpDescription.RequiredColumn.COLUMN_LEVEL.name
        )

        # Process value columns
        value_columns = self._dataframe.columns.tolist()
        columns_to_ignore = [SpValue.RequiredColumn.COLUMN_ID.name] + level_one_codes

        valid_value_codes, invalid_columns = extract_numeric_ids_and_unmatched_strings_from_list(
            value_columns, columns_to_ignore, list_scenarios
        )

        # Process invalid columns using generic function
        processed_invalid_columns = process_invalid_columns(invalid_columns)
        if processed_invalid_columns:
            errors.append(f"{self._filename}: Colunas inválidas: {processed_invalid_columns}.")

        # Get filtered description codes using generic function
        filtered_description_df = get_filtered_description_dataframe(
            self.model_sp_description.df_code_level_cleanned,
            SpDescription.RequiredColumn.COLUMN_LEVEL.name,
            SpDescription.DynamicColumn.COLUMN_SCENARIO.name
        )
        description_code_values = set(
            filtered_description_df[SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str)
        )

        valid_description_codes, _ = extract_numeric_integer_ids_from_list(description_code_values)

        # Compare codes between description and values
        comparison_errors = find_differences_in_two_set(
            first_set=valid_description_codes,
            label_1=self.model_sp_description.filename,
            second_set=valid_value_codes,
            label_2=self._filename
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_value_combination_relation(self) -> Tuple[List[str], List[str]]:
        """Validate value combination relations."""
        errors, warnings = [], []
        return errors, warnings

    def validate_unavailable_codes_values(self) -> Tuple[List[str], List[str]]:
        """
        Validate unavailable and invalid values in the data.

        Checks for:
        1. Invalid numeric values (not numbers and not "DI")
        2. Values with more than 2 decimal places

        Returns:
            Tuple of (errors, warnings) lists
        """
        errors, warnings = [], []

        # Get model properties
        exists_scenario = self.model_sp_value.exists_scenario
        list_scenarios = self.model_sp_value.list_scenarios

        # Validate scenario columns if they exist using generic function
        scenario_errors = validate_scenario_columns_exist(
            self.model_sp_scenario.data_loader_model.df_data,
            [SpScenario.RequiredColumn.COLUMN_SYMBOL.name],
            exists_scenario
        )
        if scenario_errors:
            errors.extend(scenario_errors)
            return errors, warnings

        # Prepare dataframe for validation using generic function
        df_values = prepare_values_dataframe(
            self._dataframe,
            SpValue.RequiredColumn.COLUMN_ID.name
        )

        # Get valid columns that match ID patterns
        valid_columns, _ = categorize_strings_by_id_pattern_from_list(
            df_values.columns, list_scenarios
        )

        # Validate data values in columns using generic function
        validation_errors, validation_warnings = validate_data_values_in_columns(
            df_values, valid_columns, self._filename
        )

        errors.extend(validation_errors)
        warnings.extend(validation_warnings)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpValue."""

        validations = [
            (self.validate_relation_indicators_in_values, NamesEnum.IR.value),
            (self.validate_value_combination_relation, NamesEnum.HTML_DESC.value),
            (self.validate_unavailable_codes_values, NamesEnum.UNAV_INV.value),
        ]

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings

