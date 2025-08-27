#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

import pandas as pd

from common.utils.processing.collections_processing import extract_numeric_ids_and_unmatched_strings_from_list, \
    categorize_strings_by_id_pattern_from_list, find_differences_in_two_set
from common.utils.processing.data_cleaning import clean_dataframe_integers
from config.config import NamesEnum
from controller.report.model_report import ModelReportList
from data_model import SpDescription, SpScenario, SpLegend, SpValue
from controller.context.data_context import DataModelsContext
from services.spreadsheets.validator_model_abc import ValidatorModelABC


class ModelMappingLegend:
    def __init__(self, column_sp_value=None, indicator_id=None, legend_id=None, default_min_value=0,
                 default_max_value=1):
        self.column_sp_value = column_sp_value
        self.indicator_id = indicator_id
        self.legend_id = legend_id
        self.min_value = default_min_value
        self.max_value = default_max_value

    def __str__(self):
        return f'ModelMappingLegend:(column_sp_value={self.column_sp_value}, indicator_id={self.indicator_id}, legend_description={self.legend_id}, min_value={self.min_value}, max_value={self.max_value})'


class SpLegendValidator(ValidatorModelABC):
    """
    Validates the content of the SpLegend spreadsheet.
    """

    def __init__(self, data_models_context: DataModelsContext, report_list: ModelReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_models_context=data_models_context, report_list=report_list, type_class=SpLegend, **kwargs)

        # Configure
        self.model_sp_legend = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)

        # Get model properties once
        self.scenario_exists_file = self.model_sp_value.scenario_exists_file
        self.scenarios_list = self.model_sp_value.scenarios_list

        self.sp_name_legend = ""
        self.sp_name_description = ""
        self.sp_name_value = ""

        self.global_required_columns = {}
        self.model_dataframes = {}
        # self.

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_legend = self.model_sp_legend.filename
        self.sp_name_description = self.model_sp_description.filename
        self.sp_name_value = self.model_sp_value.filename

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_legend: self.model_sp_legend.data_loader_model.df_data.copy(),
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data.copy(),
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data.copy(),
        }

    def validate_relation_indicators_in_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []

        if self.model_sp_description.data_loader_model.df_data.empty or self.model_sp_legend.data_loader_model.df_data.empty:
            return errors, warnings

        if not self.model_sp_legend.legend_read_success:
            return errors, warnings

        if self.model_sp_legend.structural_errors or self.model_sp_legend.data_cleaning_errors:
            return errors, warnings

        required_columns = {self.sp_name_description: [SpDescription.RequiredColumn.COLUMN_CODE.name,
                                                       SpDescription.RequiredColumn.COLUMN_LEVEL.name,
                                                       SpDescription.DynamicColumn.COLUMN_LEGEND.name]}

        for column in required_columns[self.sp_name_description]:
            exists_column, msg_error = self.column_exists(self.model_dataframes[self.sp_name_description],
                                                          self.sp_name_description, column)
            if not exists_column:
                errors.append(msg_error)
                break

        if errors:
            return errors, warnings

        df_legend = self.model_dataframes[self.sp_name_legend].copy()
        df_description = self.model_dataframes[self.sp_name_description].copy()

        df_description_clean, __ = clean_dataframe_integers(df_description, self.sp_name_description,
                                                            [SpDescription.RequiredColumn.COLUMN_CODE.name],
                                                            min_value=1)


        df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name] = pd.to_numeric(df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name], errors='coerce')
        df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name] = df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name].astype('Int64')

        # Remove all NaN values in column COLUMN_LEGEND
        df_description_clean = df_description_clean.dropna(subset=[SpDescription.RequiredColumn.COLUMN_CODE.name])
        df_legend = df_legend.dropna(subset=[SpLegend.RequiredColumn.COLUMN_CODE.name])

        legends_id_in_description = df_description_clean[
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '1') &
            (df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name].notna()) &
            (pd.to_numeric(df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name],
                           errors='coerce').notna())
            ][SpDescription.DynamicColumn.COLUMN_LEGEND.name].astype(str).tolist()        # DROP NA VALUES

        legends_id_in_legend = df_legend[SpLegend.RequiredColumn.COLUMN_CODE.name].astype(str).unique().tolist()

        set_one = set(legends_id_in_description)
        set_two = set(legends_id_in_legend)

        missing_in_b, missing_in_a = find_differences_in_two_set(
            first_set=set_one,
            second_set=set_two,
        )

        missing_in_b = {int(x) for x in missing_in_b if str(x).isdigit()}
        missing_in_a = {int(x) for x in missing_in_a if str(x).isdigit()}

        if missing_in_b:
            errors.append(
                f"{self.sp_name_description}: Códigos de legenda ausentes em {self.sp_name_legend}: {sorted(list(missing_in_b))}."
            )

        if missing_in_a:
            warnings.append(
                f"{self.sp_name_legend}: Códigos de legenda não referenciados em {self.sp_name_description}: {sorted(list(missing_in_a))}."
            )

        # 1. All codes that are level 1 - Cannot have legends: if they do, error

        codes_indicators_level_one = df_description_clean[df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] == '1'][SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str).tolist()

        legends_id_in_description_level_one = df_description_clean[
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] == '1') &
            (df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name].notna())
        ][SpDescription.DynamicColumn.COLUMN_LEGEND.name].unique().astype(str).tolist()

        if legends_id_in_description_level_one:
            errors.append(
                f"{self.sp_name_description}: Indicadores de nível 1 não podem ter referência de legenda. Códigos com referência em {self.sp_name_legend}: {sorted(list(codes_indicators_level_one))}."
            )

        # 3. All codes that are not level 1 and not level 2 - Must have a legend reference: if not, error
        codes_indicators_other_levels = df_description_clean[
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '1') &
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '2')
            ][SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str).tolist()

        codes_with_legend_other_levels = df_description_clean[
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '1') &
            (df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] != '2') &
            (df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name].notna())
            ][SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str).tolist()

        set_codes_other_levels = set(codes_indicators_other_levels)
        set_codes_with_legend = set(codes_with_legend_other_levels)
        missing_legends_other_levels = set_codes_other_levels - set_codes_with_legend

        if missing_legends_other_levels:
            errors.append(
                f"{self.sp_name_description}: Indicadores de níveis diferentes de 1 e 2 devem ter referência de legenda. Indicadores sem referência em {self.sp_name_legend}: {sorted(list(missing_legends_other_levels))}."
            )

        return errors, warnings

    def validate_range_multiple_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []

        if self.model_sp_value.data_loader_model.df_data.empty or self.model_sp_description.data_loader_model.df_data.empty:
            return errors, warnings

        min_lower_legend_default = self.model_sp_legend.CONSTANTS.MIN_LOWER_LEGEND_DEFAULT
        max_upper_legend_default = self.model_sp_legend.CONSTANTS.MAX_UPPER_LEGEND_DEFAULT
        exists_errors_legend = self.model_sp_legend.structural_errors or self.model_sp_legend.data_cleaning_errors
        required_columns = {self.sp_name_description: [SpDescription.RequiredColumn.COLUMN_CODE.name, SpDescription.RequiredColumn.COLUMN_LEVEL.name]}

        if self.model_sp_legend.legend_read_success:
            required_columns[self.sp_name_description].append(SpDescription.DynamicColumn.COLUMN_LEGEND.name)

        for column in required_columns[self.sp_name_description]:
            exists_column, msg_error = self.column_exists(self.model_dataframes[self.sp_name_description], self.sp_name_description, column)
            if not exists_column:
                errors.append(msg_error)
                break

        if errors:
            return errors, warnings

        df_values = self.model_dataframes[self.sp_name_value].copy()
        df_legend = self.model_dataframes[self.sp_name_legend].copy()
        df_description = self.model_dataframes[self.sp_name_description].copy()

        if SpValue.RequiredColumn.COLUMN_ID.name in df_values.columns:
            df_values.drop(columns=[SpValue.RequiredColumn.COLUMN_ID.name], inplace=True)

        df_description_clean, __ = clean_dataframe_integers(df_description, self.sp_name_description, [SpDescription.RequiredColumn.COLUMN_CODE.name], min_value=1)

        if SpDescription.DynamicColumn.COLUMN_LEGEND.name not in df_description_clean.columns:
            df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name] = pd.Series(dtype='Int64')
        else:
            df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name] = pd.to_numeric(df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name], errors='coerce')
            df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name] = df_description_clean[SpDescription.DynamicColumn.COLUMN_LEGEND.name].astype('Int64')

        codes_indicators_level_one = df_description_clean[df_description_clean[SpDescription.RequiredColumn.COLUMN_LEVEL.name] == '1'][SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str).tolist()
        valid_columns_from_values, __ = categorize_strings_by_id_pattern_from_list(
            items_to_categorize=df_values.columns.tolist(),
            allowed_scenario_suffixes=self.scenarios_list
        )

        groups_legends = pd.DataFrame({str(SpLegend.RequiredColumn.COLUMN_CODE.name): []}).groupby(str(SpLegend.RequiredColumn.COLUMN_CODE.name))
        if not exists_errors_legend:
            groups_legends = df_legend.groupby(str(SpLegend.RequiredColumn.COLUMN_CODE.name))

        mapping_legends = {}
        for data_column_sp_value in valid_columns_from_values:
            aux_indicator_id = data_column_sp_value.split('-')[0]
            aux_data_mapping_legend = ModelMappingLegend(column_sp_value=data_column_sp_value, default_min_value=min_lower_legend_default, default_max_value=max_upper_legend_default)

            if aux_indicator_id in codes_indicators_level_one:
                continue

            row_description = df_description_clean[df_description_clean[SpDescription.RequiredColumn.COLUMN_CODE.name].astype(str) == aux_indicator_id]
            if not row_description.empty:
                aux_data_mapping_legend.indicator_id = aux_indicator_id

                key_legend = row_description.iloc[0][SpDescription.DynamicColumn.COLUMN_LEGEND.name]
                group_legend = groups_legends.get_group(str(key_legend)) if str(key_legend) in groups_legends.groups else None

                if group_legend is not None:
                    aux_data_mapping_legend.legend_id = key_legend

                    group_legend = group_legend[group_legend[SpLegend.RequiredColumn.COLUMN_LABEL.name] != self._data_models_context.config.VALUE_DATA_UNAVAILABLE]
                    if not group_legend.empty:
                        group_legend[SpLegend.RequiredColumn.COLUMN_MINIMUM.name] = pd.to_numeric(group_legend[SpLegend.RequiredColumn.COLUMN_MINIMUM.name], errors='coerce')
                        group_legend[SpLegend.RequiredColumn.COLUMN_MAXIMUM.name] = pd.to_numeric(group_legend[SpLegend.RequiredColumn.COLUMN_MAXIMUM.name], errors='coerce')

                        aux_min_value = group_legend[SpLegend.RequiredColumn.COLUMN_MINIMUM.name].min()
                        aux_max_value = group_legend[SpLegend.RequiredColumn.COLUMN_MAXIMUM.name].max()

                        if not pd.isna(aux_min_value) and not pd.isna(aux_max_value):
                            aux_data_mapping_legend.min_value = aux_min_value
                            aux_data_mapping_legend.max_value = aux_max_value

            mapping_legends[data_column_sp_value] = aux_data_mapping_legend

        df_values_numeric = df_values.copy()
        for col in valid_columns_from_values:
            df_values_numeric[col] = pd.to_numeric(df_values[col].astype(str).str.replace(',', '.'), errors='coerce')

        for data_column_sp_value in valid_columns_from_values:
            code_column = data_column_sp_value.split('-')[0]

            if code_column in codes_indicators_level_one:
                continue

            min_value = mapping_legends[data_column_sp_value].min_value
            max_value = mapping_legends[data_column_sp_value].max_value

            for index, value_numeric in df_values_numeric[data_column_sp_value].items():
                value_original = df_values[data_column_sp_value][index]
                if value_original == self._data_models_context.config.VALUE_DI or pd.isna(value_numeric):
                    continue

                if value_numeric < min_value or value_numeric > max_value:
                    errors.append(
                        f"{self.sp_name_value}, linha {index + 2}: O valor {value_original} está fora do intervalo da legenda ({min_value} a {max_value}) para a coluna '{data_column_sp_value}'.")

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpLegend."""
        validations = []
        # Se existir legenda para validar
        if not self.model_sp_legend.legend_read_success and not self.model_sp_legend.data_loader_model.df_data.empty:
            validations.append((self.validate_relation_indicators_in_legend, NamesEnum.LEG_REL.value))

        validations.append((self.validate_range_multiple_legend, NamesEnum.LEG_RANGE.value))

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
