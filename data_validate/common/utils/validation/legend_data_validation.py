#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
from typing import List, Dict, Any, Tuple
import pandas as pd
from decimal import Decimal, InvalidOperation

def validate_legend_labels(group: pd.DataFrame, code: Any, filename: str, label_col: str) -> List[str]:
    """Validates that labels are unique within a legend group."""
    errors = []
    if group[label_col].duplicated().any():
        duplicate_labels = group[group[label_col].duplicated()][label_col].unique()
        for label in duplicate_labels:
            errors.append(
                f"{filename} [código: {code}]: O label '{label}' está duplicado. Labels devem ser únicos para cada código de legenda."
            )
    return errors

def validate_color_format(group: pd.DataFrame, code: Any, filename: str, color_col: str) -> List[str]:
    """Validates that color format is a valid hexadecimal string."""
    errors = []
    hex_color_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    for index, row in group.iterrows():
        color = row[color_col]
        if pd.notna(color) and not hex_color_pattern.match(str(color)):
            errors.append(
                f"{filename} [código: {code}, linha: {index + 2}]: O formato da cor '{color}' é inválido. Use o formato hexadecimal (ex: #RRGGBB)."
            )
    return errors

def validate_min_max_values(group: pd.DataFrame, code: Any, filename: str, min_col: str, max_col: str, label_col: str) -> List[str]:
    """Validates min/max values for legends, ensuring they are logical and sequential."""
    errors = []
    # Filter out 'Dado indisponível' and sort by min value
    sorted_group = group[group[label_col] != 'Dado indisponível'].copy()

    # Convert to numeric, coercing errors
    sorted_group[min_col] = pd.to_numeric(sorted_group[min_col], errors='coerce')
    sorted_group[max_col] = pd.to_numeric(sorted_group[max_col], errors='coerce')

    # Drop rows where conversion resulted in NaT
    sorted_group.dropna(subset=[min_col, max_col], inplace=True)

    if sorted_group.empty:
        return errors

    sorted_group = sorted_group.sort_values(by=min_col)

    prev_max_val = None
    for index, row in sorted_group.iterrows():
        min_val = row[min_col]
        max_val = row[max_col]

        if min_val >= max_val:
            errors.append(
                f"{filename} [código: {code}, linha: {index + 2}]: O valor mínimo ({min_val}) deve ser menor que o valor máximo ({max_val})."
            )

        if prev_max_val is not None:
            try:
                # Using Decimal for precision
                if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal('0.01'):
                    errors.append(
                        f"{filename} [código: {code}, linha: {index + 2}]: O intervalo não é contínuo. O valor mínimo {min_val} deveria ser {prev_max_val + 0.01} para seguir o valor máximo anterior."
                    )
            except InvalidOperation:
                 errors.append(
                    f"{filename} [código: {code}, linha: {index + 2}]: Valor inválido para operação de mínimo/máximo."
                )


        prev_max_val = max_val

    return errors

def validate_order_sequence(group: pd.DataFrame, code: Any, filename: str, order_col: str) -> List[str]:
    """Validates that order is sequential starting from 1."""
    errors = []
    group = group.copy()
    group[order_col] = pd.to_numeric(group[order_col], errors='coerce')
    if group[order_col].isnull().any():
        errors.append(f"{filename}: A coluna '{order_col}' da legenda '{code}' contém valores não numéricos.")
        return errors

    sorted_order = group[order_col].sort_values()
    expected_sequence = list(range(1, len(sorted_order) + 1))
    if not sorted_order.tolist() == expected_sequence:
        errors.append(
            f"{filename} [código: {code}]: A ordem dos labels não é sequencial ou não começa em 1. Valores encontrados: {sorted_order.tolist()}"
        )
    return errors

    def _validate_order_sequence(self, group: pd.DataFrame, code: int, filename: str, order_col: str):
        """Validate that order is sequential starting from 1"""
        errors = []
        column_order = SpLegend.RequiredColumn.COLUMN_ORDER.name
        orders = group[column_order].dropna().astype(int).tolist()
        expected_orders = list(range(1, len(orders) + 1))

        if orders != expected_orders:
            orders_str = ', '.join(map(str, orders))
            errors.append(
                f"{self._filename}: Sequência de ordem não é sequencial na legenda {code}. Encontrado: [{orders_str}], Esperado: {expected_orders}.")

        # Check for duplicate orders
        order_counts = group[column_order].value_counts()
        duplicated_orders = order_counts[order_counts > 1].index

        if len(duplicated_orders) > 0:
            duplicated_orders_str = ', '.join(map(str, duplicated_orders))
            errors.append(
                f"{self._filename}: Valores duplicados encontrados na coluna '{column_order}' para legenda {code}: [{duplicated_orders_str}]")
        return errors


def validate_code_sequence(df: pd.DataFrame, code_col: str, filename: str) -> List[str]:
    """Validates that legend codes are sequential."""
    errors = []
    if not pd.api.types.is_numeric_dtype(df[code_col]):
        errors.append(f"{filename}: A coluna '{code_col}' contém valores não numéricos e não pode ser validada para sequencialidade.")
        return errors

    unique_codes = sorted(df[code_col].unique())
    if not unique_codes == list(range(min(unique_codes), max(unique_codes) + 1)):
         errors.append(f"{filename}: Os códigos de legenda não são sequenciais. Códigos encontrados: {unique_codes}")
    return errors

