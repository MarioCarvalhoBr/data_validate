#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing numeric formatting and validation utilities.

This module defines the `NumberFormattingProcessing` class, which offers methods
for decimal manipulation, number validation (integer, nan), parsing, and locale-aware
formatting useful for handling data spreadsheet numeric values.
"""

import math
from decimal import Decimal, InvalidOperation
from typing import Tuple, Any

import pandas as pd
from babel.numbers import format_decimal


class NumberFormattingProcessing:
    """
    Utility class for numeric value processing and formatting.

    Provides static methods for safe decimal conversion, truncation, decimal place validation,
    NaN checks, and formatting numbers according to locale conventions (e.g., Brazilian Portuguese).
    """

    def __init__(self) -> None:
        """Initialize the NumberFormattingProcessing class."""
        pass

    @staticmethod
    def to_decimal_truncated(value_number: Any, value_to_ignore: Any, precision: int) -> Decimal:
        """
        Convert a value to a truncated Decimal object.

        Truncates the decimal part of the number to the specified precision without rounding.
        Handles comma as decimal separator. Returns 0 if value is ignored or invalid.

        Args:
            value_number (Any): The number to convert.
            value_to_ignore (Any): A specific value (e.g., 'Unavailable') to treat as 0.
            precision (int): The number of decimal places to keep.

        Returns:
            Decimal: The truncated Decimal value, or 0 if invalid/ignored.
        """
        if pd.isna(value_number) or value_number == value_to_ignore:
            return Decimal("0")

        s_val = str(value_number).replace(",", ".")
        try:
            if "." in s_val:
                integer_part, decimal_part = s_val.split(".")
                truncated_val = f"{integer_part}.{decimal_part[:precision]}"
            else:
                truncated_val = s_val
            return Decimal(truncated_val)
        except (ValueError, InvalidOperation, Exception):
            return Decimal("0")

    @staticmethod
    def check_n_decimals_places(value_number: Any, value_to_ignore: Any, number_decimal_places: int) -> bool:
        """
        Check if a number has more decimal places than allowed.

        Verifies if the number of decimal digits exceeds `number_decimal_places`.

        Args:
            value_number (Any): The number to check.
            value_to_ignore (Any): Value to skip checking.
            number_decimal_places (int): Maximum allowed decimal places.

        Returns:
            bool: True if the number has *more* decimals than allowed, False otherwise.
        """
        if pd.isna(value_number) or value_number == value_to_ignore:
            return False
        decimal_value = Decimal(str(value_number).replace(",", "."))
        return decimal_value.as_tuple().exponent < -number_decimal_places

    @staticmethod
    def check_two_decimals_places(value: Any) -> bool:
        """
        Check if a value has more than two decimal places.

        Specialized check for exactly 2 decimal places constraint. Handles infinity and NaN checks.

        Args:
            value (Any): The value to check.

        Returns:
            bool: True if the value has more than 2 decimal places, False otherwise.
        """
        if value in [float("-inf"), float("inf")] or pd.isna(value):
            return False
        return NumberFormattingProcessing.check_n_decimals_places(value, 0, 2)

    @staticmethod
    def format_number_brazilian(n: float, locale: str = "pt_BR") -> str:
        """
        Format a number using Brazilian locale conventions.

        Args:
            n (float): Number to format.
            locale (str, optional): Locale string. Default is "pt_BR".

        Returns:
            str: Formatted number string (e.g., '1.234,56').
        """
        return format_decimal(number=n, locale=locale)

    @staticmethod
    def is_nan(value: Any) -> bool:
        """
        Check if a value is NaN (Not a Number).

        Detects both pandas NaN/NaT and standard math.nan.

        Args:
            value (Any): Value to check.

        Returns:
            bool: True if value is NaN, False otherwise.
        """
        try:
            return pd.isna(value) or math.isnan(float(value))
        except (ValueError, TypeError, Exception):
            return False

    @staticmethod
    def parse_numeric(cell: Any) -> Tuple[bool, float]:
        """
        Attempt to parse a cell value to a float.

        Handles string inputs by replacing commas with dots before conversion.

        Args:
            cell (Any): Value to parse.

        Returns:
            Tuple[bool, float]: A tuple containing:
                - True and the float value if successful.
                - False and 0.0 if parsing failed.
        """
        if isinstance(cell, str):
            cell = cell.replace(",", ".")
        try:
            return True, float(cell)
        except (ValueError, TypeError):
            return False, 0.0

    @staticmethod
    def validate_integer(value: float, min_value: int = 0) -> Tuple[bool, str]:
        """
        Validate that a float value represents a valid integer within constraints.

        Checks if the float has no decimal part and is greater than or equal to `min_value`.

        Args:
            value (float): The numeric value to validate.
            min_value (int, optional): Minimum allowed value. Default is 0.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - True and an empty string if valid.
                - False and an error message if invalid.
        """
        if not value.is_integer():
            return False, f"O valor '{value}' não é um número inteiro."
        if int(value) < min_value:
            return False, f"O valor '{int(value)}' é menor que {min_value}."
        return True, ""

    @staticmethod
    def check_cell_integer(cell: Any, min_value: int = 0) -> Tuple[bool, str]:
        """
        Validate if a generic cell content contains a valid integer.

        Combines numerical parsing and integer validation.

        Args:
            cell (Any): Value to check (string, number, etc.).
            min_value (int, optional): Minimum allowed value. Default is 0.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - True and an empty string if valid.
                - False and an error message if invalid.
        """
        if NumberFormattingProcessing.is_nan(cell):
            return False, f"O valor '{cell}' não é um número."

        ok, num = NumberFormattingProcessing.parse_numeric(cell)
        if not ok:
            return False, f"O valor '{cell}' não é um número."

        valid, msg = NumberFormattingProcessing.validate_integer(num, min_value)
        if not valid:
            return False, msg

        return True, ""
