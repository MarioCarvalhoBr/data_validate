#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Description spreadsheet validator module.

This module provides validation functionality for Description spreadsheets, ensuring
data quality, format compliance, and business rule adherence for indicator metadata.
"""

import re
from collections import OrderedDict
from typing import List, Tuple, Dict, Any

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing
from data_validate.helpers.common.formatting.text_formatting_processing import TextFormattingProcessing

from data_validate.helpers.common.validation.character_processing import CharacterProcessing

from data_validate.models import SpDescription
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class SpDescriptionValidator(BaseValidator):
    """
    Validates Description spreadsheet content and metadata.

    This validator performs comprehensive checks on indicator descriptions including:
    - HTML tag detection in descriptions
    - Sequential code validation
    - Unique code enforcement
    - Text capitalization standards
    - Indicator level validation
    - Punctuation rules
    - Empty string detection
    - Special character handling (CR/LF)
    - Text length limits
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the Description validator.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models and configuration.
        validation_reports : ModelListReport
            Report aggregator for collecting validation results.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            validation_reports=validation_reports,
            type_class=SpDescription,
            **kwargs,
        )

        self.run()

    def validate_html_in_descriptions(self) -> Tuple[List[str], List[str]]:
        """
        Validate that simple descriptions do not contain HTML tags.

        Checks the simple description column for HTML tag patterns (e.g., <tag>).
        HTML content is not allowed in descriptions as it may cause rendering issues.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: List of error messages (column missing error only)
                - List[str]: List of warning messages for rows containing HTML tags
        """
        warnings = []
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in self._dataframe.iterrows():
            if re.search("<.*?>", str(row[column])):
                index = int(str(index))
                warnings.append(f"{self._filename}, linha {index + 2}: Coluna '{column}' não pode conter código HTML.")
        return [], warnings

    def validate_sequential_codes(self) -> Tuple[List[str], List[str]]:
        """
        Validate that indicator codes are sequential starting from 1.

        Ensures that:
        - All codes are numeric integers
        - The first code is 1
        - Codes follow a sequential pattern (1, 2, 3, ...)

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: List of error messages for validation failures
                - List[str]: Empty list (no warnings generated)
        """
        errors = []

        # 0. Check if the column exists
        column = SpDescription.RequiredColumn.COLUMN_CODE.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        # Load the original codes and cleaned codes
        original_codes = pd.to_numeric(self._dataframe[column], errors="coerce")
        codes_cleaned = self._data_model.RequiredColumn.COLUMN_CODE

        # 1. Check if the column has only integers
        if original_codes.size != codes_cleaned.size:
            errors.append(f"{self._filename}: A verificação foi abortada porque a coluna '{column}' contém valores não numéricos.")
            return errors, []

        # 2. Check if the first code is 1
        if codes_cleaned.at[0] != 1:
            errors.append(f"{self._filename}: A coluna '{column}' deve começar em 1.")

        # 3. Check if the codes are sequential and starting from 1
        if not codes_cleaned.equals(pd.Series(range(1, len(codes_cleaned) + 1))):
            errors.append(f"{self._filename}: A coluna '{column}' deve conter valores inteiros e sequenciais (1, 2, 3, ...).")

        return errors, []

    def validate_unique_codes(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all indicator codes are unique.

        Checks for duplicate code values in the code column and reports any
        duplicates found.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: List of error messages listing duplicate codes
                - List[str]: Empty list (no warnings generated)
        """
        errors = []
        column = SpDescription.RequiredColumn.COLUMN_CODE.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        codes_cleaned = self._data_model.RequiredColumn.COLUMN_CODE
        duplicated_codes = codes_cleaned[codes_cleaned.duplicated()].tolist()

        if duplicated_codes:
            errors.append(f"{self._filename}: A coluna '{column}' contém códigos duplicados: {duplicated_codes}.")

        return errors, []

    def validate_text_capitalization(self) -> Tuple[List[str], List[str]]:
        """
        Validate text capitalization in name columns.

        Checks that simple and complete name columns follow proper capitalization
        standards while preserving acronyms. Also detects special characters like
        CR, LF, and extra spaces that should not be present.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for capitalization issues
        """
        warnings = []
        columns_to_check = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
        ]

        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue

            # Filter non-empty values
            mask = self._dataframe[column].notna() & (self._dataframe[column] != "")
            filtered_data = self._dataframe[mask]

            if not filtered_data.empty:
                # Process original text with all replacements
                original_series = (
                    filtered_data[column]
                    .astype(str)
                    .str.replace("  ", " (EXTRA_SPACE)")
                    .str.replace("\r", "(CR)")
                    .str.replace("\n", "(LF)")
                    .str.replace("\x0d", "(CR)")
                    .str.replace("\x0a", "(LF)")
                )

                # Process expected correct text with all replacements and capitalization
                expected_series = (
                    filtered_data[column]
                    .astype(str)
                    .str.replace("\r", "")
                    .str.replace("\n", "")
                    .str.replace("\x0d", "")
                    .str.replace("\x0a", "")
                    .str.strip()
                    .apply(lambda x: TextFormattingProcessing.capitalize_text_keep_acronyms(x.strip()))
                )

                # Find mismatches
                mismatches_mask = original_series != expected_series
                mismatches_indices = original_series[mismatches_mask].index

                for idx in mismatches_indices:
                    original_text = original_series.loc[idx]
                    expected_text = expected_series.loc[idx]
                    warnings.append(
                        f"{self._filename}, linha {idx + 2}: Valor da coluna '{column}' fora do padrão. Esperado: '{expected_text}'. Encontrado: '{original_text}'."
                    )

        return [], warnings

    def validate_indicator_levels(self) -> Tuple[List[str], List[str]]:
        """
        Validate indicator level values.

        Ensures that all indicator levels in the level column are positive integers
        greater than zero.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: List of error messages for invalid levels
                - List[str]: Empty list (no warnings generated)
        """
        errors = []
        column = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        exists_column, msg_error_column = self._column_exists(column)
        if not exists_column:
            return [msg_error_column], []

        for index, row in self._dataframe.iterrows():
            level = row[column]
            is_valid, __ = NumberFormattingProcessing.check_cell_integer(level, min_value=1)
            if not is_valid:
                line_updated = int(index) + 2
                errors.append(
                    f"{self._filename}, linha {line_updated}: O nível do indicador na coluna '{column}' deve ser um número inteiro maior que 0."
                )
        return errors, []

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        """
        Validate punctuation rules in name and description columns.

        Ensures that:
        - Name columns do not end with punctuation
        - Description columns end with a period

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for punctuation violations
        """
        warnings = []
        columns_dont_punctuation = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
        ]
        columns_must_end_with_dot = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name,
        ]

        for column in list(columns_dont_punctuation + columns_must_end_with_dot):
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = CharacterProcessing.check_characters_punctuation_rules(
            self._dataframe,
            self._filename,
            columns_dont_punctuation,
            columns_must_end_with_dot,
        )
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_empty_strings(self) -> Tuple[List[str], List[str]]:
        """
        Validate that required text columns do not contain empty values.

        Checks that name and description columns contain non-empty, non-null values
        in all rows.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: List of error messages for empty values
                - List[str]: Empty list (no warnings generated)
        """
        errors = []

        columns_to_check = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name,
        ]
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)
                continue
            empty_rows = self._dataframe[self._dataframe[column].isna() | (self._dataframe[column] == "")].index
            if not empty_rows.empty:
                for index in empty_rows:
                    errors.append(f"{self._filename}, linha {index + 2}: Nenhum item da coluna '{column}' pode ser vazio.")
        return errors, []

    def validate_cr_lf_characters(self) -> Tuple[List[str], List[str]]:
        """
        Validate special CR/LF characters in text columns.

        Checks for carriage return (CR) and line feed (LF) characters that should not
        appear at the start/end of columns or anywhere in name columns.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for CR/LF violations
        """
        warnings = []

        columns_start_end = self._data_model.EXPECTED_COLUMNS
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
        __, all_warnings_cr_lf = CharacterProcessing.check_special_characters_cr_lf(
            self._dataframe, self._filename, columns_start_end, columns_anywhere
        )

        warnings.extend(all_warnings_cr_lf)
        return [], warnings

    def validate_title_length(self) -> Tuple[List[str], List[str]]:
        """
        Validate the length of indicator titles.

        Checks that simple name values do not exceed the configured maximum
        title length.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for titles exceeding max length
        """
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name
        max_len = SpDescription.CONSTANTS.MAX_TITLE_LENGTH
        return self._check_text_length(column, max_len)

    def validate_simple_description_length(self) -> Tuple[List[str], List[str]]:
        """
        Validate the length of simple descriptions.

        Checks that simple description values do not exceed the configured maximum
        description length.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors generated)
                - List[str]: List of warning messages for descriptions exceeding max length
        """
        column = SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name
        max_len = SpDescription.CONSTANTS.MAX_SIMPLE_DESC_LENGTH
        return self._check_text_length(column, max_len)

    def _prepare_statement(self) -> None:
        """
        Prepare validation statements.

        This method is currently a placeholder for future initialization logic
        that may be needed before running validations.
        """
        pass

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all Description spreadsheet validations.

        Orchestrates the validation process by executing all description checks
        and building reports based on the validation results. Title length validation
        is conditionally included based on configuration flags.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        - If the dataframe is empty, all validations are marked as not executed
        - Title length validation can be disabled via command line flag
        """
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
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        # Add title length validation if the flag is not set to skip it
        if not self._data_models_context.data_args.data_action.no_warning_titles_length:
            validations.append((self.validate_title_length, NamesEnum.TITLES_N.value))

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
