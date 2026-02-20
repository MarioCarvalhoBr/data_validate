#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing text formatting for error and warning messages.

This module defines the `MessageFormattingProcessing` class, which generates
standardized messages for validation issues such as missing or extra columns
in data files.
"""

from typing import List, Tuple


class MessageFormattingProcessing:
    """
    Utility class for formatting validation messages.

    Provides static methods to construct user-friendly error and warning messages
    related to data structure validation.
    """

    def __init__(self) -> None:
        """Initialize the MessageFormattingProcessing class."""
        pass

    @staticmethod
    def format_text_to_missing_and_expected_columns(
        file_name: str, missing_columns: List[str], extra_columns: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Format error and warning messages for missing and extra columns in a file.

        Constructs lists of localized strings describing structural issues found
        during file validation.

        Args:
            file_name (str): Name of the file being checked.
            missing_columns (List[str]): List of missing column names.
            extra_columns (List[str]): List of extra column names.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing:
                - List of error messages for missing columns.
                - List of warning messages for extra (unexpected) columns.
        """
        errors = []
        warnings = []
        try:
            errors = [f"{file_name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
            warnings = [f"{file_name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
        except Exception as exc:
            errors.append(f"{file_name}: Erro ao processar a formatação de erros e avisos: {str(exc)}")
        return errors, warnings
