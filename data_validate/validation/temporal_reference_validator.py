#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
from collections import OrderedDict
from typing import List, Tuple, Dict, Any
import pandas as pd

from config.config import Config, NamesEnum
from core.report import ReportList
from data_model import SpTemporalReference
from data_validate.common.utils.formatting.text_formatting import capitalize_text_keep_acronyms
from data_validate.common.utils.validation.data_validation import check_punctuation, check_special_characters_cr_lf, check_unique_values
from data_validate.common.utils.formatting.number_formatting import check_cell
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC


class SpTemporalReferenceValidator(ValidatorModelABC):
    """
    Validates the content of the SpTemporalReference spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList, **kwargs: Dict[str, Any]):

        super().__init__(data_context=data_context, report_list=report_list, type_class=SpTemporalReference, **kwargs)

    def _column_exists(self, column: str) -> Tuple[bool, str]:
        if column not in self._dataframe.columns:
            return False, f"{self._filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente."
        return True, ""

    def _check_text_length(self, column: str, max_len: int) -> Tuple[List[str], List[str]]:
        """Helper function to validate text length in a column."""
        warnings = []
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self._dataframe.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                warnings.append(f'{self._filename}, linha {index + 2}: O texto da coluna "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
        return [], warnings

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_dont_punctuation = []
        columns_must_end_with_dot = [SpTemporalReference.RequiredColumn.COLUMN_DESCRIPTION.name]

        list_columns = list(columns_dont_punctuation + columns_must_end_with_dot)
        for column in list_columns:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(self._dataframe, self._filename, columns_dont_punctuation, columns_must_end_with_dot)
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_reference_years(self) -> Tuple[List[str], List[str]]:
        errors = []

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name,
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)
                return errors, []

        # Remove first row: This is actual year
        column_series_symbol= SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.iloc[1:]
        years = column_series_symbol.unique()

        # Check if all years are greater than the current year
        for year in years:
            if year <= self._data_context.config.CURRENT_YEAR:
                errors.append(f"{self._filename}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.")

        return errors, []

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        errors = []
        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_NAME.name,
            SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.name
        ]

        # Check if columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)

        __, unique_errors = check_unique_values(
            df=self._dataframe,
            file_name=self._filename,
            columns_uniques=columns_to_check
        )
        errors.extend(unique_errors)

        return errors, []

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpTemporalReference."""
        if self._dataframe.empty:
            return self._errors, self._warnings

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_TEMP.value),
            (self.validate_reference_years, NamesEnum.YEARS_TEMP.value),
            (self.validate_unique_values, NamesEnum.UVR_TEMP.value),
        ]
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings