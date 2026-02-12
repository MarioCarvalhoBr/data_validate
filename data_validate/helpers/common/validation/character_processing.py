#  Copyright (c) 2026 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing character validation utilities for DataFrames.

This module defines the `CharacterProcessing` class, which includes methods
to check for punctuation rules and special characters (CR/LF) in DataFrame text columns.
"""

import re
from typing import Optional, List, Tuple

import pandas as pd


class CharacterProcessing:
    """
    Utility class for validating character content in DataFrame columns.

    Provides static methods to enforce punctuation rules (e.g., must/must not end with dot)
    and to detect prohibited special characters like Carriage Return (CR) and Line Feed (LF).
    """

    def __init__(self) -> None:
        """Initialize the CharacterProcessing class."""
        pass

    @staticmethod
    def check_characters_punctuation_rules(
        dataframe: pd.DataFrame,
        file_name: str,
        columns_dont_punctuation: Optional[List[str]] = None,
        columns_must_end_with_dot: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Check punctuation rules for specified columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_dont_punctuation: Columns that should not end with punctuation
            columns_must_end_with_dot: Columns that must end with a dot

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        warnings: List[str] = []

        columns_dont_punctuation = columns_dont_punctuation or []
        columns_must_end_with_dot = columns_must_end_with_dot or []

        # Filter existing columns
        existing_no_punct = [col for col in columns_dont_punctuation if col in dataframe.columns]
        existing_with_dot = [col for col in columns_must_end_with_dot if col in dataframe.columns]

        punctuation_chars = {",", ".", ";", ":", "!", "?"}

        for column in existing_no_punct:
            non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
            if non_empty_mask.any():
                text_series = dataframe.loc[non_empty_mask, column].astype(str).str.strip()
                ends_with_punct = text_series.str[-1].isin(punctuation_chars)

                for idx in text_series[ends_with_punct].index:
                    warnings.append(f"{file_name}, linha {idx + 2}: O valor da coluna '{column}' não deve terminar com pontuação.")

        for column in existing_with_dot:
            non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
            if non_empty_mask.any():
                text_series = dataframe.loc[non_empty_mask, column].astype(str).str.strip()
                not_ends_with_dot = ~text_series.str.endswith(".")

                for idx in text_series[not_ends_with_dot].index:
                    warnings.append(f"{file_name}, linha {idx + 2}: O valor da coluna '{column}' deve terminar com ponto.")

        return not bool(warnings), warnings

    @staticmethod
    def check_special_characters_cr_lf_columns_start_end(
        dataframe: pd.DataFrame,
        file_name: str,
        columns_start_end: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Check for CR/LF characters at start and end of text in specified columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_start_end: Columns to check for CR/LF at start/end

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        warnings: List[str] = []
        columns_start_end = columns_start_end or []

        existing_columns = [col for col in columns_start_end if col in dataframe.columns]

        for column in existing_columns:
            non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
            if not non_empty_mask.any():
                continue

            # Get non-empty values safely
            non_empty_values = dataframe[column][non_empty_mask]
            if len(non_empty_values) == 0:
                continue

            text_series = non_empty_values.astype(str)

            # Check for CR/LF at positions using vectorized operations
            patterns = {
                "end_cr": (
                    text_series.str.endswith("\x0d"),
                    "O texto da coluna '{column}' possui um caracter inválido (CR) no final do texto. Remova o último caractere do texto.",
                ),
                "end_lf": (
                    text_series.str.endswith("\x0a"),
                    "O texto da coluna '{column}' possui um caracter inválido (LF) no final do texto. Remova o último caractere do texto.",
                ),
                "start_cr": (
                    text_series.str.startswith("\x0d"),
                    "O texto da coluna '{column}' possui um caracter inválido (CR) no início do texto. Remova o primeiro caractere do texto.",
                ),
                "start_lf": (
                    text_series.str.startswith("\x0a"),
                    "O texto da coluna '{column}' possui um caracter inválido (LF) no início do texto. Remova o primeiro caractere do texto.",
                ),
            }

            for pattern_name, (mask, message_template) in patterns.items():
                for idx in text_series[mask].index:
                    warnings.append(f"{file_name}, linha {idx + 2}: " + message_template.format(column=column))

        return not bool(warnings), warnings

    @staticmethod
    def check_special_characters_cr_lf_columns_anywhere(
        dataframe: pd.DataFrame,
        file_name: str,
        columns_anywhere: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Check for CR/LF characters anywhere in text in specified columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_anywhere: Columns to check for CR/LF anywhere in text

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        warnings: List[str] = []
        columns_anywhere = columns_anywhere or []

        existing_columns = [col for col in columns_anywhere if col in dataframe.columns]

        for column in existing_columns:
            non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
            if not non_empty_mask.any():
                continue

            # Get non-empty values safely
            non_empty_values = dataframe[column][non_empty_mask]
            if len(non_empty_values) == 0:
                continue

            text_series = non_empty_values.astype(str)

            def find_cr_lf_positions(text: str) -> List[Tuple[int, str]]:
                """Find positions of CR/LF characters in text."""
                return [(match.start() + 1, "CR" if match.group() == "\x0d" else "LF") for match in re.finditer(r"[\x0D\x0A]", text)]

            cr_lf_positions = text_series.apply(find_cr_lf_positions)

            for idx, positions in cr_lf_positions.items():
                for pos, char_type in positions:
                    warnings.append(
                        f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido ({char_type}) na posição {pos}. Remova o caractere do texto."
                    )

        return not bool(warnings), warnings

    @staticmethod
    def check_special_characters_cr_lf(
        dataframe: pd.DataFrame,
        file_name: str,
        columns_start_end: Optional[List[str]] = None,
        columns_anywhere: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Check for CR/LF special characters in DataFrame columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_start_end: Columns to check for CR/LF at start/end positions
            columns_anywhere: Columns to check for CR/LF anywhere in text

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        all_warnings: List[str] = []

        _, warnings_start_end = CharacterProcessing.check_special_characters_cr_lf_columns_start_end(dataframe, file_name, columns_start_end)
        all_warnings.extend(warnings_start_end)

        _, warnings_anywhere = CharacterProcessing.check_special_characters_cr_lf_columns_anywhere(dataframe, file_name, columns_anywhere)
        all_warnings.extend(warnings_anywhere)

        return not bool(all_warnings), all_warnings
