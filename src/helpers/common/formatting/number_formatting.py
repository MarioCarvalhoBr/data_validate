import pandas as pd
import math
from typing import Tuple, Any
from babel.numbers import format_decimal


# def truncate_number(x, precision):
def truncate_number(x, precision):
    """Trunca o valor 'x' à precisão especificada sem arredondamento."""
    # Se não tiver casas decimais, retorna o valor original
    if x == int(x):
        return x
    factor = 10**precision
    return math.trunc(x * factor) / factor


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
    except Exception:
        return False


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


def check_cell_integer(cell: Any, min_value: int = 0) -> Tuple[bool, str]:
    """
    Validate if a cell contains a valid integer greater than or equal to min_value.

    Args:
        cell (Any): Value to check.
        min_value (int): Minimum allowed value. Default is 0.
    Returns:
        Tuple[bool, str]: (True, "") if valid, (False, error message) otherwise.
    """
    if is_nan(cell):
        return False, f"O valor '{cell}' não é um número."

    ok, num = parse_numeric(cell)
    if not ok:
        return False, f"O valor '{cell}' não é um número."

    valid, msg = validate_integer(num, min_value)
    if not valid:
        return False, msg

    return True, ""


def check_cell_float(cell: Any, min_value: int = 0) -> Tuple[bool, str]:
    """
    Validate if a cell contains a valid float greater than or equal to min_value.

    Args:
        cell (Any): Value to check.
        min_value (int): Minimum allowed value. Default is 0.
    Returns:
        Tuple[bool, str]: (True, "") if valid, (False, error message) otherwise.
    """
    if is_nan(cell):
        return False, f"O valor '{cell}' não é um número."

    ok, num = parse_numeric(cell)
    if not ok:
        return False, f"O valor '{cell}' não é um número."

    # Check minimum value constraint
    if num < min_value:
        return (
            False,
            f"O valor '{num}' é menor que o valor mínimo permitido ({min_value}).",
        )

    return True, ""
