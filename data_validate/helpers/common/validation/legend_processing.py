#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing legend data validation utilities.

This module defines the `LegendProcessing` class, which offers methods
to validate legend labels, sequential types, color formats, order sequences,
and logical consistency of min/max values.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import List, Any

import pandas as pd

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class LegendProcessing:
    """
    Utility class for processing and validating legend data.

    Provides methods to validate labels (uniqueness, emptiness), numeric columns checks,
    logical consistency of intervals (min < max, continuity), color formats, and sequence order.

    Attributes:
        value_data_unavailable: Value representing unavailable data (e.g. "DI" or specific string)
        filename: Name of the file being processed for error reporting
    """

    def __init__(self, value_data_unavailable: Any, filename: str):
        """
        Initialize the LegendProcessing.

        Args:
            value_data_unavailable: The value designated for unavailable data
            filename: The name of the file being validated
        """
        self.value_data_unavailable = value_data_unavailable
        self.filename = filename

    @staticmethod
    def get_min_max_values(df, key_lower, key_upper):
        """
        Calculate global min and max values from dataframe columns.

        Args:
            df: DataFrame containing the data
            key_lower: Column name for lower bounds
            key_upper: Column name for upper bounds

        Returns:
            Tuple of (min_value, max_value)
        """
        min_value = df[key_lower].min()
        max_value = df[key_upper].max()

        return min_value, max_value

    def validate_legend_labels(self, dataframe: pd.DataFrame, code: Any, label_col: str) -> List[str]:
        """
        Validate that labels are unique within a legend group.

        Args:
            dataframe: Validating DataFrame subset
            code: Legend code identifier
            label_col: Column name containing labels

        Returns:
            List of error messages for duplicated labels
        """
        errors = []
        if dataframe[label_col].duplicated().any():
            duplicate_labels = dataframe[dataframe[label_col].duplicated()][label_col].unique()
            for label in duplicate_labels:
                errors.append(
                    f"{self.filename} [código: {code}]: O label '{label}' está duplicado. Labels devem ser únicos para cada código de legenda."
                )
        return errors

    def validate_legend_columns_dtypes_numeric(
        self,
        original_dataframe: pd.DataFrame,
        code_value: Any,
        code_col: str,
        label_col: str,
        min_col: str,
        max_col: str,
        order_col: str,
    ) -> List[str]:
        """
        Validate that required columns have the correct data types (numeric).

        Checks for empty labels, ensures code/min/max/order are numeric, and verifies
        specific rules for 'unavailable data' rows (min/max should be empty).

        Args:
            original_dataframe: Detailed DataFrame
            code_value: Current legend code
            code_col: Column name for codes
            label_col: Column name for labels
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            order_col: Column name for order

        Returns:
            List of validation error messages
        """
        errors = []
        # Check if columns exist
        columns_to_check = [col for col in [code_col, min_col, max_col, order_col] if col in original_dataframe.columns]

        # 1 - Check column label: Null or empty values
        if label_col in original_dataframe.columns:
            empty_labels = original_dataframe[original_dataframe[label_col].isnull() | (original_dataframe[label_col] == "")]
            if not empty_labels.empty:
                indices_empty_labels = empty_labels.index.tolist()
                indices_empty_labels = [idx + 2 for idx in indices_empty_labels]  # Adjust for header row
                errors.append(
                    f"{self.filename} [código: {code_value}, linha(s): {', '.join(map(str, indices_empty_labels))}]: A coluna '{label_col}' contém valores vazios ou nulos."
                )

        # INSTANCE LOCAL DATAFRAME
        local_dataframe = original_dataframe.copy()

        # 2 - Check column code, min, max, order: Numeric values
        for col in columns_to_check:
            local_dataframe[col] = pd.to_numeric(local_dataframe[col], errors="coerce")
        for col in columns_to_check:
            filtered_df = local_dataframe[local_dataframe[label_col] != self.value_data_unavailable]
            if filtered_df[col].isnull().any():
                indices_non_numeric_values = filtered_df[filtered_df[col].isnull()].index.tolist()
                non_numeric_values_original = original_dataframe.loc[indices_non_numeric_values, col].to_list()
                indices_non_numeric_values = [idx + 2 for idx in indices_non_numeric_values]  # Adjust for header row
                errors.append(
                    f"{self.filename} [código: {code_value}, linha(s): {', '.join(map(str, indices_non_numeric_values))}]: A coluna '{col}' contém valores não numéricos: {non_numeric_values_original}"
                )
                continue

        # NEW INSTANCE
        local_dataframe = original_dataframe.copy()

        # 2.2 - If the label is 'Dado indisponível', the min, max values must be empty (cannot have any values)
        if min_col in local_dataframe.columns and max_col in local_dataframe.columns and label_col in local_dataframe.columns:
            unavailable_mask = original_dataframe[label_col] == self.value_data_unavailable
            invalid_min = local_dataframe.loc[unavailable_mask & local_dataframe[min_col].notnull()]
            invalid_max = local_dataframe.loc[unavailable_mask & local_dataframe[max_col].notnull()]

            if not invalid_min.empty:
                indices_invalid_min = invalid_min.index.tolist()
                indices_invalid_min = [idx + 2 for idx in indices_invalid_min]
                errors.append(
                    f"{self.filename} [código: {code_value}, linha(s): {', '.join(map(str, indices_invalid_min))}]: A coluna '{min_col}' deve estar vazia quando o label é '{self.value_data_unavailable}'."
                )
            if not invalid_max.empty:
                indices_invalid_max = invalid_max.index.tolist()
                indices_invalid_max = [idx + 2 for idx in indices_invalid_max]
                errors.append(
                    f"{self.filename} [código: {code_value}, linha(s): {', '.join(map(str, indices_invalid_max))}]: A coluna '{max_col}' deve estar vazia quando o label é '{self.value_data_unavailable}'."
                )

        # 2.3 - There must be exactly one label 'Dado indisponível'. If there is more than one, error. If there is none, error. If there is exactly one, ok.
        if label_col in local_dataframe.columns:
            unavailable_labels = original_dataframe[original_dataframe[label_col] == self.value_data_unavailable]
            if len(unavailable_labels) == 0:
                errors.append(
                    f"{self.filename} [código: {code_value}]: Deve existir um label '{self.value_data_unavailable}' por código, mas nenhum foi encontrado."
                )
            elif len(unavailable_labels) > 1:
                indices_unavailable_labels = unavailable_labels.index.tolist()
                indices_unavailable_labels = [idx + 2 for idx in indices_unavailable_labels]
                errors.append(
                    f"{self.filename} [código: {code_value}, linha(s): {', '.join(map(str, indices_unavailable_labels))}]: Deve existir exatamente um label '{self.value_data_unavailable}' por código, mas foram encontrados {len(unavailable_labels)}."
                )

        # 3 - Check column code, order: Integer values
        for col in [code_col, order_col]:
            if col in local_dataframe.columns:
                for index, value in local_dataframe[col].items():
                    valid, message = NumberFormattingProcessing.check_cell_integer(value, min_value=1)
                    origina_value = original_dataframe.at[index, col]
                    if not valid:
                        errors.append(
                            f"{self.filename} [código: {code_value}, linha: {index + 2}]: A coluna '{col}' contém um valor inválido: O valor '{origina_value}' não é um número inteiro válido."
                        )
        return errors

    def validate_color_format(self, dataframe: pd.DataFrame, code: Any, color_col: str) -> List[str]:
        """
        Validate that color format is a valid hexadecimal string.

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            color_col: Column name containing color codes

        Returns:
            List of error messages for invalid color formats
        """
        errors = []
        hex_color_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
        for index, row in dataframe.iterrows():
            color = row[color_col]
            if not hex_color_pattern.match(str(color)):
                errors.append(
                    f"{self.filename} [código: {code}, linha: {index + 2}]: O formato da cor '{color}' é inválido. Use o formato hexadecimal (ex: #RRGGBB)."
                )
        return errors

    def validate_min_max_has_excessive_decimals(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        min_col: str,
        max_col: str,
        label_col: str,
    ) -> List[str]:
        """
        Validate min/max values for excessive decimals.

        Checks if min/max values exceed allowed decimal precision (usually 2 places).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            label_col: Column name for labels

        Returns:
            List of error messages for excessive decimals
        """
        errors = []
        # Filter out 'Dado indisponível' and sort by min value
        sorted_group = dataframe[dataframe[label_col] != self.value_data_unavailable].copy()

        # Convert to numeric, coercing errors
        sorted_group[min_col] = pd.to_numeric(sorted_group[min_col], errors="coerce")
        sorted_group[max_col] = pd.to_numeric(sorted_group[max_col], errors="coerce")

        # Drop rows where conversion resulted in NaT
        sorted_group.dropna(subset=[min_col, max_col], inplace=True)

        if sorted_group.empty:
            return errors

        sorted_group = sorted_group.sort_values(by=min_col)

        for index, row in sorted_group.iterrows():
            min_val = row[min_col]
            max_val = row[max_col]
            index = int(str(index))

            if NumberFormattingProcessing.check_two_decimals_places(min_val):
                errors.append(
                    f"{self.filename} [código: {code}, linha: {index + 2}]: Legenda inválida. O valor mínimo '{min_val}' possui mais de duas casas decimais. Será considerado o intervalo padrão (0 a 1)."
                )
            if NumberFormattingProcessing.check_two_decimals_places(max_val):
                errors.append(
                    f"{self.filename} [código: {code}, linha: {index + 2}]: Legenda inválida. O valor máximo '{max_val}' possui mais de duas casas decimais. Será considerado o intervalo padrão (0 a 1)."
                )

        return errors

    def validate_min_max_values(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        min_col: str,
        max_col: str,
        label_col: str,
    ) -> List[str]:
        """
        Validate min/max values logical consistency.

        Ensures min < max and that intervals are continuous (next min = prev max + 0.01).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            label_col: Column name for labels

        Returns:
            List of error messages for logical inconsistencies
        """
        errors = []
        # Filter out 'Dado indisponível' and sort by min value
        sorted_group = dataframe[dataframe[label_col] != self.value_data_unavailable].copy()

        # Convert to numeric, coercing errors
        sorted_group[min_col] = pd.to_numeric(sorted_group[min_col], errors="coerce")
        sorted_group[max_col] = pd.to_numeric(sorted_group[max_col], errors="coerce")

        # Drop rows where conversion resulted in NaT
        sorted_group.dropna(subset=[min_col, max_col], inplace=True)

        if sorted_group.empty:
            return errors

        sorted_group = sorted_group.sort_values(by=min_col)

        # If any min or max value has more than 2 decimal places, skip the following validations and return errors

        if any(
            NumberFormattingProcessing.check_two_decimals_places(row[min_col]) or NumberFormattingProcessing.check_two_decimals_places(row[max_col])
            for _, row in sorted_group.iterrows()
        ):
            return errors

        prev_max_val = None
        for index, row in sorted_group.iterrows():
            min_val = row[min_col]
            max_val = row[max_col]

            if min_val >= max_val:
                errors.append(
                    f"{self.filename} [código: {code}, linha: {index + 2}]: O valor mínimo ({min_val}) deve ser menor que o valor máximo ({max_val})."
                )

            if prev_max_val is not None:
                try:
                    # Using Decimal for precision
                    if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal("0.01"):
                        errors.append(
                            f"{self.filename} [código: {code}, linha: {index + 2}]: O intervalo não é contínuo. O valor mínimo {min_val} deveria ser {prev_max_val + 0.01} para seguir o valor máximo anterior."
                        )
                except InvalidOperation:
                    errors.append(f"{self.filename} [código: {code}, linha: {index + 2}]: Valor inválido para operação de mínimo/máximo.")

            prev_max_val = max_val

        return errors

    def validate_order_sequence(self, dataframe: pd.DataFrame, code: Any, order_col: str) -> List[str]:
        """
        Validate that order is sequential starting from 1.

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            order_col: Column name for order

        Returns:
            List of error messages if sequence is broken or invalid
        """
        errors = []
        dataframe = dataframe.copy()
        dataframe[order_col] = pd.to_numeric(dataframe[order_col], errors="coerce")
        if dataframe[order_col].isnull().any():
            errors.append(f"{self.filename}: A coluna '{order_col}' da legenda '{code}' contém valores não numéricos.")
            return errors

        sorted_order = dataframe[order_col].sort_values()
        expected_sequence = list(range(1, len(sorted_order) + 1))
        if not sorted_order.tolist() == expected_sequence:
            errors.append(
                f"{self.filename} [código: {code}]: A coluna '{order_col}' da legenda não é sequencial ou não começa em 1. Valores encontrados: {sorted_order.tolist()}"
            )
        return errors

    def validate_code_sequence(self, dataframe: pd.DataFrame, code_col: str) -> List[str]:
        """
        Validate that legend codes are sequential.

        Args:
            dataframe: DataFrame to validate
            code_col: Column name for legend codes

        Returns:
            List of error messages if codes are not sequential
        """
        errors = []
        local_dataframe = dataframe.copy()
        local_dataframe[code_col] = pd.to_numeric(local_dataframe[code_col], errors="coerce")

        if local_dataframe[code_col].isnull().any():
            errors.append(f"{self.filename}: A coluna '{code_col}' contém valores não numéricos e não pode ser validada para sequencialidade.")

            indices_non_numeric_values_local = local_dataframe[local_dataframe[code_col].isnull()].index.tolist()
            non_numeric_values_original = dataframe.loc[indices_non_numeric_values_local, code_col].tolist()

            errors.append(f"{self.filename}: Valores não numéricos encontrados na coluna '{code_col}': {non_numeric_values_original}")

            return errors

        actual_sequence = []
        for code in local_dataframe[code_col].tolist():
            if code not in actual_sequence:
                actual_sequence.append(int(code))

        expected_sequence = list(range(1, len(actual_sequence) + 1))

        # Report if the first value of the sequence does not start at 1
        if actual_sequence and actual_sequence[0] != 1:
            errors.append(f"{self.filename}: A sequência de códigos de legenda deve começar em 1. Código inicial encontrado: {actual_sequence[0]}")

        if not actual_sequence == expected_sequence:
            errors.append(f"{self.filename}: Os códigos de legenda não são sequenciais. Códigos encontrados: {actual_sequence}")
        return errors
