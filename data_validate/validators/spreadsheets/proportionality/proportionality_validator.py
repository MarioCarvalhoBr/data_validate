#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any, Set


import pandas as pd
from pandas import DataFrame

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import SpProportionality, SpDescription, SpValue, SpComposition
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


from data_validate.helpers.common.processing.data_cleaning import (
    clean_dataframe_integers,
)
from data_validate.helpers.common.formatting.number_formatting import check_cell_integer
from data_validate.helpers.common.processing.collections_processing import (
    categorize_strings_by_id_pattern_from_list,
    find_differences_in_two_set_with_message,
)
from data_validate.helpers.common.processing.collections_processing import generate_group_from_list


def get_valids_codes_from_description(
    df_description: pd.DataFrame, column_name_level: str, column_name_code: str, column_name_scenario: str
) -> Set[str]:
    df_description = df_description[df_description[column_name_level] != "1"]

    if column_name_scenario in df_description.columns:
        df_description = df_description[~((df_description[column_name_level] == "2") & (df_description[column_name_scenario] == "0"))]

    codes_cleaned = set(df_description[column_name_code].astype(str))
    valid_codes = set()

    for code in codes_cleaned:
        is_correct, __ = check_cell_integer(code, 1)
        if is_correct:
            valid_codes.add(code)

    set_valid_codes = set(str(code) for code in valid_codes)
    return set_valid_codes


