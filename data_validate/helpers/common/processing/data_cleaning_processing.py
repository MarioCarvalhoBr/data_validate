#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing data cleaning utilities including integer validation.

This module defines the `DataCleaningProcessing` class, which offers methods
to clean and validate DataFrame columns, specifically ensuring integer integrity
and handling empty values.
"""

from typing import Callable, cast

import pandas as pd

from data_validate.helpers.common.default_translate import get_default_translate
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class DataCleaningProcessing:
    """
    Utility class for data cleaning and validation operations.

    Provides static methods to clean DataFrame columns by validating data types
    (e.g., integrity checks for integer columns) and filtering out invalid rows.
    """

    def __init__(self) -> None:
        """Initialize the DataCleaningProcessing class."""
        pass

    @staticmethod
    def clean_column_integer(
        df: pd.DataFrame,
        column: str,
        file_name: str,
        min_value: int = 0,
        allow_empty: bool = False,
        translate: Callable[..., str] | None = None,
        rule_id: str = "",
    ) -> tuple[pd.DataFrame, list[str]]:
        """
        Validate and clean a single DataFrame column, enforcing integer constraints.

        Iterates through the column to verify each cell contains a valid integer
        (or is empty if allowed). Drops invalid rows and returns cleaning errors.

        Args:
            df (pd.DataFrame): The DataFrame containing the column to clean.
            column (str): The name of the column to validate.
            file_name (str): Original file name for error reporting context.
            min_value (int, optional): The minimum allowed integer value. Defaults to 0.
            allow_empty (bool, optional): If True, treats empty cells as valid. Defaults to False.
            translate (Callable[..., str], optional): Message-catalog renderer
                (`key, **params -> str`). ARC-005: every error message is a catalog
                key, never a hardcoded literal; defaults to `get_default_translate()`
                so callers that only inspect the returned dataframe (every `rules/*.py`
                caller discards these messages) do not need to pass one.
            rule_id (str, optional): The rule ID (`"CLEAN-001"`, …) this call site
                implements, used to key the per-cell invalid-value message as
                `rule.<rule_id>.error`. Callers that do not render the returned
                messages (every `rules/*.py` caller) may leave this empty; it then
                falls back to a shared, rule-agnostic key.

        Returns:
            tuple[pd.DataFrame, list[str]]: A tuple containing:
                - pd.DataFrame: A new DataFrame with only valid rows for this column.
                - list[str]: A list of error messages for invalid cells found.
        """
        translate = translate or get_default_translate()
        error_key = f"rule.{rule_id}.error" if rule_id else "rule.file_cleaning.invalid_cell"

        errors: list[str] = []
        if column not in df.columns:
            errors.append(translate("rule.file_cleaning.column_not_found", filename=file_name, column=column))
            return df, errors

        mask_valid: list[bool] = []
        for idx, raw in df[column].items():
            if allow_empty and (pd.isna(raw) or str(raw).strip() == ""):
                mask_valid.append(True)
                continue
            is_valid, message = NumberFormattingProcessing.check_cell_integer(raw, min_value, translate=translate)
            if not is_valid:
                errors.append(
                    translate(error_key, filename=file_name, row=cast(int, idx) + 2, column=column, message=message)
                )
                mask_valid.append(False)
            else:
                mask_valid.append(True)

        df_clean = df.loc[mask_valid].copy()
        if not allow_empty:
            df_clean[column] = df_clean[column].apply(lambda x: int(float(str(x).replace(",", "."))))
        else:
            df_clean[column] = df_clean[column].apply(
                lambda x: int(float(str(x).replace(",", "."))) if bool(pd.notna(x)) and str(x).strip() != "" else x
            )
        return df_clean, errors

    @staticmethod
    def clean_dataframe_integers(
        df: pd.DataFrame,
        file_name: str,
        columns_to_clean: list[str],
        min_value: int = 0,
        allow_empty: bool = False,
        translate: Callable[..., str] | None = None,
        rule_id: str = "",
    ) -> tuple[pd.DataFrame, list[str]]:
        """
        Clean multiple columns in the DataFrame, enforcing integer validation on all.

        Sequentially applies `clean_column_integer` to each specified column,
        accumulating errors and progressively filtering the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to process.
            file_name (str): Original file name for error reporting context.
            columns_to_clean (list[str]): List of column names to validate and clean.
            min_value (int, optional): Minimum allowed value for integers. Defaults to 0.
            allow_empty (bool, optional): If True, allows empty values in the columns. Defaults to False.
            translate (Callable[..., str], optional): Message-catalog renderer, see
                `clean_column_integer`.
            rule_id (str, optional): The rule ID this call site implements, see
                `clean_column_integer`.

        Returns:
            tuple[pd.DataFrame, list[str]]: A tuple containing:
                - pd.DataFrame: The fully cleaned DataFrame.
                - list[str]: Aggregated list of all validation errors encountered.
        """
        df_work = df.copy()
        all_errors: list[str] = []

        for col in columns_to_clean:
            df_work, errors = DataCleaningProcessing.clean_column_integer(
                df_work, col, file_name, min_value, allow_empty, translate=translate, rule_id=rule_id
            )
            all_errors.extend(errors)

        return df_work, all_errors
