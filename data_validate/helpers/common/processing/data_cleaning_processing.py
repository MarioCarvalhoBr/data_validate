from typing import Tuple, List

import pandas as pd

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class DataCleaningProcessing:

    def __init__(self) -> None:
        pass

    @staticmethod
    def clean_column_integer(
        df: pd.DataFrame,
        column: str,
        file_name: str,
        min_value: int = 0,
        allow_empty: bool = False,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate and clean a single column, dropping invalid rows.

        Returns the cleaned DataFrame and a list of error messages.
        """
        errors: List[str] = []
        if column not in df.columns:
            errors.append(f"{file_name}: A coluna '{column}' não foi encontrada.")
            return df, errors

        mask_valid: List[bool] = []
        for idx, raw in df[column].items():
            if allow_empty and (pd.isna(raw) or str(raw).strip() == ""):
                mask_valid.append(True)
                continue
            is_valid, message = NumberFormattingProcessing.check_cell_integer(raw, min_value)
            if not is_valid:
                errors.append(f"{file_name}, linha {idx + 2}: A coluna '{column}' contém um valor inválido: {message}")
                mask_valid.append(False)
            else:
                mask_valid.append(True)

        df_clean = df.loc[mask_valid].copy()
        if not allow_empty:
            df_clean[column] = df_clean[column].apply(lambda x: int(float(str(x).replace(",", "."))))
        else:
            df_clean[column] = df_clean[column].apply(lambda x: (int(float(str(x).replace(",", "."))) if pd.notna(x) and str(x).strip() != "" else x))
        return df_clean, errors

    @staticmethod
    def clean_dataframe_integers(
        df: pd.DataFrame,
        file_name: str,
        columns_to_clean: List[str],
        min_value: int = 0,
        allow_empty: bool = False,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Clean multiple columns in the DataFrame, validating integer values.

        Returns the cleaned DataFrame and a list of all errors.
        """
        df_work = df.copy()
        all_errors: List[str] = []

        for col in columns_to_clean:
            df_work, errors = DataCleaningProcessing.clean_column_integer(df_work, col, file_name, min_value, allow_empty)
            all_errors.extend(errors)

        return df_work, all_errors
