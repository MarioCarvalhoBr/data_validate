#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

import pandas as pd

from config.config import NamesEnum
from core.report import ReportList
from data_model import SpScenario
from data_validate.common.utils.validation.data_validation import check_punctuation, check_unique_values
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC


class SpScenarioValidator(ValidatorModelABC):
    """
    Validates the content of the SpScenario spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList, **kwargs: Dict[str, Any]):

        super().__init__(data_context=data_context, report_list=report_list, type_class=SpScenario, **kwargs)

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
        columns_dont_punctuation = [SpScenario.RequiredColumn.COLUMN_NAME.name]
        columns_must_end_with_dot = [SpScenario.RequiredColumn.COLUMN_DESCRIPTION.name]

        list_columns = list(columns_dont_punctuation + columns_must_end_with_dot)
        for column in list_columns:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(self._dataframe, self._filename, columns_dont_punctuation, columns_must_end_with_dot)
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        errors = []
        columns_to_check = [
            SpScenario.RequiredColumn.COLUMN_NAME.name,
            SpScenario.RequiredColumn.COLUMN_SYMBOL.name
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
        """Runs all content validations for SpScenario."""
        if self._dataframe.empty:
            return self._errors, self._warnings

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_SCEN.value),
            (self.validate_unique_values, NamesEnum.UVR_SCEN.value),
        ]
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings