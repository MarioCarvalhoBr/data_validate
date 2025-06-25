#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
import pandas as pd
from typing import List, Tuple

from config.config import Config, NamesEnum
from core.report import ReportList
from data_model import SpDescription
from data_validate.common.utils.formatting.text_formatting import capitalize_text_keep_acronyms
from data_validate.common.utils.validation.data_validation import check_punctuation
from validation.data_context import DataContext


class SpDescriptionValidator:
    """
    Validates the content of the SpDescription spreadsheet.
    """

    def __init__(self, data_context: DataContext, config: Config, report_list: ReportList):
        self.sp_model = data_context.get_instance_of(SpDescription)
        self.config = config
        self.report_list = report_list

        self.data_model = self.sp_model.DATA_MODEL
        self.filename = self.sp_model.FILENAME
        self.df_description = self.data_model.df_data.copy()

        self.TITLES_VERITY = config.get_verify_names()
        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.run_all_validations()

    def run_all_validations(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpDescription."""
        if self.df_description.empty:
            return self.errors, self.warnings

        validations = [
            (self._validate_html_in_descriptions, NamesEnum.HTML_DESC.value),
            (self._validate_sequential_codes, NamesEnum.SC.value),
            (self._validate_unique_codes, NamesEnum.CU.value),
            (self._validate_text_capitalization, NamesEnum.INP.value),
            (self._validate_indicator_levels, NamesEnum.IL.value),
            (self._validate_punctuation, NamesEnum.MAND_PUNC_DESC.value),
            (self._validate_empty_strings, NamesEnum.EF.value),
            (self._validate_cr_lf_characters, NamesEnum.LB_DESC.value),
            (self._validate_title_length, NamesEnum.TITLES_N.value),
            (self._validate_simple_description_length, NamesEnum.SIMP_DESC_N.value),
        ]

        for func, report_key in validations:
            errors, warnings = func()
            if errors or warnings:
                self.report_list.extend(self.TITLES_VERITY[report_key], errors=errors, warnings=warnings)
            self.errors.extend(errors)
            self.warnings.extend(warnings)

        return self.errors, self.warnings

    def _column_exists(self, column: str) -> Tuple[bool, List[str]]:
        if column not in self.df_description.columns:
            return False, f"{self.filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente."
        return True, []

    def _validate_html_in_descriptions(self) -> Tuple[List[str], List[str]]:
        warnings = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_DESC"]
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_description.iterrows():
            if re.search('<.*?>', str(row[column])):
                warnings.append(f"{self.filename}, linha {index + 2}: Coluna '{column}' não pode conter código HTML.")
        return [], warnings

    def _validate_sequential_codes(self) -> Tuple[List[str], List[str]]:
        errors = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_CODE"]
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        codes = pd.to_numeric(self.df_description[column], errors='coerce')
        if codes.isnull().any():
            errors.append(f"{self.filename}: A verificação foi abortada porque a coluna '{column}' contém valores não numéricos.")
            return errors, []
        codes = codes.dropna().astype(int)
        if codes.iloc[0] != 1:
            errors.append(f"{self.filename}: A coluna '{column}' deve começar em 1.")
        if codes.tolist() != list(range(codes.iloc[0], codes.iloc[-1] + 1)):
            errors.append(f"{self.filename}: A coluna '{column}' deve conter valores inteiros e sequenciais.")
        return errors, []

    def _validate_unique_codes(self) -> Tuple[List[str], List[str]]:
        errors = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_CODE"]
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        duplicated_codes = self.df_description[self.df_description[column].duplicated()][column].tolist()
        if duplicated_codes:
            errors.append(f"{self.filename}: A coluna '{column}' contém códigos duplicados: {duplicated_codes}.")
        return errors, []

    def _validate_text_capitalization(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_to_check = [
            SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_NAME"],
            SpDescription.REQUIRED_COLUMNS["COLUMN_COMPLETE_NAME"]
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue
            for index, row in self.df_description.iterrows():
                text = row[column]
                if pd.isna(text) or text == "":
                    continue
                original_text = str(text).replace('\r', '<CR>').replace('\n', '<LF>')
                corrected_text = capitalize_text_keep_acronyms(str(text).strip())
                if original_text != corrected_text:
                    warnings.append(f"{self.filename}, linha {index + 2}: Coluna '{column}' fora do padrão. Esperado: '{corrected_text}'. Encontrado: '{original_text}'.")
        return [], warnings

    def _validate_indicator_levels(self) -> Tuple[List[str], List[str]]:
        errors = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_LEVEL"]
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        for index, row in self.df_description.iterrows():
            level = pd.to_numeric(row[column], errors='coerce')
            if pd.isna(level) or level < 1 or int(level) != level:
                line_updated = int(index) + 2
                errors.append(f"{self.filename}, linha {line_updated}: O nível do indicador na coluna '{column}' deve ser um número inteiro maior que 0.")
        return errors, []

    def _validate_punctuation(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_dont_punctuation = [SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_NAME"], SpDescription.REQUIRED_COLUMNS["COLUMN_COMPLETE_NAME"]]
        columns_must_end_with_dot = [SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_DESC"], SpDescription.REQUIRED_COLUMNS["COLUMN_COMPLETE_DESC"]]

        for column in list(columns_dont_punctuation + columns_must_end_with_dot):
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(self.df_description, self.filename, columns_dont_punctuation, columns_must_end_with_dot)
        warnings.extend(punctuation_warnings)
        return [], warnings

    def _validate_empty_strings(self) -> Tuple[List[str], List[str]]:
        errors = []
        columns_to_check = list(SpDescription.REQUIRED_COLUMNS.values())
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

    def _validate_cr_lf_characters(self) -> Tuple[List[str], List[str]]:
        warnings = []
        columns_to_check = [
            SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_NAME"],
            SpDescription.REQUIRED_COLUMNS["COLUMN_COMPLETE_NAME"]
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue
            for index, row in self.df_description.iterrows():
                text = str(row[column])
                if pd.isna(text) or text == "":
                    continue
                if text.strip() != text:
                    warnings.append(f"{self.filename}, linha {index + 2}: O texto na coluna '{column}' possui espaços em branco no início ou no fim.")
                if '\r' in text or '\n' in text:
                    warnings.append(f"{self.filename}, linha {index + 2}: O texto na coluna '{column}' contém caracteres de nova linha (CR/LF) inválidos.")
        return [], warnings

    def _validate_title_length(self) -> Tuple[List[str], List[str]]:
        warnings = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_NAME"]
        max_len = SpDescription.INFO.get("MAX_TITLE_LENGTH", 80)
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_description.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                warnings.append(f'{self.filename}, linha {index + 2}: O título em "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
        return [], warnings

    def _validate_simple_description_length(self) -> Tuple[List[str], List[str]]:
        warnings = []
        column = SpDescription.REQUIRED_COLUMNS["COLUMN_SIMPLE_DESC"]
        max_len = SpDescription.INFO.get("MAX_SIMPLE_DESC_LENGTH", 200)
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self.df_description.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                warnings.append(f'{self.filename}, linha {index + 2}: A descrição em "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
        return [], warnings