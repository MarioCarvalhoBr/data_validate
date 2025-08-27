import pandas as pd
import math
from typing import Tuple, Any
from babel.numbers import format_decimal


def format_number_brazilian(n):
    """Formata um número no padrão brasileiro."""
    return format_decimal(n, locale='pt_BR')

def is_nan(value: Any) -> bool:
    """Check if a value is NaN (including pandas NaN)."""
    try:
        return pd.isna(value) or math.isnan(float(value))
    except Exception:
        return False


def parse_numeric(cell: Any) -> Tuple[bool, float]:
    """Try to parse a cell to float, handling comma as decimal separator."""
    if isinstance(cell, str):
        cell = cell.replace(',', '.')
    try:
        return True, float(cell)
    except (ValueError, TypeError):
        return False, 0.0


def validate_integer(value: float, min_value: int = 0) -> Tuple[bool, str]:
    """Validate that a float is an integer >= min_value."""
    if not value.is_integer():
        return False, f"O valor '{value}' não é um número inteiro."
    if int(value) < min_value:
        return False, f"O valor '{int(value)}' é menor que {min_value}."
    return True, ""


def check_cell_integer(cell: Any, min_value: int = 0) -> Tuple[bool, str]:
    """Full validation: NaN, numeric parsing, integer and range check."""
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
    """Check if a cell is a valid float."""
    if is_nan(cell):
        return False, f"O valor '{cell}' não é um número."

    ok, num = parse_numeric(cell)
    if not ok:
        return False, f"O valor '{cell}' não é um número."

    return True, ""