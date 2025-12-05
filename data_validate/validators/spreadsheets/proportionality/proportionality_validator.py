#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from decimal import Decimal, ROUND_DOWN
from typing import List, Tuple, Dict, Any

import pandas as pd
from pandas import DataFrame

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.formatting.number_formatting import format_number_brazilian
from data_validate.helpers.common.formatting.number_formatting import (
    to_decimal_truncated,
    check_n_decimals_places
)
from data_validate.helpers.common.processing.collections_processing import (
    categorize_strings_by_id_pattern_from_list,
    find_differences_in_two_set_with_message,
)
from data_validate.helpers.common.processing.collections_processing import generate_group_from_list
from data_validate.helpers.common.processing.data_cleaning import (
    clean_dataframe_integers,
)
from data_validate.helpers.common.validation.proportionality_data_validation import (
    get_valids_codes_from_description,
    build_subdatasets,
)
from data_validate.models import SpProportionality, SpDescription, SpValue, SpComposition
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


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

    def _check_sum_equals_one(self, subdatasets, sp_df_values):
        errors = []
        warnings = []

        # Constantes para otimização de acesso
        VALUE_DI = self._data_models_context.config.VALUE_DI

        # Variáveis globais de estado
        global_has_more_than_3_decimals = False
        global_count_more_than_3 = 0
        first_line_init_more_than_3 = 0

        for parent_id, subdataset in subdatasets.items():
            df_data = subdataset.iloc[:, 1:].copy()
            ids = subdataset.iloc[:, 0]

            # ---------------------------------------------------------
            # 1. Validação de Formato (Numérico ou DI)
            # ---------------------------------------------------------
            # Máscara de onde é DI
            is_di = df_data == VALUE_DI

            df_numeric = df_data.replace(",", ".", regex=True).apply(pd.to_numeric, errors='coerce')
            is_invalid = df_numeric.isna() & (~is_di) & (df_data.notna())

            if is_invalid.any().any():
                rows_with_errors = is_invalid.any(axis=1)
                error_indices = rows_with_errors[rows_with_errors].index
                excel_indices = error_indices + 3

                count_errors = is_invalid.sum().sum()

                if count_errors == 1:
                    row_idx = error_indices[0]
                    errors.append(
                        f"{self.sp_name_proportionality}, linha {row_idx + 3}: O valor não é um número válido e nem {VALUE_DI} ({self._data_models_context.config.VALUE_DATA_UNAVAILABLE.capitalize()}) para o indicador pai '{parent_id}'."
                    )
                else:
                    line_init = excel_indices.min()
                    line_end = excel_indices.max()
                    errors.append(
                        f"{self.sp_name_proportionality}: {count_errors} valores que não são número válido nem {VALUE_DI} ({self._data_models_context.config.VALUE_DATA_UNAVAILABLE.capitalize()}) para o indicador pai '{parent_id}' entre as linhas {line_init} e {line_end}."
                    )
                df_data[is_invalid] = VALUE_DI

            # ---------------------------------------------------------
            # 2. Verificação de Casas Decimais (> 3)
            # ---------------------------------------------------------
            # Aplica verificação boolean
            has_excess_decimals_mask = df_data.map(
                lambda value_number: check_n_decimals_places(value_number, VALUE_DI, self._data_models_context.config.PRECISION_DECIMAL_PLACE_TRUNCATE)
            )
            count_excess = has_excess_decimals_mask.sum().sum()

            if count_excess > 0:
                if not global_has_more_than_3_decimals:
                    first_row_idx = has_excess_decimals_mask.any(axis=1).idxmax()
                    first_line_init_more_than_3 = first_row_idx + 3

                global_has_more_than_3_decimals = True
                global_count_more_than_3 += count_excess

            # ---------------------------------------------------------
            # 3. Conversão para Decimal e Soma
            # ---------------------------------------------------------
            # Transforma o dataframe em objetos Decimal (truncados)
            df_decimals = df_data.map(
                lambda value_number: to_decimal_truncated(value_number, VALUE_DI, self._data_models_context.config.PRECISION_DECIMAL_PLACE_TRUNCATE)
            )
            row_sums = df_decimals.sum(axis=1)

            # ---------------------------------------------------------
            # 4. Validação da Soma (= 1)
            # ---------------------------------------------------------
            # CASO A: Soma igual a 0 (Verificação cruzada complexa)
            zero_sum_mask = row_sums == 0
            if zero_sum_mask.any():
                zero_indices = zero_sum_mask[zero_sum_mask].index
                zero_ids = ids.loc[zero_indices]

                relevant_values = sp_df_values[sp_df_values[self.column_name_id].isin(zero_ids)]
                df_check = relevant_values.set_index(self.column_name_id)

                for idx in zero_indices:
                    row_id = ids[idx]
                    if row_id not in df_check.index:
                        continue
                    values_row = df_check.loc[row_id]
                    cols_to_check = [c for c in df_data.columns if c in values_row.index]

                    for col in cols_to_check:
                        val = values_row[col]
                        if val != VALUE_DI:
                            try:
                                if float(str(val).replace(',', '.')) != 0:
                                    errors.append(
                                        f"{self.sp_name_proportionality}: A soma de fatores influenciadores para o ID '{row_id}' no pai '{col}' é 0 (zero). Na planilha {self.sp_name_value}, existe(m) valor(es) para os filhos do indicador '{col}', no mesmo ID, que não é (são) zero ou DI (Dado Indisponível)."
                                    )
                            except:
                                pass

            # CASO B: Soma fora de [0.99, 1.01] e != 0
            limit_low = Decimal("0.99")
            limit_high = Decimal("1.01")

            # Erro Crítico
            error_mask = (row_sums != 0) & ((row_sums < limit_low) | (row_sums > limit_high))

            if error_mask.any():
                for idx in error_mask[error_mask].index:
                    val_sum = row_sums[idx]
                    formatted_sum = format_number_brazilian(val_sum, self._data_models_context.lm.current_language)
                    errors.append(
                        f"{self.sp_name_proportionality}, linha {idx + 3}: A soma dos valores para o indicador pai {parent_id} é {formatted_sum}, e não 1."
                    )

            # Aviso (Warning): Soma diferente de 1 mas dentro da margem [0.99, 1.01]
            warning_mask = (row_sums != 1) & (row_sums >= limit_low) & (row_sums <= limit_high)

            if warning_mask.any():
                for idx in warning_mask[warning_mask].index:
                    val_sum = row_sums[idx]
                    formatted_sum = format_number_brazilian(val_sum, self._data_models_context.lm.current_language)
                    warnings.append(
                        f"{self.sp_name_proportionality}, linha {idx + 3}: A soma dos valores para o indicador pai {parent_id} é {formatted_sum}, e não 1."
                    )

        # ---------------------------------------------------------
        # 5. Aviso Global de Casas Decimais
        # ---------------------------------------------------------
        if global_has_more_than_3_decimals:
            text_existem = "Existem" if global_count_more_than_3 > 1 else "Existe"
            text_valores = "valores" if global_count_more_than_3 > 1 else "valor"
            warnings.append(
                f"{self.sp_name_proportionality}, linha {first_line_init_more_than_3}: {text_existem} {global_count_more_than_3} {text_valores} com mais de 3 casas decimais, serão consideradas apenas as 3 primeiras casas decimais."
            )

        return errors, warnings


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

    def validate_parent_child_relationships(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        if self.model_dataframes[self.sp_name_composition].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_parent_child_relationships,
                        NamesEnum.IND_VAL_PROP.value,
                    )
                ]
            )
            return errors, warnings

        # Somente com dados de descricao e composicao (deve ser igual, apenas extrair)
        local_required_columns = {
            self.sp_name_proportionality: self.global_required_columns[self.sp_name_proportionality],
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Setup dataframes
        df_proportionalities = self.model_dataframes[self.sp_name_proportionality].copy()
        df_composition = self.model_dataframes[self.sp_name_composition].copy()

        # Build subdatasets
        subdatasets = build_subdatasets(df_proportionalities, self.column_name_id)

        # Filter composition to remove level 1 parents
        df_composition = df_composition[df_composition[self.column_name_parent] != "1"]

        dict_grouped_composition = {}
        for __, row in df_composition.iterrows():
            parent = row[self.column_name_parent]
            child = row[self.column_name_child]

            if parent not in dict_grouped_composition:
                dict_grouped_composition[parent] = []

            dict_grouped_composition[parent].append(child)

        for parent_id, subdataset in subdatasets.items():

            cleaned_parent_id = parent_id.split("-")[0]

            if cleaned_parent_id not in dict_grouped_composition.keys():
                if ":" not in parent_id:
                    errors.append(
                        f"{self.sp_name_proportionality}: O indicador pai '{cleaned_parent_id}' (em '{parent_id}') não está presente na coluna '{self.column_name_parent}' da planilha {self.sp_name_composition}."
                    )
                continue

            children_codes = [col for col in subdataset.columns.tolist() if not col.lower().startswith(self.column_name_id)]
            children_codes_cleaned = [filho.split("-")[0] for filho in children_codes]

            dict_children_codes_cleaned = dict()
            dict_children_codes_cleaned.setdefault(cleaned_parent_id, []).extend(children_codes_cleaned)

            set_errors = {
                f"{self.sp_name_proportionality}: O indicador '{filho}' (em '{filho_orig}') não é filho do indicador '{cleaned_parent_id}' (em '{parent_id}') conforme especificado em {self.sp_name_composition}."
                for filho, filho_orig in zip(children_codes_cleaned, children_codes)
                if filho not in dict_grouped_composition[cleaned_parent_id]
            }
            errors.extend(set_errors)

            for child in dict_grouped_composition[cleaned_parent_id]:
                if child not in dict_children_codes_cleaned[cleaned_parent_id]:
                    code_pai_local = parent_id.split("-")[0]
                    errors.append(
                        f"{self.sp_name_proportionality}: Deve existir pelo menos uma relação do indicador filho '{child}' com o indicador pai '{code_pai_local}' (em '{parent_id}') conforme especificado em {self.sp_name_composition}."
                    )

        errors = sorted(set(errors))

        return errors, warnings

    def validate_sum_properties_in_influencing_factors(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        if self.model_dataframes[self.sp_name_value].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_sum_properties_in_influencing_factors,
                        NamesEnum.SUM_PROP.value,
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

        subdatasets = build_subdatasets(df_proportionalities, self.column_name_id)

        errors, warnings = self._check_sum_equals_one(subdatasets, df_values)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpProportionality."""

        validations = [
            (self.validate_relation_indicators_in_proportionality, NamesEnum.IR.value),
            (self.validate_columns_repeated_indicators, NamesEnum.REP_IND_PROP.value),
            (self.validate_relation_indicators_in_value_and_proportionality, NamesEnum.IND_VAL_PROP.value),
            (self.validate_parent_child_relationships, NamesEnum.IR_PROP.value),
            (self.validate_sum_properties_in_influencing_factors, NamesEnum.SUM_PROP.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
