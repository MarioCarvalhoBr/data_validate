#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
from collections import OrderedDict
from typing import List, Tuple
import pandas as pd

from config.config import Config, NamesEnum
from core.report import ReportList
from data_model import SpScenario
from data_validate.common.utils.formatting.text_formatting import capitalize_text_keep_acronyms
from data_validate.common.utils.validation.data_validation import check_punctuation, check_special_characters_cr_lf, check_unique_values
from data_validate.common.utils.formatting.number_formatting import check_cell
from validation.data_context import DataContext


class SpScenarioValidator:
    """
    Validates the content of the SpScenario spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList):
        # SETUP
        self.data_context = data_context
        self.report_list = report_list

        # UNPACK DATA
        self.sp_model = data_context.get_instance_of(SpScenario)
        self.config = data_context.config
        self.fs_utils = data_context.fs_utils
        self.data_model = self.sp_model.DATA_MODEL
        self.filename = self.sp_model.FILENAME
        self.df_scenario = self.data_model.df_data.copy()

        # SETUP VALIDATION
        self.TITLES_VERITY = self.config.get_verify_names()
        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.run_all_validations()

    def _column_exists(self, column: str) -> Tuple[bool, str]:
        if column not in self.df_scenario.columns:
            return False, f"{self.filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente."
        return True, ""

    def _check_text_length(self, column: str, max_len: int) -> Tuple[List[str], List[str]]:
        """Helper function to validate text length in a column."""
        warnings = []
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_scenario.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                warnings.append(f'{self.filename}, linha {index + 2}: O texto da coluna "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
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

        _, punctuation_warnings = check_punctuation(self.df_scenario, self.filename, columns_dont_punctuation, columns_must_end_with_dot)
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
            df=self.df_scenario,
            file_name=self.filename,
            columns_uniques=columns_to_check
        )
        errors.extend(unique_errors)

        return errors, []

    def run_all_validations(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""
        if self.df_scenario.empty:
            return self.errors, self.warnings

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_SCEN.value),
            (self.validate_unique_values, NamesEnum.UVR_SCEN.value),

        ]

        for func, report_key in validations:
            errors, warnings = func()
            if errors or warnings:
                self.report_list.extend(self.TITLES_VERITY[report_key], errors=errors, warnings=warnings)
            self.errors.extend(errors)
            self.warnings.extend(warnings)

        return self.errors, self.warnings