class SpProportionalityValidator(ValidatorModelABC):
    """
    Validates the content of the SpProportionality spreadsheet.
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
            type_class=SpProportionality,
            **kwargs,
        )

        # Configure
        self.model_sp_proportionality = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)
        self.model_sp_composition = self._data_models_context.get_instance_of(SpComposition)

        # Get model properties once
        self.exists_scenario = self.model_sp_value.scenario_exists_file
        self.list_scenarios = self.model_sp_value.scenarios_list

        # Initialize variables

        # Spreadsheet names
        self.sp_name_proportionality = ""
        self.sp_name_description = ""
        self.sp_name_value = ""
        self.sp_name_composition = ""

        # Column names used in validations

        # Columns in SpProportionality and SpValue
        self.column_name_id: str = ""

        # Columns in SpDescription
        self.column_name_code: str = ""
        self.column_name_level: str = ""
        self.column_name_scenario: str = ""

        # Columns in SpComposition
        self.column_name_parent: str = ""
        self.column_name_child: str = ""

        self.global_required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_proportionality = self.model_sp_proportionality.filename
        self.sp_name_description = self.model_sp_description.filename
        self.sp_name_value = self.model_sp_value.filename
        self.sp_name_composition = self.model_sp_composition.filename

        # Set column names
        self.column_name_id = SpProportionality.RequiredColumn.COLUMN_ID.name

        self.column_name_code = SpDescription.RequiredColumn.COLUMN_CODE.name
        self.column_name_level = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        self.column_name_scenario = SpDescription.DynamicColumn.COLUMN_SCENARIO.name

        self.column_name_parent = SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name
        self.column_name_child = SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name

        # Define required columns efficiently
        self.global_required_columns = {
            self.sp_name_proportionality: [SpProportionality.RequiredColumn.COLUMN_ID.name],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_LEVEL.name,
            ],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_composition: [
                SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name,
                SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name,
            ],
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_proportionality: self.model_sp_proportionality.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_composition: self.model_sp_composition.data_loader_model.df_data,
        }

    def validate_relation_indicators_in_proportionality(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []

        if self.model_dataframes[self.sp_name_description].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_relation_indicators_in_proportionality,
                        NamesEnum.IR.value,
                    )
                ]
            )
            return errors, warnings

        # Somente com dados de descricao e composicao (deve ser igual, apenas extrair)
        local_required_columns = {
            self.sp_name_proportionality: self.global_required_columns[self.sp_name_proportionality],
            self.sp_name_description: self.global_required_columns[self.sp_name_description],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Create working copies and clean data
        df_description: DataFrame = self.model_dataframes[self.sp_name_description].copy()
        df_proportionality: DataFrame = self.model_dataframes[self.sp_name_proportionality].copy()

        # Clean integer columns: df_description
        df_description, _ = clean_dataframe_integers(
            df=df_description,
            file_name=self.sp_name_description,
            columns_to_clean=[self.column_name_code],
        )

        # List of codes at level 1 to remove
        codes_level_to_remove = df_description[df_description[self.column_name_level] == "1"][self.column_name_code].astype(str).tolist()
        set_valid_codes_description = get_valids_codes_from_description(
            df_description, self.column_name_level, self.column_name_code, self.column_name_scenario
        )

        # List all codes in proportionality (both levels of MultiIndex)
        level_one_columns = df_proportionality.columns.get_level_values(0).unique().tolist()
        level_two_columns = df_proportionality.columns.get_level_values(1).unique().tolist()

        # Remove ID column from both levels if present
        if self.column_name_id in level_two_columns:
            level_two_columns.remove(self.column_name_id)

        # Remove unnamed columns
        level_one_columns = [col for col in level_one_columns if not col.startswith("Unnamed")]
        level_two_columns = [col for col in level_two_columns if not col.startswith("Unnamed")]

        # Extract codes from both levels from pattern
        set_valid_codes_prop = set()
        level_columns = [level_one_columns, level_two_columns]
        for level_column in level_columns:
            codes_matched_by_pattern, __ = categorize_strings_by_id_pattern_from_list(level_column, self.list_scenarios)
            codes_matched_by_pattern = [str(code) for code in codes_matched_by_pattern]
            codes_cleaned = set([code.split("-")[0] for code in codes_matched_by_pattern]) - set(codes_level_to_remove)

            # Add to all_codes_proportionalities
            set_valid_codes_prop = set_valid_codes_prop.union(codes_cleaned)

        # Convert to integers for comparison
        set_valid_codes_description = set([int(code) for code in set_valid_codes_description])
        set_valid_codes_prop = set([int(code) for code in set(set_valid_codes_prop)])

        # Compare codes between description and proportionality
        comparison_errors = find_differences_in_two_set_with_message(
            first_set=set_valid_codes_description,
            label_1=self.sp_name_description,
            second_set=set_valid_codes_prop,
            label_2=self.sp_name_proportionality,
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_columns_repeated_indicators(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []

        local_required_columns = {
            self.sp_name_proportionality: self.global_required_columns[self.sp_name_proportionality],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        df_proportionalities: DataFrame = self.model_dataframes[self.sp_name_proportionality].copy()

        # Códigos dos indicadores que estão em nível 1
        level_one_columns = [col for col in df_proportionalities.columns.get_level_values(0).tolist() if not col.lower().startswith("unnamed")]
        grouped_columns = generate_group_from_list(level_one_columns)

        unique_list = []
        for group in grouped_columns:
            first_element = group[0]
            if first_element not in unique_list:
                unique_list.append(first_element)
            else:
                errors.append(f"{self.sp_name_proportionality}: O indicador pai '{first_element}' está repetido na planilha.")

        errors = list(set(errors))

        return errors, warnings

    def validate_relation_indicators_in_value_and_proportionality(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        if self.model_dataframes[self.sp_name_value].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_relation_indicators_in_value_and_proportionality,
                        NamesEnum.IND_VAL_PROP.value,
                    )
                ]
            )
            return errors, warnings

        # Somente com dados de descricao e composicao (deve ser igual, apenas extrair)
        local_required_columns = {
            self.sp_name_proportionality: self.global_required_columns[self.sp_name_proportionality],
            self.sp_name_value: self.global_required_columns[self.sp_name_value],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        df_proportionalities = self.model_dataframes[self.sp_name_proportionality].copy()
        df_values = self.model_dataframes[self.sp_name_value].copy()

        # Get all codes in proportionality (both levels of MultiIndex)

        # Get all columns in level 1
        columns_level_one_prop = df_proportionalities.columns.get_level_values(0).unique().tolist()
        columns_level_one_prop = [col for col in columns_level_one_prop if not col.lower().startswith("unnamed: 0_level_0")]

        # Get all columns in level 2
        columns_level_two_prop = df_proportionalities.columns.get_level_values(1).unique().tolist()
        columns_level_two_prop.remove(self.column_name_id)

        # Create a set with all codes in both levels
        set_all_columns_prop = set(columns_level_one_prop + columns_level_two_prop)

        # Get all codes in values
        columns_values = df_values.columns.unique().tolist()
        columns_values.remove(self.column_name_id)
        set_all_columns_values = set(columns_values)

        # Compare codes between description and proportionality
        comparison_errors = find_differences_in_two_set_with_message(
            first_set=set_all_columns_prop,
            label_1=self.sp_name_proportionality,
            second_set=set_all_columns_values,
            label_2=self.sp_name_value,
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_xxx(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - XXX")

        return errors, warnings

    def validate_yyy(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - YYY")

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpProportionality."""

        validations = [
            (self.validate_relation_indicators_in_proportionality, NamesEnum.IR.value),
            (self.validate_columns_repeated_indicators, NamesEnum.REP_IND_PROP.value),
            (self.validate_relation_indicators_in_value_and_proportionality, NamesEnum.IND_VAL_PROP.value),
            (self.validate_xxx, NamesEnum.IR.value),
            (self.validate_yyy, NamesEnum.IR.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
