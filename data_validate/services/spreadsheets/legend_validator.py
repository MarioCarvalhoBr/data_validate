#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from idlelib.iomenu import errors
from typing import List, Tuple, Dict, Any
import re

import pandas as pd

from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDescription, SpScenario, SpLegend, SpValue
from controller.data_context import DataModelsContext
from services.spreadsheets.validator_model_abc import ValidatorModelABC


class SpLegendValidator(ValidatorModelABC):
    """
    Validates the content of the SpLegend spreadsheet.
    """

    def __init__(self, data_models_context: DataModelsContext, report_list: ReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_models_context=data_models_context, report_list=report_list, type_class=SpLegend, **kwargs)

        # Configure
        self.model_sp_legend = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)
        self.model_sp_scenario = self._data_models_context.get_instance_of(SpScenario)

        # Get model properties once
        self.exists_scenario = self.model_sp_value.exists_scenario
        self.list_scenarios = self.model_sp_value.list_scenarios

        self.sp_name_legend = ""
        self.sp_name_description = ""
        self.sp_name_value = ""
        self.sp_name_scenario = ""

        self.global_required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_legend = self.model_sp_legend.CONSTANTS.SP_NAME
        self.sp_name_description = self.model_sp_description.CONSTANTS.SP_NAME
        self.sp_name_value = self.model_sp_value.CONSTANTS.SP_NAME
        self.sp_name_scenario = self.model_sp_scenario.CONSTANTS.SP_NAME

        # Define required columns efficiently
        self.global_required_columns = {
            self.sp_name_legend: [SpLegend.RequiredColumn.COLUMN_CODE.name, SpLegend.RequiredColumn.COLUMN_LABEL.name,
                                  SpLegend.RequiredColumn.COLUMN_COLOR.name, SpLegend.RequiredColumn.COLUMN_MINIMUM.name,
                                  SpLegend.RequiredColumn.COLUMN_MAXIMUM.name, SpLegend.RequiredColumn.COLUMN_ORDER.name],
            self.sp_name_description: [SpDescription.RequiredColumn.COLUMN_CODE.name, SpDescription.DynamicColumn.COLUMN_LEGEND.name],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_scenario: [SpScenario.RequiredColumn.COLUMN_SYMBOL.name] if self.exists_scenario else []
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_legend: self.model_sp_legend.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_scenario: self.model_sp_scenario.data_loader_model.df_data if self.exists_scenario else pd.DataFrame()
        }

    def _validate_code_sequence(self, df: pd.DataFrame, column_code: str) -> List[str]:
        """Validate that legend codes are sequential starting from 1"""
        errors = []

        if column_code not in df.columns:
            errors.append(f"{self._filename}: Coluna '{column_code}' não encontrada no DataFrame.")
            return errors

        # Get unique codes and sort them
        unique_codes = sorted(df[column_code].dropna().unique().astype(int))
        expected_codes = list(range(1, len(unique_codes) + 1))

        # Find codes that are out of expected range
        out_of_range_codes = [code for code in unique_codes if code not in expected_codes]

        if out_of_range_codes:
            out_of_range_str = ', '.join(map(str, out_of_range_codes))
            errors.append(
                f"{self._filename}: Códigos de legenda fora da sequência esperada: [{out_of_range_str}]. Esperado: [1, 2, 3, ...].")

        return errors
    def _validate_legend_labels(self, legend_group: pd.DataFrame, code: int):
        """Validate that labels are unique within each legend"""
        errors = []
        column_label = SpLegend.RequiredColumn.COLUMN_LABEL.name
        labels = legend_group[column_label].dropna()
        duplicated_labels = labels[labels.duplicated()].unique()

        if len(duplicated_labels) > 0:
            duplicated_values_str = ', '.join(map(str, duplicated_labels))
            errors.append(f"{self._filename}: Valores duplicados encontrados na coluna '{column_label}' para legenda {code}: [{duplicated_values_str}]")

        return errors
    def _validate_color_format(self, legend_group: pd.DataFrame, code: int):
        """Validate that colors follow hexadecimal format #XXXXXX"""
        errors = []
        column_color = SpLegend.RequiredColumn.COLUMN_COLOR.name

        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        invalid_colors = []

        for idx, color in legend_group[column_color].items():
            if pd.notna(color) and not hex_pattern.match(str(color)):
                invalid_colors.append(str(color))

        if invalid_colors:
            invalid_colors_str = ', '.join(invalid_colors)
            errors.append(
                f"{self._filename}: Formato de cor inválido encontrado na legenda {code}: [{invalid_colors_str}]. Formato esperado: #XXXXXX.")
        return errors
    def _validate_min_max_values(self, legend_group: pd.DataFrame, code: int):
        """
        Validate min/max values based on several rules:
        1. Min and max values must have at most two decimal places.
        2. Min value must be strictly less than the max value.
        3. Intervals must be continuous, with a gap of 0.01 between them.
        """
        errors = []
        column_minimum = SpLegend.RequiredColumn.COLUMN_MINIMUM.name
        column_maximum = SpLegend.RequiredColumn.COLUMN_MAXIMUM.name
        column_label = SpLegend.RequiredColumn.COLUMN_LABEL.name
        column_order = SpLegend.RequiredColumn.COLUMN_ORDER.name

        # Sort by order to check continuity
        sorted_group = legend_group.sort_values(by=column_order).copy()

        # Convert min/max to numeric, coercing errors to NaN
        sorted_group[column_minimum] = pd.to_numeric(sorted_group[column_minimum], errors='coerce')
        sorted_group[column_maximum] = pd.to_numeric(sorted_group[column_maximum], errors='coerce')

        # Helper to check decimal places
        def has_more_than_two_decimal_places(value):
            return pd.notna(value) and (isinstance(value, float) or isinstance(value, int)) and len(str(value).split('.')[-1]) > 2

        invalid_ranges = []
        decimal_errors = []
        continuity_errors = []

        for i, row in enumerate(sorted_group.itertuples(index=False)):
            min_val = getattr(row, column_minimum)
            max_val = getattr(row, column_maximum)
            label = getattr(row, column_label)

            # Skip validation for "Dado indisponível" where values are NaN
            if pd.isna(min_val) and pd.isna(max_val):
                continue

            # Rule 1: Check for more than two decimal places
            if has_more_than_two_decimal_places(min_val):
                decimal_errors.append(f"'{label}' (min: {min_val})")
            if has_more_than_two_decimal_places(max_val):
                decimal_errors.append(f"'{label}' (max: {max_val})")

            # Rule 2: Validate that min < max
            if pd.notna(min_val) and pd.notna(max_val) and min_val >= max_val:
                invalid_ranges.append(f"'{label}' (min: {min_val}, max: {max_val})")

            # Rule 3: Check for interval continuity
            if i > 0:
                prev_row = sorted_group.iloc[i - 1]
                prev_max_val = prev_row[column_maximum]
                prev_label = prev_row[column_label]

                if pd.notna(prev_max_val) and pd.notna(min_val):
                    # Using round to handle potential floating point inaccuracies
                    if round(min_val - prev_max_val, 2) != 0.01:
                        continuity_errors.append(
                            f"'{prev_label}' (max: {prev_max_val}) e '{label}' (min: {min_val})")

        if decimal_errors:
            errors.append(
                f"{self._filename}: Valores com mais de duas casas decimais na legenda {code}: [{', '.join(decimal_errors)}].")
        if invalid_ranges:
            errors.append(
                f"{self._filename}: Intervalos min/max inválidos (min >= max) na legenda {code}: [{', '.join(invalid_ranges)}].")
        if continuity_errors:
            errors.append(
                f"{self._filename}: Intervalos não contínuos na legenda {code}: [{', '.join(continuity_errors)}].")

        return errors

    def _validate_order_sequence(self, legend_group: pd.DataFrame, code: int):
        """Validate that order is sequential starting from 1"""
        errors = []
        column_order = SpLegend.RequiredColumn.COLUMN_ORDER.name
        orders = legend_group[column_order].dropna().astype(int).tolist()
        expected_orders = list(range(1, len(orders) + 1))

        if orders != expected_orders:
            orders_str = ', '.join(map(str, orders))
            errors.append(
                f"{self._filename}: Sequência de ordem não é sequencial na legenda {code}. Encontrado: [{orders_str}], Esperado: {expected_orders}.")

        # Check for duplicate orders
        order_counts = legend_group[column_order].value_counts()
        duplicated_orders = order_counts[order_counts > 1].index

        if len(duplicated_orders) > 0:
            duplicated_orders_str = ', '.join(map(str, duplicated_orders))
            errors.append(
                f"{self._filename}: Valores duplicados encontrados na coluna '{column_order}' para legenda {code}: [{duplicated_orders_str}]")
        return errors

    def validate_structure_columns(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []

        df_legends = self.model_dataframes[self.sp_name_legend]
        column_code = SpLegend.RequiredColumn.COLUMN_CODE.name

        for column in self.global_required_columns[self.sp_name_legend]:
            exists_column, error_msg = self._column_exists_dataframe(df_legends, column)
            if not exists_column:
                return errors, warnings

        # 1. Validate code sequence first
        errors_codes_sequence = self._validate_code_sequence(df_legends, column_code)
        errors.extend(errors_codes_sequence)

        # Group by codigo to validate each legend separately
        grouped = df_legends.groupby(column_code)

        for code, legend_group in grouped:
            errors.extend(self._validate_legend_labels(legend_group, code))
            errors.extend(self._validate_color_format(legend_group, code))
            errors.extend( self._validate_min_max_values(legend_group, code))
            errors.extend(self._validate_order_sequence(legend_group, code))
            pass

        return errors, warnings

    def validate_overlapping_multiple_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def validate_range_multiple_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpLegend."""
        validations = []
        # Verfica se o arquivo existe e se leu com sucesso
        if self.model_sp_legend.data_loader_model.exists_file:
            validations.append((self.validate_structure_columns, NamesEnum.FS.value))
        validations.append((self.validate_overlapping_multiple_legend, NamesEnum.LEG_OVER.value))
        validations.append((self.validate_range_multiple_legend, NamesEnum.LEG_RANGE.value))

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
