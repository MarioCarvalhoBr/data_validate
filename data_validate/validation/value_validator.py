#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

from common.utils.generation.combinations import generate_combinations, processar_combinacoes_extras
from common.utils.processing.collections_processing import extract_numeric_ids_and_unmatched_strings_from_list, \
    extract_numeric_integer_ids_from_list, find_differences_in_two_set, categorize_strings_by_id_pattern_from_list
from common.utils.processing.data_cleaning import clean_dataframe
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

        # Get model properties once
        self.exists_scenario = self.model_sp_value.exists_scenario
        self.list_scenarios = self.model_sp_value.list_scenarios

        self.sp_name_description = ""
        self.sp_name_temporal_reference = ""
        self.sp_name_scenario = ""
        self.sp_name_value = ""
        self.required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_description = self.model_sp_description.CONSTANTS.SP_NAME
        self.sp_name_temporal_reference = self.model_sp_temporal_reference.CONSTANTS.SP_NAME
        self.sp_name_scenario = self.model_sp_scenario.CONSTANTS.SP_NAME
        self.sp_name_value = self.model_sp_value.CONSTANTS.SP_NAME

        # Define required columns efficiently
        self.required_columns = {
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_description: [SpDescription.RequiredColumn.COLUMN_CODE.name,SpDescription.RequiredColumn.COLUMN_LEVEL.name],
            self.sp_name_temporal_reference: [SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name],
            self.sp_name_scenario: [SpScenario.RequiredColumn.COLUMN_SYMBOL.name] if self.exists_scenario else []
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_temporal_reference: self.model_sp_temporal_reference.data_loader_model.df_data,
            self.sp_name_scenario: self.model_sp_scenario.data_loader_model.df_data if self.exists_scenario else None
        }

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
        value_columns = self.model_sp_value.data_loader_model.df_data.columns.tolist()
        columns_to_ignore = [SpValue.RequiredColumn.COLUMN_ID.name] + level_one_codes

        valid_value_codes, invalid_columns = extract_numeric_ids_and_unmatched_strings_from_list(
            value_columns, columns_to_ignore, list_scenarios
        )

        # Process invalid columns using generic function
        processed_invalid_columns = process_invalid_columns(invalid_columns)
        if processed_invalid_columns:
            errors.append(f"{self.model_sp_value.filename}: Colunas inválidas: {processed_invalid_columns}.")

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
            label_2=self.model_sp_value.filename
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_value_combination_relation(self) -> Tuple[List[str], List[str]]:
        """
        Validate value combination relations between indicators and their expected columns.

        This function ensures that each indicator has the correct combination of columns
        in the values dataframe based on its level and scenario configuration.
        """
        errors, warnings = [], []

        if self.exists_scenario:
            self.required_columns[self.sp_name_description].append(SpDescription.DynamicColumn.COLUMN_SCENARIO.name)

        for model_name, columns in self.required_columns.items():
            dataframe = self.model_dataframes[model_name]
            if dataframe is not None:
                for column in columns:
                    exists_column, error_msg = self._column_exists_dataframe(dataframe, column)
                    if not exists_column:
                        errors.append(error_msg)

        if errors:
            return errors, warnings

        # Prepare cleaned dataframes
        # No-need to clean the values dataframe
        df_values = self.model_dataframes[self.sp_name_value].copy()

        # Need to clean the description and temporal reference dataframes
        df_description, _ = clean_dataframe(
            self.model_dataframes[self.sp_name_description],
            self.sp_name_description,
            self.required_columns[self.sp_name_description]
        )
        df_temporal_reference, _ = clean_dataframe(
            self.model_dataframes[self.sp_name_temporal_reference],
            self.sp_name_temporal_reference,
            self.required_columns[self.sp_name_temporal_reference]
        )

        # Get temporal symbols once (sorted for consistency)
        temporal_symbols = sorted(df_temporal_reference[SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name].unique())
        first_year = temporal_symbols[0]
        value_columns = set(df_values.columns)

        # Process each indicator efficiently
        for _, row in df_description.iterrows():
            code = str(row[SpDescription.RequiredColumn.COLUMN_CODE.name])
            level = int(row[SpDescription.RequiredColumn.COLUMN_LEVEL.name])
            scenario = int(row[SpDescription.DynamicColumn.COLUMN_SCENARIO.name]) if self.exists_scenario else 0

            # Generate expected combinations based on level and scenario
            expected_combinations = []
            if level >= 2:
                if scenario == 0:
                    expected_combinations = [f"{code}-{first_year}"]
                elif scenario == 1:
                    expected_combinations = generate_combinations(code, first_year, temporal_symbols, self.list_scenarios)

            # Validate required combinations exist
            for combination in expected_combinations:
                if combination not in value_columns:
                    # Skip validation for level 2 with scenario 0 (special case)
                    if level == 2 and scenario == 0:
                        continue
                    errors.append(f"{self.model_sp_value.filename}: A coluna '{combination}' é obrigatória.")

            # Find actual combinations for this code
            actual_combinations = [col for col in value_columns if col.startswith(f"{code}-")]

            # Check for extra combinations
            has_extra_error, extra_columns = processar_combinacoes_extras(expected_combinations, actual_combinations)
            if has_extra_error:
                for extra_column in extra_columns:
                    if level == 1:
                        errors.append(f"{self.model_sp_value.filename}: A coluna '{extra_column}' é desnecessária para o indicador de nível 1.")
                    else:
                        errors.append(f"{self.model_sp_value.filename}: A coluna '{extra_column}' é desnecessária.")

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
            self.model_sp_value.data_loader_model.df_data,
            SpValue.RequiredColumn.COLUMN_ID.name
        )

        # Get valid columns that match ID patterns
        valid_columns, _ = categorize_strings_by_id_pattern_from_list(
            df_values.columns, list_scenarios
        )

        # Validate data values in columns using generic function
        validation_errors, validation_warnings = validate_data_values_in_columns(
            df_values, valid_columns, self.model_sp_value.filename
        )

        errors.extend(validation_errors)
        warnings.extend(validation_warnings)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpValue."""

        validations = [
            (self.validate_relation_indicators_in_values, NamesEnum.IR.value),
            (self.validate_value_combination_relation, NamesEnum.VAL_COMB.value),
            (self.validate_unavailable_codes_values, NamesEnum.UNAV_INV.value),
        ]

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings

