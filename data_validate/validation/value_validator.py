#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any
import pandas as pd
from decimal import Decimal

import re
from common.utils.formatting.number_formatting import check_cell
from common.utils.processing.collections_processing import extract_numeric_ids_and_unmatched_strings_from_list, \
    extract_numeric_integer_ids_from_list, find_differences_in_two_set, categorize_strings_by_id_pattern_from_list
from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDescription, SpTemporalReference, SpScenario, SpValue
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC


class SpValueValidator(ValidatorModelABC):
    """
    Validates the content of the SpScenario spreadsheet.
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

        def _get_filtered_description_dataframe() -> pd.DataFrame:
            """Get cleaned description dataframe with level filters applied."""
            df_code_level = self.model_sp_description.df_code_level_cleanned.copy()

            # Remove level 1 indicators
            df_filtered = df_code_level[df_code_level[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '1']

            # Remove level 2 indicators with scenario 0 if scenario column exists
            scenario_column = SpDescription.DynamicColumn.COLUMN_SCENARIO.name
            if scenario_column in df_filtered.columns:
                df_filtered = df_filtered[~((df_filtered[SpDescription.RequiredColumn.COLUMN_LEVEL.name] == '2') & (
                            df_filtered[scenario_column] == '0'))]

            return df_filtered

        def _extract_level_one_codes() -> List[str]:
            """Extract level 1 codes to be ignored during validation."""
            df_code_level = self.model_sp_description.df_code_level_cleanned.copy()
            column_code = SpDescription.RequiredColumn.COLUMN_CODE.name
            column_level = SpDescription.RequiredColumn.COLUMN_LEVEL.name

            return df_code_level[df_code_level[column_level] == '1'][column_code].astype(str).tolist()

        def _process_invalid_columns(invalid_columns: List[str]) -> List[str]:
            """Process and clean invalid column names, returning sorted list."""
            # Filter out columns containing ':'
            filtered_columns = {col for col in invalid_columns if ':' not in col}
            return sorted(filtered_columns)

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
            exists_column, error_msg = self._column_exists_dataframe(self.model_sp_scenario.data_loader_model.df_data,
                                                                     column)
            if not exists_column:
                errors.append(error_msg)

        if errors:
            return errors, warnings

        # Extract level 1 codes to ignore
        level_one_codes = _extract_level_one_codes()

        # Process value columns
        value_columns = self._dataframe.columns.tolist()
        columns_to_ignore = [SpValue.RequiredColumn.COLUMN_ID.name] + level_one_codes

        valid_value_codes, invalid_columns = extract_numeric_ids_and_unmatched_strings_from_list(
            value_columns, columns_to_ignore, list_scenarios
        )

        # Process invalid columns
        processed_invalid_columns = _process_invalid_columns(invalid_columns)
        if processed_invalid_columns:
            errors.append(f"{self._filename}: Colunas inválidas: {processed_invalid_columns}.")

        # Get filtered description codes
        filtered_description_df = _get_filtered_description_dataframe()
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

        def _validate_scenario_columns(exists_scenario: bool) -> List[str]:
            """Validate scenario columns if scenarios exist."""
            if not exists_scenario:
                return []

            errors = []
            scenario_columns = [SpScenario.RequiredColumn.COLUMN_SYMBOL.name]

            for column in scenario_columns:
                exists_column, error_msg = self._column_exists_dataframe(
                    self.model_sp_scenario.data_loader_model.df_data, column
                )
                if not exists_column:
                    errors.append(error_msg)

            return errors

        def _prepare_values_dataframe() -> pd.DataFrame:
            """Prepare values dataframe by removing ID column if it exists."""
            df_values = self._dataframe.copy()
            id_column = SpValue.RequiredColumn.COLUMN_ID.name

            if id_column in df_values.columns:
                df_values = df_values.drop(columns=[id_column])

            return df_values

        def _validate_numeric_value(value: Any, row_index: int, column: str) -> Tuple[bool, str, bool]:
            """
            Validate a single numeric value.

            Returns:
                Tuple of (is_valid, error_message, has_excessive_decimals)
            """
            # Skip DI (Data Unavailable) values
            if value == "DI":
                return True, "", False

            # Check if value is NaN or can't be converted to numeric
            numeric_value = pd.to_numeric(str(value).replace(',', '.'), errors='coerce')
            if pd.isna(value) or pd.isna(numeric_value):
                error_msg = (f"{self._filename}, linha {row_index + 2}: "
                             f"O valor não é um número válido e nem DI (Dado Indisponível) "
                             f"para a coluna '{column}'.")
                return False, error_msg, False

            # Check decimal places using Decimal for precision
            try:
                decimal_value = Decimal(str(value).replace(',', '.'))
                has_excessive_decimals = decimal_value.as_tuple().exponent < -2
                return True, "", has_excessive_decimals
            except (ValueError, TypeError):
                error_msg = (f"{self._filename}, linha {row_index + 2}: "
                             f"Erro ao processar valor decimal para a coluna '{column}'.")
                return False, error_msg, False

        def _process_column_validation(df_values: pd.DataFrame, column: str) -> Tuple[List[str], set]:
            """
            Process validation for a single column.

            Returns:
                Tuple of (error_messages, rows_with_excessive_decimals)
            """
            errors = []
            excessive_decimal_rows = set()

            invalid_values = []
            first_invalid_row = None
            last_invalid_row = None

            for index, value in df_values[column].items():
                is_valid, error_msg, has_excessive_decimals = _validate_numeric_value(
                    value, index, column
                )

                if not is_valid:
                    invalid_values.append((index + 2, error_msg))
                    if first_invalid_row is None:
                        first_invalid_row = index + 2
                    last_invalid_row = index + 2

                if has_excessive_decimals:
                    excessive_decimal_rows.add(index + 2)

            # Generate error messages based on count
            if len(invalid_values) == 1:
                errors.append(invalid_values[0][1])
            elif len(invalid_values) > 1:
                error_msg = (f"{self._filename}: {len(invalid_values)} valores que não são "
                             f"número válido nem DI (Dado Indisponível) para a coluna '{column}', "
                             f"entre as linhas {first_invalid_row} e {last_invalid_row}.")
                errors.append(error_msg)

            return errors, excessive_decimal_rows

        def _generate_decimal_warning(all_excessive_decimal_rows: set, count_excessive_decimal_rows: int) -> str:
            """Generate warning message for values with excessive decimal places."""
            if not all_excessive_decimal_rows:
                return ""

            count = len(all_excessive_decimal_rows)
            text_existem = "Existem" if count > 1 else "Existe"
            text_valores = "valores" if count > 1 else "valor"

            sorted_rows = sorted(all_excessive_decimal_rows)
            first_row = sorted_rows[0]
            last_row = sorted_rows[-1]

            return (f"{self._filename}: {text_existem} {count_excessive_decimal_rows} {text_valores} com mais de 2 "
                    f"casas decimais, serão consideradas apenas as 2 primeiras casas decimais. "
                    f"Entre as linhas {first_row} e {last_row}.")

        # Get model properties
        exists_scenario = self.model_sp_value.exists_scenario
        list_scenarios = self.model_sp_value.list_scenarios

        # Validate scenario columns if they exist
        scenario_errors = _validate_scenario_columns(exists_scenario)
        if scenario_errors:
            return scenario_errors, warnings

        # Prepare dataframe for validation
        df_values = _prepare_values_dataframe()

        # Get valid columns that match ID patterns
        valid_columns, _ = categorize_strings_by_id_pattern_from_list(
            df_values.columns, list_scenarios
        )

        # Process each valid column
        all_excessive_decimal_rows = set()
        count_excessive_decimal_rows = 0

        for column in valid_columns:
            column_errors, excessive_decimal_rows = _process_column_validation(
                df_values, column
            )
            errors.extend(column_errors)
            count_excessive_decimal_rows += len(excessive_decimal_rows)
            all_excessive_decimal_rows.update(excessive_decimal_rows)

        # Generate warning for excessive decimal places
        decimal_warning = _generate_decimal_warning(all_excessive_decimal_rows, count_excessive_decimal_rows)
        if decimal_warning:
            warnings.append(decimal_warning)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""

        validations = [
            (self.validate_relation_indicators_in_values, NamesEnum.IR.value),
            (self.validate_value_combination_relation, NamesEnum.HTML_DESC.value),
            (self.validate_unavailable_codes_values, NamesEnum.UNAV_INV.value),
        ]

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings

