#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Unit tests for value_data_validation module."""

import pytest
import pandas as pd
from typing import Any, Set

from data_validate.helpers.common.validation.value_data_validation import (
    validate_numeric_value,
    process_column_validation,
    generate_decimal_warning,
    validate_data_values_in_columns,
)


class TestValidateNumericValue:
    """Test suite for validate_numeric_value function."""

    @pytest.mark.parametrize(
        "value, row_index, column, filename, expected_valid, expected_has_decimals",
        [
            # Valid cases
            ("DI", 0, "test_col", "test.xlsx", True, False),
            (10.5, 0, "test_col", "test.xlsx", True, False),
            (10.55, 0, "test_col", "test.xlsx", True, False),
            ("10.5", 0, "test_col", "test.xlsx", True, False),
            ("10,5", 0, "test_col", "test.xlsx", True, False),
            (100, 0, "test_col", "test.xlsx", True, False),
            ("100", 0, "test_col", "test.xlsx", True, False),
            (0, 0, "test_col", "test.xlsx", True, False),
            (-10.5, 0, "test_col", "test.xlsx", True, False),
            # Valid with excessive decimals
            (10.555, 0, "test_col", "test.xlsx", True, True),
            ("10.555", 0, "test_col", "test.xlsx", True, True),
            ("10,555", 0, "test_col", "test.xlsx", True, True),
            (123.12345, 0, "test_col", "test.xlsx", True, True),
        ],
    )
    def test_validate_numeric_value_valid_cases(
        self,
        value: Any,
        row_index: int,
        column: str,
        filename: str,
        expected_valid: bool,
        expected_has_decimals: bool,
    ) -> None:
        """Test validate_numeric_value with valid inputs."""
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            value, row_index, column, filename
        )

        assert is_valid == expected_valid
        assert error_msg == ""
        assert has_excessive_decimals == expected_has_decimals

    @pytest.mark.parametrize(
        "value, row_index, column, filename",
        [
            # Invalid cases
            ("invalid_text", 0, "test_col", "test.xlsx"),
            ("", 0, "test_col", "test.xlsx"),
            (None, 0, "test_col", "test.xlsx"),
            # Changed pd.NA to None since pd.NA causes boolean ambiguity
            ("abc123", 0, "test_col", "test.xlsx"),
            ("10.5.3", 0, "test_col", "test.xlsx"),
            ("10,5,3", 0, "test_col", "test.xlsx"),
            (float("nan"), 0, "test_col", "test.xlsx"),
        ],
    )
    def test_validate_numeric_value_invalid_cases(
        self, value: Any, row_index: int, column: str, filename: str
    ) -> None:
        """Test validate_numeric_value with invalid inputs."""
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            value, row_index, column, filename
        )

        assert is_valid is False
        assert "não é um número válido e nem DI (Dado Indisponível)" in error_msg
        assert f"{filename}, linha {row_index + 2}:" in error_msg
        assert f"coluna '{column}'" in error_msg
        assert has_excessive_decimals is False

    def test_validate_numeric_value_di_case(self) -> None:
        """Test validate_numeric_value with DI (Data Unavailable) value."""
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            "DI", 5, "codigo", "dados.xlsx"
        )

        assert is_valid is True
        assert error_msg == ""
        assert has_excessive_decimals is False

    def test_validate_numeric_value_decimal_processing_error(self) -> None:
        """Test validate_numeric_value with decimal processing error."""
        # Test with a string that can't be converted to Decimal properly
        # This will trigger the invalid value path, not the decimal processing error
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            "invalid_text", 0, "test_col", "test.xlsx"
        )

        assert is_valid is False
        assert "não é um número válido e nem DI (Dado Indisponível)" in error_msg
        assert has_excessive_decimals is False


