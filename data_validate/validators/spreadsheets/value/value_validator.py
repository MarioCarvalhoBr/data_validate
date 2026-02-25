#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Value spreadsheet validator module.

This module validates value data including indicator relationships, column combinations,
data format validation, and ensures proper value constraints across temporal references
and scenarios.
"""

from typing import List, Tuple, Dict, Any

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.common.generation.combinations_processing import CombinationsProcessing
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.value_processing import ValueProcessing
from data_validate.models import SpDescription, SpTemporalReference, SpScenario, SpValue
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class SpValueValidator(BaseValidator):
    """
    Validates Value spreadsheet content and relationships.

    This validator performs comprehensive checks on value data including:
    - Indicator relationship validation with description
    - Column combination validation based on level and scenario
    - Data format validation (numeric values, decimal places)
    - Invalid and unavailable value detection
    - Temporal reference and scenario consistency

    Attributes
    ----------
    model_sp_value : SpValue
        Value model instance containing indicator data.
    model_sp_description : SpDescription
        Description model instance containing indicator metadata.
    model_sp_temporal_reference : SpTemporalReference
        Temporal reference model instance for time periods.
    model_sp_scenario : SpScenario
        Scenario model instance for scenario definitions.
    exists_scenario : bool
        Flag indicating if scenario file exists.
    list_scenarios : List[str]
        List of available scenario identifiers.
    sp_name_description : str
        Description spreadsheet filename.
    sp_name_temporal_reference : str
        Temporal reference spreadsheet filename.
    sp_name_scenario : str
        Scenario spreadsheet filename.
    sp_name_value : str
        Value spreadsheet filename.
    global_required_columns : Dict[str, List[str]]
        Required columns mapping for validation.
    model_dataframes : Dict[str, pd.DataFrame]
        DataFrames mapping for each model.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ValidationReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the Value validator.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models and configuration.
        validation_reports : ValidationReport
            Report aggregator for collecting validation results.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            validation_reports=validation_reports,
            type_class=SpValue,
            **kwargs,
        )

        # Configure
        self.model_sp_value = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_temporal_reference = self._data_models_context.get_instance_of(SpTemporalReference)
        self.model_sp_scenario = self._data_models_context.get_instance_of(SpScenario)

        # Get model properties once
        self.exists_scenario = self.model_sp_value.scenario_exists_file
        self.list_scenarios = self.model_sp_value.scenarios

        self.sp_name_description = ""
        self.sp_name_temporal_reference = ""
        self.sp_name_scenario = ""
        self.sp_name_value = ""
        self.global_required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self) -> None:
        """
        Prepare validation context, column mappings, and dataframe references.

        Sets up:
        - Spreadsheet names for all models
        - Column name mappings for validation
        - Required columns dictionary (conditional on scenario existence)
        - DataFrame references for all models

        Notes
        -----
        Scenario-related configurations are conditional based on scenario file existence.
        """
        # Get model properties once
        self.sp_name_description = self.model_sp_description.filename
        self.sp_name_temporal_reference = self.model_sp_temporal_reference.filename
        self.sp_name_scenario = self.model_sp_scenario.filename
        self.sp_name_value = self.model_sp_value.filename

        # Define required columns efficiently
        self.global_required_columns = {
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_LEVEL.name,
            ],
            self.sp_name_temporal_reference: [SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name],
            self.sp_name_scenario: ([SpScenario.RequiredColumn.COLUMN_SYMBOL.name] if self.exists_scenario else []),
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_value: self.model_sp_value.data_loader_model.raw_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.raw_data,
            self.sp_name_temporal_reference: self.model_sp_temporal_reference.data_loader_model.raw_data,
            self.sp_name_scenario: (self.model_sp_scenario.data_loader_model.raw_data if self.exists_scenario else pd.DataFrame()),
        }

    def validate_relation_indicators_in_values(self) -> Tuple[List[str], List[str]]:
        """
        Validate indicator relationships between values and descriptions.

        Ensures that:
        - All value columns match valid indicator codes from description
        - Level 1 indicators are excluded from validation
        - Level 2 indicators with scenario 0 are handled appropriately
        - All description indicators (except excluded levels) exist in values
        - Column names follow valid patterns (code-year or code-year-scenario)

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for missing indicators and invalid columns
                - List[str]: Empty list (no warnings generated)

        Notes
        -----
        - Validation is skipped if description dataframe is empty
        - Level 1 indicators are automatically excluded
        - Columns containing ':' are ignored in invalid column detection
        - Level 2 with scenario 0 are conditionally excluded
        """
        errors, warnings = [], []

        if self.model_dataframes[self.sp_name_description].empty:
            return errors, warnings

        errors = self.check_columns_in_models_dataframes(
            required_columns={
                self.sp_name_description: self.global_required_columns[self.sp_name_description],
                self.sp_name_scenario: self.global_required_columns[self.sp_name_scenario],
            },
            model_dataframes=self.model_dataframes,
        )
        if errors:
            return errors, warnings

        code_column_name = SpDescription.RequiredColumn.COLUMN_CODE.name
        level_column_name = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        scenario_column_name = SpDescription.DynamicColumn.COLUMN_SCENARIO.name

        # Prepare cleaned dataframes
        # No-need to clean the values dataframe
        df_values = self.model_dataframes[self.sp_name_value].copy()
        # Need to clean the description and temporal reference dataframes
        df_description, _ = DataCleaningProcessing.clean_dataframe_integers(
            self.model_dataframes[self.sp_name_description],
            self.sp_name_description,
            [code_column_name],
        )

        level_one_codes = df_description[df_description[level_column_name] == "1"][code_column_name].astype(str).tolist()

        # Process value columns
        value_columns = df_values.columns.tolist()
        columns_to_ignore = self.global_required_columns[self.sp_name_value] + level_one_codes

        valid_value_codes, invalid_columns = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
            value_columns, columns_to_ignore, self.list_scenarios
        )

        # Filter out columns containing ':'
        processed_invalid_columns = sorted({col for col in invalid_columns if ":" not in col})

        if processed_invalid_columns:
            errors.append(f"{self.model_sp_value.filename}: Colunas inválidas: {processed_invalid_columns}.")

        # Get filtered description codes using generic function
        # Remove level 1 indicators
        filtered_description_df = df_description[df_description[level_column_name] != "1"].copy()

        # Remove level 2 indicators with scenario 0 if scenario column exists
        if self.exists_scenario and scenario_column_name in filtered_description_df.columns:
            filtered_description_df = filtered_description_df[
                ~((filtered_description_df[level_column_name] == "2") & (filtered_description_df[scenario_column_name] == "0"))
            ]

        # Extract valid description codes
        valid_description_codes, _ = CollectionsProcessing.extract_numeric_integer_ids_from_list(
            id_values_list=set(filtered_description_df[code_column_name].astype(str))
        )

        # Compare codes between description and values
        comparison_errors = CollectionsProcessing.find_differences_in_two_set_with_message(
            first_set=valid_description_codes,
            label_1=self.model_sp_description.filename,
            second_set=valid_value_codes,
            label_2=self.model_sp_value.filename,
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_value_combination_relation(self) -> Tuple[List[str], List[str]]:
        """
        Validate value combination relations between indicators and their expected columns.

        Ensures that each indicator has the correct combination of columns in the values
        dataframe based on its level and scenario configuration. Validates:
        - Level >= 2 indicators have appropriate temporal-scenario combinations
        - Level 2 with scenario 0 have only base year column
        - Level 2 with scenario 1 have full temporal-scenario matrix
        - No extra unnecessary columns exist for any indicator
        - No missing required combinations

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for missing/extra columns
                - List[str]: Empty list (no warnings generated)

        Notes
        -----
        - Validation is skipped if description or temporal reference is empty
        - Level 1 indicators should not have any temporal columns
        - Level >= 2 indicators require specific combinations based on scenario
        - Extra columns are flagged with specific messages per level
        """
        errors, warnings = [], []

        if self.model_dataframes[self.sp_name_description].empty or self.model_dataframes[self.sp_name_temporal_reference].empty:
            return errors, warnings

        code_column_name = SpDescription.RequiredColumn.COLUMN_CODE.name
        level_column_name = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        scenario_column_name = SpDescription.DynamicColumn.COLUMN_SCENARIO.name
        symbol_column_name = SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name

        local_required_columns = self.global_required_columns.copy()
        if self.exists_scenario:
            local_required_columns[self.sp_name_description].append(scenario_column_name)

        errors = self.check_columns_in_models_dataframes(
            required_columns=local_required_columns,
            model_dataframes=self.model_dataframes,
        )
        if errors:
            return errors, warnings

        # Prepare cleaned dataframes
        # No-need to clean the values dataframe
        df_values = self.model_dataframes[self.sp_name_value].copy()

        # Need to clean the description and temporal reference dataframes
        df_description, _ = DataCleaningProcessing.clean_dataframe_integers(
            self.model_dataframes[self.sp_name_description],
            self.sp_name_description,
            local_required_columns[self.sp_name_description],
        )
        df_temporal_reference, _ = DataCleaningProcessing.clean_dataframe_integers(
            self.model_dataframes[self.sp_name_temporal_reference],
            self.sp_name_temporal_reference,
            local_required_columns[self.sp_name_temporal_reference],
        )

        # Get temporal symbols once (sorted for consistency)
        temporal_symbols = sorted(df_temporal_reference[symbol_column_name].unique())
        first_year = temporal_symbols[0]
        sp_value_columns = set(df_values.columns)

        # Process each indicator efficiently
        for _, row in df_description.iterrows():
            code = str(row[code_column_name])
            level = int(row[level_column_name])
            scenario = int(row[scenario_column_name]) if self.exists_scenario else 0

            # Generate expected combinations based on level and scenario
            expected_combinations = []
            if level >= 2:
                if scenario == 0:
                    expected_combinations = [f"{code}-{first_year}"]
                elif scenario == 1:
                    expected_combinations = CombinationsProcessing.generate_combinations(code, first_year, temporal_symbols, self.list_scenarios)

            # Validate required combinations exist
            for combination in expected_combinations:
                if combination not in sp_value_columns:
                    # Skip validation for level 2 with scenario 0 (special case)
                    if level == 2 and scenario == 0:
                        continue
                    errors.append(f"{self.model_sp_value.filename}: A coluna '{combination}' é obrigatória.")

            # Find actual combinations for this code
            actual_combinations = [col for col in sp_value_columns if col.startswith(f"{code}-")]

            # Check for extra combinations
            has_extra_error, extra_columns = CombinationsProcessing.find_extra_combinations(expected_combinations, actual_combinations)
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

        Performs comprehensive data quality checks including:
        - Invalid numeric values (not numbers and not "DI" marker)
        - Values with more than 2 decimal places
        - Proper format validation for all value columns

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for invalid numeric values
                - List[str]: Warning messages for excessive decimal places

        Notes
        -----
        - ID column is excluded from validation
        - Only columns matching valid ID patterns are validated
        - "Dado indisponível" (DI) markers are allowed
        - Maximum 2 decimal places enforced for numeric values
        """
        errors, warnings = [], []

        errors = self.check_columns_in_models_dataframes(
            required_columns={self.sp_name_scenario: (self.global_required_columns[self.sp_name_scenario] if self.exists_scenario else [])},
            model_dataframes=self.model_dataframes,
        )

        if errors:
            return errors, warnings

        id_column_name = SpValue.RequiredColumn.COLUMN_ID.name

        # Prepare dataframe for validation using generic function
        df_values = self.model_dataframes[self.sp_name_value].copy()
        if id_column_name in df_values.columns:
            df_values = df_values.drop(columns=[id_column_name])

        # Get valid columns that match ID patterns
        valid_columns, _ = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(df_values.columns, self.list_scenarios)

        # Validate data values in columns using generic function
        validation_errors, validation_warnings = ValueProcessing.validate_data_values_in_columns(
            df_values, valid_columns, self.model_sp_value.filename
        )

        errors.extend(validation_errors)
        warnings.extend(validation_warnings)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all value validations.

        Orchestrates the execution of all value validators including:
        - Indicator relationship validation with description
        - Column combination validation based on level and scenario
        - Data format and quality validation (invalid/unavailable values)

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        All validations are skipped if the value dataframe is empty.
        Results are aggregated into reports via `build_reports()`.
        """

        validations = [
            (self.validate_relation_indicators_in_values, NamesEnum.IR.value),
            (self.validate_value_combination_relation, NamesEnum.VAL_COMB.value),
            (self.validate_unavailable_codes_values, NamesEnum.UNAV_INV.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
