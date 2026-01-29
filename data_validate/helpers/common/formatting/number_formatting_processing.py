import math
from decimal import Decimal, InvalidOperation
from typing import Tuple, Any

import pandas as pd
from babel.numbers import format_decimal


class NumberFormattingProcessing:

    def __init__(self) -> None:
        pass

    @staticmethod
    def to_decimal_truncated(value_number: Any, value_to_ignore: Any, precision: int) -> Decimal:
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
        if pd.isna(value_number) or value_number == value_to_ignore:
            return False
        decimal_value = Decimal(str(value_number).replace(",", "."))
        return decimal_value.as_tuple().exponent < -number_decimal_places

    @staticmethod
    def check_two_decimals_places(value: Any) -> bool:
        if value in [float("-inf"), float("inf")] or pd.isna(value):
            return False
        return NumberFormattingProcessing.check_n_decimals_places(value, 0, 2)

    @staticmethod
    def format_number_brazilian(n: float, locale: str = "pt_BR") -> str:
        """
        Format a number using Brazilian locale.

        Args:
            n (float): Number to format.
            locale (str): Locale string. Default is "pt_BR".
        Returns:
            str: Formatted number string.
        """
        return format_decimal(number=n, locale=locale)

    @staticmethod
    def is_nan(value: Any) -> bool:
        """
        Check if a value is NaN (including pandas NaN).

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
        Try to parse a cell to float, handling comma as decimal separator.

        Args:
            cell (Any): Value to parse.
        Returns:
            Tuple[bool, float]: (True, float value) if successful, (False, 0.0) otherwise.
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
        Validate that a float is an integer greater than or equal to min_value.

        Args:
            value (float): Value to validate.
            min_value (int): Minimum allowed value. Default is 0.
        Returns:
            Tuple[bool, str]: (True, "") if valid, (False, error message) otherwise.
        """
        if not value.is_integer():
            return False, f"O valor '{value}' não é um número inteiro."
        if int(value) < min_value:
            return False, f"O valor '{int(value)}' é menor que {min_value}."
        return True, ""

    @staticmethod
    def check_cell_integer(cell: Any, min_value: int = 0) -> Tuple[bool, str]:
        """
        Validate if a cell contains a valid integer greater than or equal to min_value.

        Args:
            cell (Any): Value to check.
            min_value (int): Minimum allowed value. Default is 0.
        Returns:
            Tuple[bool, str]: (True, "") if valid, (False, error message) otherwise.
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