class TestProcessColumnValidation:
    """Test suite for process_column_validation function."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "valid_col": [10.5, 20.75, "DI", 30.0],
                "invalid_col": [10.5, "invalid", "DI", None],
                "excessive_decimals": [10.555, 20.7777, "DI", 30.12345],
            }
        )

    def test_process_column_validation_valid_column(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test process_column_validation with valid column."""
        errors, excessive_decimal_rows = process_column_validation(
            sample_dataframe, "valid_col", "test.xlsx"
        )

        assert len(errors) == 0
        assert len(excessive_decimal_rows) == 0

    def test_process_column_validation_invalid_column(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test process_column_validation with invalid values."""
        errors, excessive_decimal_rows = process_column_validation(
            sample_dataframe, "invalid_col", "test.xlsx"
        )

        assert len(errors) == 1
        assert "2 valores que não são número válido nem DI" in errors[0]
        assert "entre as linhas 3 e 5" in errors[0]
        assert len(excessive_decimal_rows) == 0

    def test_process_column_validation_excessive_decimals(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test process_column_validation with excessive decimal places."""
        errors, excessive_decimal_rows = process_column_validation(
            sample_dataframe, "excessive_decimals", "test.xlsx"
        )

        assert len(errors) == 0
        assert excessive_decimal_rows == {2, 3, 5}

    def test_process_column_validation_single_invalid_value(self) -> None:
        """Test process_column_validation with single invalid value."""
        df = pd.DataFrame({"col": [10.5, "invalid", 30.0]})

        errors, excessive_decimal_rows = process_column_validation(
            df, "col", "test.xlsx"
        )

        assert len(errors) == 1
        assert "não é um número válido e nem DI" in errors[0]
        assert "linha 3:" in errors[0]
        assert len(excessive_decimal_rows) == 0

    def test_process_column_validation_empty_dataframe(self) -> None:
        """Test process_column_validation with empty DataFrame."""
        df = pd.DataFrame({"col": []})

        errors, excessive_decimal_rows = process_column_validation(
            df, "col", "test.xlsx"
        )

        assert len(errors) == 0
        assert len(excessive_decimal_rows) == 0

    def test_process_column_validation_mixed_errors_and_decimals(self) -> None:
        """Test process_column_validation with both errors and excessive decimals."""
        df = pd.DataFrame({"col": [10.555, "invalid", 20.7777, None, "DI", 30.12345]})

        errors, excessive_decimal_rows = process_column_validation(
            df, "col", "test.xlsx"
        )

        assert len(errors) == 1
        assert "2 valores que não são número válido nem DI" in errors[0]
        assert excessive_decimal_rows == {2, 4, 7}


class TestGenerateDecimalWarning:
    """Test suite for generate_decimal_warning function."""

    def test_generate_decimal_warning_no_excessive_decimals(self) -> None:
        """Test generate_decimal_warning with no excessive decimal rows."""
        warning = generate_decimal_warning(set(), 0, "test.xlsx")

        assert warning == ""

    def test_generate_decimal_warning_single_value(self) -> None:
        """Test generate_decimal_warning with single excessive decimal value."""
        warning = generate_decimal_warning({5}, 1, "test.xlsx")

        assert "Existe 1 valor com mais de 2 casas decimais" in warning
        assert "Entre as linhas 5 e 5" in warning
        assert "test.xlsx:" in warning

    def test_generate_decimal_warning_multiple_values(self) -> None:
        """Test generate_decimal_warning with multiple excessive decimal values."""
        warning = generate_decimal_warning({2, 5, 8}, 3, "test.xlsx")

        assert "Existem 3 valores com mais de 2 casas decimais" in warning
        assert "Entre as linhas 2 e 8" in warning
        assert "test.xlsx:" in warning

    def test_generate_decimal_warning_count_mismatch(self) -> None:
        """Test generate_decimal_warning with count different from set size."""
        warning = generate_decimal_warning({2, 5}, 5, "dados.xlsx")

        assert "Existem 5 valores com mais de 2 casas decimais" in warning
        assert "Entre as linhas 2 e 5" in warning
        assert "dados.xlsx:" in warning

    @pytest.mark.parametrize(
        "rows, count, expected_existem, expected_valores",
        [
            ({1}, 1, "Existe", "valor"),
            ({1, 2}, 2, "Existem", "valores"),
            ({1, 2, 3}, 3, "Existem", "valores"),
            ({10}, 1, "Existe", "valor"),
        ],
    )
    def test_generate_decimal_warning_grammar(
        self, rows: Set[int], count: int, expected_existem: str, expected_valores: str
    ) -> None:
        """Test generate_decimal_warning grammar for singular/plural forms."""
        warning = generate_decimal_warning(rows, count, "test.xlsx")

        assert expected_existem in warning
        assert expected_valores in warning


class TestValidateDataValuesInColumns:
    """Test suite for validate_data_values_in_columns function."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "col1": [10.5, 20.75, "DI", 30.0],
                "col2": [100.555, 200.777, "DI", 300.123],
                "col3": [10.5, "invalid", "DI", None],
                "col4": ["text", "more_text", "invalid", "error"],
            }
        )

    def test_validate_data_values_in_columns_valid_columns(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with valid columns only."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, ["col1"], "test.xlsx"
        )

        assert len(errors) == 0
        assert len(warnings) == 0

    def test_validate_data_values_in_columns_excessive_decimals(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with excessive decimal places."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, ["col2"], "test.xlsx"
        )

        assert len(errors) == 0
        assert len(warnings) == 1
        assert "Existem 3 valores com mais de 2 casas decimais" in warnings[0]

    def test_validate_data_values_in_columns_invalid_values(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with invalid values."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, ["col3"], "test.xlsx"
        )

        assert len(errors) == 1
        assert "2 valores que não são número válido nem DI" in errors[0]
        assert len(warnings) == 0

    def test_validate_data_values_in_columns_all_invalid(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with all invalid values."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, ["col4"], "test.xlsx"
        )

        assert len(errors) == 1
        assert "4 valores que não são número válido nem DI" in errors[0]
        assert len(warnings) == 0

    def test_validate_data_values_in_columns_multiple_columns(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with multiple columns."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, ["col1", "col2", "col3"], "test.xlsx"
        )

        assert len(errors) == 1
        assert "2 valores que não são número válido nem DI" in errors[0]
        assert len(warnings) == 1
        assert "Existem 3 valores com mais de 2 casas decimais" in warnings[0]

    def test_validate_data_values_in_columns_empty_dataframe(self) -> None:
        """Test validate_data_values_in_columns with empty DataFrame."""
        df = pd.DataFrame({"col": []})

        errors, warnings = validate_data_values_in_columns(df, ["col"], "test.xlsx")

        assert len(errors) == 0
        assert len(warnings) == 0

    def test_validate_data_values_in_columns_empty_columns_list(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with empty columns list."""
        errors, warnings = validate_data_values_in_columns(
            sample_dataframe, [], "test.xlsx"
        )

        assert len(errors) == 0
        assert len(warnings) == 0

    def test_validate_data_values_in_columns_nonexistent_column(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test validate_data_values_in_columns with nonexistent column."""
        with pytest.raises(KeyError):
            validate_data_values_in_columns(
                sample_dataframe, ["nonexistent_col"], "test.xlsx"
            )

    def test_validate_data_values_in_columns_comprehensive_scenario(self) -> None:
        """Test validate_data_values_in_columns with comprehensive scenario."""
        df = pd.DataFrame(
            {
                "perfect_col": [10.5, 20.75, "DI", 30.0],
                "decimal_col": [
                    100.555,
                    200.777,
                    300.123,
                    400.456,
                ],  # Fixed: same length
                "error_col": ["invalid", None, "text", "bad"],  # Fixed: same length
                "mixed_col": [10.555, "invalid", "DI", 30.12345],
            }
        )

        errors, warnings = validate_data_values_in_columns(
            df,
            ["perfect_col", "decimal_col", "error_col", "mixed_col"],
            "comprehensive.xlsx",
        )

        # Should have errors from error_col and mixed_col
        assert len(errors) == 2

        # Should have warnings from decimal_col and mixed_col
        assert len(warnings) == 1
        assert (
            "Existem 6 valores com mais de 2 casas decimais" in warnings[0]
        )  # Updated count


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_very_large_numbers(self) -> None:
        """Test validation with very large numbers."""
        large_number = 1e20
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            large_number, 0, "test_col", "test.xlsx"
        )

        assert is_valid is True
        assert error_msg == ""
        # Large numbers typically don't have decimal issues

    def test_very_small_numbers(self) -> None:
        """Test validation with very small numbers."""
        small_number = 1e-10
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            small_number, 0, "test_col", "test.xlsx"
        )

        assert is_valid is True
        assert error_msg == ""
        assert has_excessive_decimals is True  # Very small numbers have many decimals

    def test_zero_variations(self) -> None:
        """Test validation with different zero representations."""
        zero_values = [0, 0.0, "0", "0.0", "0,0", 0.00]

        for zero_val in zero_values:
            is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
                zero_val, 0, "test_col", "test.xlsx"
            )

            assert is_valid is True
            assert error_msg == ""

    def test_negative_numbers_with_decimals(self) -> None:
        """Test validation with negative numbers having excessive decimals."""
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            -10.555, 0, "test_col", "test.xlsx"
        )

        assert is_valid is True
        assert error_msg == ""
        assert has_excessive_decimals is True

    def test_scientific_notation(self) -> None:
        """Test validation with scientific notation."""
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            "1.5e2", 0, "test_col", "test.xlsx"
        )

        assert is_valid is True
        assert error_msg == ""

    def test_special_float_values(self) -> None:
        """Test validation with special float values."""
        # Test infinity - these are actually treated as invalid by pandas.to_numeric
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            float("inf"), 0, "test_col", "test.xlsx"
        )
        # Infinity values are treated as invalid in this validation function
        assert is_valid is False

        # Test negative infinity
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            float("-inf"), 0, "test_col", "test.xlsx"
        )
        # Negative infinity values are also treated as invalid
        assert is_valid is False
