import math

import pandas as pd

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class TestNumberFormatting:
    """Test cases for number formatting functions."""

    def test_format_number_brazilian(self):
        """Test Brazilian number formatting."""
        # Test positive number
        result = NumberFormattingProcessing.format_number_brazilian(1234.56)
        assert result == "1.234,56"

        # Test negative number
        result = NumberFormattingProcessing.format_number_brazilian(-1234.56)
        assert result == "-1.234,56"

        # Test zero
        result = NumberFormattingProcessing.format_number_brazilian(0)
        assert result == "0"

        # Test integer
        result = NumberFormattingProcessing.format_number_brazilian(1000)
        assert result == "1.000"

    def test_is_nan(self):
        """Test NaN detection function."""
        # Test pandas NaN
        assert NumberFormattingProcessing.is_nan(pd.NA) is True
        assert NumberFormattingProcessing.is_nan(pd.NaT) is True

        # Test math NaN
        assert NumberFormattingProcessing.is_nan(float("nan")) is True
        assert NumberFormattingProcessing.is_nan(math.nan) is True

        # Test non-NaN values
        assert NumberFormattingProcessing.is_nan(0) is False
        assert NumberFormattingProcessing.is_nan(1.5) is False
        assert NumberFormattingProcessing.is_nan("string") is False
        assert NumberFormattingProcessing.is_nan("") is False
        assert NumberFormattingProcessing.is_nan(None) is True  # pd.isna(None) returns True

        # Test exception handling (invalid float conversion)
        assert NumberFormattingProcessing.is_nan("not_a_number") is False

    def test_parse_numeric(self):
        """Test numeric parsing function."""
        # Test valid numbers
        success, value = NumberFormattingProcessing.parse_numeric(123.45)
        assert success is True
        assert value == 123.45

        success, value = NumberFormattingProcessing.parse_numeric("123.45")
        assert success is True
        assert value == 123.45

        # Test comma as decimal separator
        success, value = NumberFormattingProcessing.parse_numeric("123,45")
        assert success is True
        assert value == 123.45

        # Test integers
        success, value = NumberFormattingProcessing.parse_numeric(100)
        assert success is True
        assert value == 100.0

        # Test invalid values
        success, value = NumberFormattingProcessing.parse_numeric("invalid")
        assert success is False
        assert value == 0.0

        success, value = NumberFormattingProcessing.parse_numeric(None)
        assert success is False
        assert value == 0.0

    def test_validate_integer(self):
        """Test integer validation function."""
        # Test valid integers
        valid, msg = NumberFormattingProcessing.validate_integer(5.0)
        assert valid is True
        assert msg == ""

        valid, msg = NumberFormattingProcessing.validate_integer(0.0)
        assert valid is True
        assert msg == ""

        # Test non-integers
        valid, msg = NumberFormattingProcessing.validate_integer(5.5)
        assert valid is False
        assert "não é um número inteiro" in msg

        # Test below minimum value
        valid, msg = NumberFormattingProcessing.validate_integer(3.0, min_value=5)
        assert valid is False
        assert "é menor que 5" in msg

        # Test custom minimum value
        valid, msg = NumberFormattingProcessing.validate_integer(10.0, min_value=5)
        assert valid is True
        assert msg == ""

    def test_check_cell_integer(self):
        """Test cell integer validation function."""
        # Test valid integers
        valid, msg = NumberFormattingProcessing.check_cell_integer(5)
        assert valid is True
        assert msg == ""

        valid, msg = NumberFormattingProcessing.check_cell_integer("5")
        assert valid is True
        assert msg == ""

        valid, msg = NumberFormattingProcessing.check_cell_integer("5,0")
        assert valid is True
        assert msg == ""

        # Test NaN values
        valid, msg = NumberFormattingProcessing.check_cell_integer(pd.NA)
        assert valid is False
        assert "não é um número" in msg

        # Test invalid numbers
        valid, msg = NumberFormattingProcessing.check_cell_integer("invalid")
        assert valid is False
        assert "não é um número" in msg

        # Test non-integers
        valid, msg = NumberFormattingProcessing.check_cell_integer(5.5)
        assert valid is False
        assert "não é um número inteiro" in msg

        # Test below minimum
        valid, msg = NumberFormattingProcessing.check_cell_integer(3, min_value=5)
        assert valid is False
        assert "é menor que 5" in msg
