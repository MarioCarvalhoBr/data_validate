#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
from collections import OrderedDict
from typing import List, Tuple
import pandas as pd

from config.config import Config, NamesEnum
from core.report import ReportList
from data_model import SpDescription
from data_validate.common.utils.formatting.text_formatting import capitalize_text_keep_acronyms
from data_validate.common.utils.validation.data_validation import check_punctuation, check_special_characters_cr_lf
from data_validate.common.utils.formatting.number_formatting import check_cell
from validation.data_context import DataContext


class SpDescriptionValidator:
    """
    Validates the content of the SpDescription spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList):
        # SETUP
        self.data_context = data_context
        self.report_list = report_list

        # UNPACK DATA
        self.sp_model = data_context.get_instance_of(SpDescription)
        self.config = data_context.config
        self.fs_utils = data_context.fs_utils
        self.data_model = self.sp_model.DATA_MODEL
        self.filename = self.sp_model.FILENAME
        self.df_description = self.data_model.df_data.copy()

        # SETUP VALIDATION
        self.TITLES_VERITY = self.config.get_verify_names()
        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.run_all_validations()

    def _column_exists(self, column: str) -> Tuple[bool, str]:
        if column not in self.df_description.columns:
            return False, f"{self.filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente."
        return True, ""

    def _check_text_length(self, column: str, max_len: int) -> Tuple[List[str], List[str]]:
        """Helper function to validate text length in a column."""
        warnings = []
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_description.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                warnings.append(f'{self.filename}, linha {index + 2}: O texto da coluna "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
        return [], warnings

    def validate_html_in_descriptions(self) -> Tuple[List[str], List[str]]:
        warnings = []
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_description.iterrows():
            if re.search('<.*?>', str(row[column])):
                index = int(str(index))
                warnings.append(f"{self.filename}, linha {index + 2}: Coluna '{column}' não pode conter código HTML.")
        return [], warnings

    def validate_sequential_codes(self) -> Tuple[List[str], List[str]]:
        errors = []

        # 0. Check if the column exists
        column = SpDescription.RequiredColumn.COLUMN_CODE.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        # Load the original codes and cleaned codes
        original_codes = pd.to_numeric(self.df_description[column], errors='coerce')
        codes_cleaned = self.sp_model.RequiredColumn.COLUMN_CODE

        # 1. Check if the column has only integers
        if original_codes.size != codes_cleaned.size:
            errors.append(f"{self.filename}: A verificação foi abortada porque a coluna '{column}' contém valores não numéricos.")
            return errors, []

        # 2. Check if the first code is 1
        if codes_cleaned.at[0] != 1:
            errors.append(f"{self.filename}: A coluna '{column}' deve começar em 1.")

        # 3. Check if the codes are sequential and starting from 1
        if not codes_cleaned.equals(pd.Series(range(1, len(codes_cleaned) + 1))):
            errors.append(f"{self.filename}: A coluna '{column}' deve conter valores inteiros e sequenciais (1, 2, 3, ...).")

        return errors, []

    def validate_unique_codes(self) -> Tuple[List[str], List[str]]:
        errors = []
        column = SpDescription.RequiredColumn.COLUMN_CODE.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        codes_cleaned = self.sp_model.RequiredColumn.COLUMN_CODE
        duplicated_codes = codes_cleaned[codes_cleaned.duplicated()].tolist()

        if duplicated_codes:
            errors.append(f"{self.filename}: A coluna '{column}' contém códigos duplicados: {duplicated_codes}.")

        return errors, []

    def validate_text_capitalization(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_to_check = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name
        ]

        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue

            # Filter non-empty values
            mask = self.df_description[column].notna() & (self.df_description[column] != "")
            filtered_data = self.df_description[mask]

            if not filtered_data.empty:
                # Process original text with all replacements
                original_series = (filtered_data[column].astype(str)
                                   .str.replace('\r', '<CR>')
                                   .str.replace('\n', '<LF>')
                                   .str.replace('\x0D', '<CR>')
                                   .str.replace('\x0A', '<LF>'))

                # Process expected correct text with all replacements and capitalization
                expected_series = (filtered_data[column].astype(str)
                                   .str.replace('\x0D', '')
                                   .str.replace('\x0A', '')
                                   .str.strip()
                                   .apply(lambda x: capitalize_text_keep_acronyms(x.strip())))

                # Find mismatches
                mismatches_mask = original_series != expected_series
                mismatches_indices = original_series[mismatches_mask].index

                for idx in mismatches_indices:
                    original_text = original_series.loc[idx]
                    expected_text = expected_series.loc[idx]
                    warnings.append(
                        f"{self.filename}, linha {idx + 2}: Valor da coluna '{column}' fora do padrão. Esperado: '{expected_text}'. Encontrado: '{original_text}'.")

        return [], warnings

    def validate_indicator_levels(self) -> Tuple[List[str], List[str]]:
        errors = []
        column = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        for index, row in self.df_description.iterrows():
            level = row[column]
            is_valid, __ = check_cell(level, min_value=1)
            if not is_valid:
                line_updated = int(index) + 2
                errors.append(f"{self.filename}, linha {line_updated}: O nível do indicador na coluna '{column}' deve ser um número inteiro maior que 0.")
        return errors, []

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_dont_punctuation = [SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name, SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name]
        columns_must_end_with_dot = [SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name, SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name]

        for column in list(columns_dont_punctuation + columns_must_end_with_dot):
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(self.df_description, self.filename, columns_dont_punctuation, columns_must_end_with_dot)
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_empty_strings(self) -> Tuple[List[str], List[str]]:
        errors = []

        columns_to_check = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)
                continue
            empty_rows = self.df_description[self.df_description[column].isna() | (self.df_description[column] == "")].index
            if not empty_rows.empty:
                for index in empty_rows:
                    errors.append(f"{self.filename}, linha {index + 2}: Nenhum item da coluna '{column}' pode ser vazio.")
        return errors, []

    def validate_cr_lf_characters(self) -> Tuple[List[str], List[str]]:
        warnings = []

        columns_start_end = self.sp_model.EXPECTED_COLUMNS
        columns_anywhere = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
        ]

        # Create an ordered dictionary with the columns
        columns_to_check = list(OrderedDict.fromkeys(columns_anywhere + columns_start_end).keys())

        # Check if the columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue

        # Run the checks for CR/LF characters
        __, all_warnings_cr_lf = check_special_characters_cr_lf(self.df_description, self.filename, columns_start_end, columns_anywhere)

        warnings.extend(all_warnings_cr_lf)
        return [], warnings

    def validate_title_length(self) -> Tuple[List[str], List[str]]:
        """Validate the length of titles."""
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name
        max_len = SpDescription.CONSTANTS.MAX_TITLE_LENGTH
        return self._check_text_length(column, max_len)

    def validate_simple_description_length(self) -> Tuple[List[str], List[str]]:
        """Validate the length of simple descriptions."""
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name
        max_len = SpDescription.CONSTANTS.MAX_SIMPLE_DESC_LENGTH
        return self._check_text_length(column, max_len)

    def run_all_validations(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpDescription."""
        if self.df_description.empty:
            return self.errors, self.warnings

        validations = [
            (self.validate_html_in_descriptions, NamesEnum.HTML_DESC.value),
            (self.validate_sequential_codes, NamesEnum.SC.value),
            (self.validate_unique_codes, NamesEnum.CO_UN.value),
            (self.validate_text_capitalization, NamesEnum.INP.value),
            (self.validate_indicator_levels, NamesEnum.IL.value),
            (self.validate_punctuation, NamesEnum.MAND_PUNC_DESC.value),
            (self.validate_empty_strings, NamesEnum.EF.value),
            (self.validate_cr_lf_characters, NamesEnum.LB_DESC.value),
            (self.validate_simple_description_length, NamesEnum.SIMP_DESC_N.value),
        ]
        # Add title length validation if the flag is not set to skip it
        if not self.data_context.data_args.data_action.no_warning_titles_length:
            validations.append((self.validate_title_length, NamesEnum.TITLES_N.value))

        for func, report_key in validations:
            errors, warnings = func()
            if errors or warnings:
                self.report_list.extend(self.TITLES_VERITY[report_key], errors=errors, warnings=warnings)
            self.errors.extend(errors)
            self.warnings.extend(warnings)

        return self.errors, self.warnings