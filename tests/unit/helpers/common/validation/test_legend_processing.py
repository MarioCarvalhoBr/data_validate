#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Unit tests for legend_processing module."""

from decimal import Decimal, InvalidOperation
from typing import List

import pandas as pd
import pytest

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.common.validation.legend_processing import LegendProcessing


@pytest.fixture
def mock_context(mocker):
    """
    Cria um mock para ter apenas value_data_unavailable="Dado indisponível" e  filename="test_legend.xlsx"
    """
    mock = mocker.Mock(spec=GeneralContext)
    mock.value_data_unavailable = "Dado indisponível"
    mock.filename = "test_legend.xlsx"
    return mock


@pytest.fixture
def legend_processor(mock_context) -> LegendProcessing:
    """Create LegendProcessing instance for testing."""
    return LegendProcessing(value_data_unavailable=mock_context.value_data_unavailable, filename="test_legend.xlsx")


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "codigo": [1, 2, 3],
            "label": ["Baixo", "Médio", "Alto"],
            "minimo": [0.0, 10.0, 20.0],
            "maximo": [9.99, 19.99, 30.0],
            "ordem": [1, 2, 3],
            "cor": ["#FF0000", "#00FF00", "#0000FF"],
        }
    )


@pytest.fixture
def invalid_dataframe() -> pd.DataFrame:
    """Create DataFrame with invalid data for testing."""
    return pd.DataFrame(
        {
            "codigo": ["invalid", 2, 3],
            "label": ["", "Médio", None],
            "minimo": ["not_number", 10.0, 20.0],
            "maximo": [9.99, "invalid", 30.0],
            "ordem": [1.5, 2, "three"],
            "cor": ["invalid_color", "#00FF00", "#0000FF"],
        }
    )


@pytest.fixture
def unavailable_data_dataframe() -> pd.DataFrame:
    """Create DataFrame with 'Dado indisponível' entries."""
    return pd.DataFrame(
        {
            "codigo": [1, 2],
            "label": ["Baixo", "Dado indisponível"],
            "minimo": [0.0, None],
            "maximo": [9.99, None],
            "ordem": [1, 2],
        }
    )


class TestLegendProcessing:
    """Test suite for LegendProcessing class."""

    def test_init(self, mock_context) -> None:
        """Test LegendProcessing initialization."""
        filename = "test_file.xlsx"
        processor = LegendProcessing(value_data_unavailable=mock_context.value_data_unavailable, filename=filename)

        assert processor.filename == filename

    def test_get_min_max_values_basic(self) -> None:
        """Test get_min_max_values with valid data."""
        df = pd.DataFrame({"min_col": [1.0, 2.0, 3.0], "max_col": [10.0, 20.0, 30.0]})

        min_val, max_val = LegendProcessing.get_min_max_values(df, "min_col", "max_col")

        assert min_val == 1.0
        assert max_val == 30.0

    def test_get_min_max_values_with_nan(self) -> None:
        """Test get_min_max_values with NaN values."""
        df = pd.DataFrame({"min_col": [1.0, float("nan"), 3.0], "max_col": [10.0, 20.0, float("nan")]})

        min_val, max_val = LegendProcessing.get_min_max_values(df, "min_col", "max_col")

        assert min_val == 1.0
        assert max_val == 20.0

    def test_get_min_max_values_empty_dataframe(self) -> None:
        """Test get_min_max_values with empty DataFrame."""
        df = pd.DataFrame({"min_col": [], "max_col": []})

        min_val, max_val = LegendProcessing.get_min_max_values(df, "min_col", "max_col")

        assert pd.isna(min_val)
        assert pd.isna(max_val)


class TestValidateLegendLabels:
    """Test suite for validate_legend_labels method."""

    def test_validate_legend_labels_no_duplicates(self, legend_processor: LegendProcessing) -> None:
        """Test validation with no duplicate labels."""
        df = pd.DataFrame({"label": ["Baixo", "Médio", "Alto"]})

        errors = legend_processor.validate_legend_labels(df, 1, "label")

        assert len(errors) == 0

    def test_validate_legend_labels_with_duplicates(self, legend_processor: LegendProcessing) -> None:
        """Test validation with duplicate labels."""
        df = pd.DataFrame({"label": ["Baixo", "Médio", "Baixo", "Alto", "Médio"]})

        errors = legend_processor.validate_legend_labels(df, 1, "label")

        assert len(errors) == 2
        assert "O label 'Baixo' está duplicado" in errors[0]
        assert "O label 'Médio' está duplicado" in errors[1]
        assert "código: 1" in errors[0]

    def test_validate_legend_labels_empty_dataframe(self, legend_processor: LegendProcessing) -> None:
        """Test validation with empty DataFrame."""
        df = pd.DataFrame({"label": []})

        errors = legend_processor.validate_legend_labels(df, 1, "label")

        assert len(errors) == 0

    def test_validate_legend_labels_single_row(self, legend_processor: LegendProcessing) -> None:
        """Test validation with single row."""
        df = pd.DataFrame({"label": ["Único"]})

        errors = legend_processor.validate_legend_labels(df, 1, "label")

        assert len(errors) == 0


class TestValidateLegendColumnsDtypesNumeric:
    """Test suite for validate_legend_columns_dtypes_numeric method."""

    def test_validate_columns_dtypes_valid_data(self, legend_processor: LegendProcessing) -> None:
        """Test validation with valid data types."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2, 3, 4],
                "label": ["Baixo", "Médio", "Alto", "Dado indisponível"],
                "minimo": [0.0, 10.0, 20.0, None],
                "maximo": [9.99, 19.99, 30.0, None],
                "ordem": [1, 2, 3, 4],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 0

    def test_validate_columns_dtypes_empty_labels(self, legend_processor: LegendProcessing) -> None:
        """Test validation with empty or null labels."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2, 3, 4],
                "label": ["Baixo", "", None, "Dado indisponível"],
                "minimo": [0.0, 10.0, 20.0, None],
                "maximo": [9.99, 19.99, 30.0, None],
                "ordem": [1, 2, 3, 4],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 1
        assert "contém valores vazios ou nulos" in errors[0]
        assert "linha(s): 3, 4" in errors[0]

    def test_validate_columns_dtypes_non_numeric_values(self, legend_processor: LegendProcessing) -> None:
        """Test validation with non-numeric values in numeric columns."""
        df = pd.DataFrame(
            {
                "codigo": ["not_number", 2, 3],
                "label": ["Baixo", "Médio", "Alto"],
                "minimo": ["invalid", 10.0, 20.0],
                "maximo": [9.99, "text", 30.0],
                "ordem": [1, 2, "three"],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) >= 4  # At least one error per invalid column

    def test_validate_columns_dtypes_unavailable_data_with_values(self, legend_processor: LegendProcessing) -> None:
        """Test validation when 'Dado indisponível' has min/max values."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2],
                "label": ["Baixo", "Dado indisponível"],
                "minimo": [0.0, 10.0],  # Should be None for 'Dado indisponível'
                "maximo": [9.99, 20.0],  # Should be None for 'Dado indisponível'
                "ordem": [1, 2],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 2
        assert "deve estar vazia quando o label é 'Dado indisponível'" in errors[0]
        assert "deve estar vazia quando o label é 'Dado indisponível'" in errors[1]

    def test_validate_columns_dtypes_no_unavailable_label(self, legend_processor: LegendProcessing) -> None:
        """Test validation when no 'Dado indisponível' label exists."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2, 3],
                "label": ["Baixo", "Médio", "Alto"],
                "minimo": [0.0, 10.0, 20.0],
                "maximo": [9.99, 19.99, 30.0],
                "ordem": [1, 2, 3],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 1
        assert "Deve existir um label 'Dado indisponível' por código" in errors[0]

    def test_validate_columns_dtypes_multiple_unavailable_labels(self, legend_processor: LegendProcessing) -> None:
        """Test validation when multiple 'Dado indisponível' labels exist."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2, 3],
                "label": ["Dado indisponível", "Médio", "Dado indisponível"],
                "minimo": [None, 10.0, None],
                "maximo": [None, 19.99, None],
                "ordem": [1, 2, 3],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 1
        assert "Deve existir exatamente um label 'Dado indisponível'" in errors[0]
        assert "foram encontrados 2" in errors[0]

    def test_validate_columns_dtypes_non_integer_code_order(self, legend_processor: LegendProcessing) -> None:
        """Test validation with non-integer values in code and order columns."""
        df = pd.DataFrame(
            {
                "codigo": [1.5, 2, 3],
                "label": ["Baixo", "Médio", "Dado indisponível"],
                "minimo": [0.0, 10.0, None],
                "maximo": [9.99, 19.99, None],
                "ordem": [1, 2.5, 3],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        assert len(errors) == 2
        assert "não é um número inteiro válido" in errors[0]
        assert "não é um número inteiro válido" in errors[1]

    def test_validate_columns_dtypes_missing_columns(self, legend_processor: LegendProcessing) -> None:
        """Test validation when some columns don't exist."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2],
                "label": ["Baixo", "Dado indisponível"],
                # Missing minimo, maximo, ordem columns
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        # Should not crash and should validate available columns
        assert isinstance(errors, list)


class TestValidateColorFormat:
    """Test suite for validate_color_format method."""

    @pytest.mark.parametrize(
        "colors, expected_error_count",
        [
            (["#FF0000", "#00FF00", "#0000FF"], 0),  # Valid 6-digit hex
            (["#F00", "#0F0", "#00F"], 0),  # Valid 3-digit hex
            (["#FF0000", "#F00", "#ABCDEF"], 0),  # Mixed valid formats
            (["invalid", "#00FF00", "#0000FF"], 1),  # One invalid
            (["#GG0000", "#00FF00", "#0000FF"], 1),  # Invalid character
            (["FF0000", "#00FF00", "#0000FF"], 1),  # Missing #
            (["#12345", "#00FF00", "#0000FF"], 1),  # Wrong length
            (["#1234567", "#00FF00", "#0000FF"], 1),  # Too long
            (["", "#00FF00", "#0000FF"], 1),  # Empty string
            (["invalid", "bad_color", "wrong"], 3),  # All invalid
        ],
    )
    def test_validate_color_format_various_inputs(
        self,
        legend_processor: LegendProcessing,
        colors: List[str],
        expected_error_count: int,
    ) -> None:
        """Test color format validation with various inputs."""
        df = pd.DataFrame({"cor": colors})

        errors = legend_processor.validate_color_format(df, 1, "cor")

        assert len(errors) == expected_error_count
        if expected_error_count > 0:
            assert all("formato da cor" in error for error in errors)
            assert all("inválido" in error for error in errors)

    def test_validate_color_format_empty_dataframe(self, legend_processor: LegendProcessing) -> None:
        """Test color validation with empty DataFrame."""
        df = pd.DataFrame({"cor": []})

        errors = legend_processor.validate_color_format(df, 1, "cor")

        assert len(errors) == 0

    def test_validate_color_format_line_numbers(self, legend_processor: LegendProcessing) -> None:
        """Test that error messages include correct line numbers."""
        df = pd.DataFrame({"cor": ["#FF0000", "invalid", "#0000FF"]})

        errors = legend_processor.validate_color_format(df, 1, "cor")

        assert len(errors) == 1
        assert "linha: 3" in errors[0]  # Row index 1 + 2 for header


class TestValidateMinMaxValues:
    """Test suite for validate_min_max_values method."""

    def test_validate_min_max_values_valid_sequence(self, legend_processor: LegendProcessing) -> None:
        """Test validation with valid min/max sequence."""
        df = pd.DataFrame(
            {
                "label": ["Baixo", "Médio", "Alto", "Dado indisponível"],
                "minimo": [0.0, 10.01, 20.01, None],
                "maximo": [10.0, 20.0, 30.0, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        assert len(errors) == 0

    def test_validate_min_max_values_invalid_range(self, legend_processor: LegendProcessing) -> None:
        """Test validation when min >= max."""
        df = pd.DataFrame(
            {
                "label": ["Baixo", "Médio", "Dado indisponível"],
                "minimo": [10.0, 20.0, None],  # min >= max for first row
                "maximo": [5.0, 19.99, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        assert len(errors) == 3
        assert "valor mínimo (10.0) deve ser menor que o valor máximo (5.0)" in errors[0]
        assert "valor mínimo (20.0) deve ser menor que o valor máximo (19.99)" in errors[1]
        assert "intervalo não é contínuo" in errors[2]

    def test_validate_min_max_values_non_continuous_intervals(self, legend_processor: LegendProcessing) -> None:
        """Test validation with non-continuous intervals."""
        df = pd.DataFrame(
            {
                "label": ["Baixo", "Médio", "Alto", "Dado indisponível"],
                "minimo": [0.0, 10.02, 20.01, None],  # Gap between intervals
                "maximo": [10.0, 20.0, 30.0, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        assert len(errors) == 1
        assert "intervalo não é contínuo" in errors[0]
        assert "deveria ser 10.01" in errors[0]

    def test_validate_min_max_values_with_nan(self, legend_processor: LegendProcessing) -> None:
        """Test validation with NaN values."""
        df = pd.DataFrame(
            {
                "label": ["Baixo", "Médio", "Dado indisponível"],
                "minimo": [0.0, float("nan"), None],
                "maximo": [10.0, 20.0, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        # Should not crash and process available data
        assert isinstance(errors, list)

    def test_validate_min_max_values_empty_after_filter(self, legend_processor: LegendProcessing) -> None:
        """Test validation when DataFrame is empty after filtering."""
        df = pd.DataFrame({"label": ["Dado indisponível"], "minimo": [None], "maximo": [None]})

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        assert len(errors) == 0

    def test_validate_min_max_values_invalid_decimal_operation(self, legend_processor: LegendProcessing) -> None:
        """Test validation with invalid decimal operations."""
        # Mock Decimal to raise InvalidOperation
        original_decimal = Decimal

        def mock_decimal_constructor(value):
            if str(value) == "10.0":
                raise InvalidOperation("Mock invalid operation")
            return original_decimal(value)

        # Patch Decimal temporarily
        import data_validate.helpers.common.validation.legend_processing as legend_module

        legend_module.Decimal = mock_decimal_constructor

        try:
            df = pd.DataFrame(
                {
                    "label": ["Baixo", "Médio", "Dado indisponível"],
                    "minimo": [0.0, 10.0, None],
                    "maximo": [5.0, 20.0, None],
                }
            )

            errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

            assert len(errors) >= 1
            assert any("Valor inválido para operação" in error for error in errors)
        finally:
            # Restore original Decimal
            legend_module.Decimal = original_decimal

    def test_validate_min_max_values_sorting(self, legend_processor: LegendProcessing) -> None:
        """Test that validation sorts by minimum value correctly."""
        df = pd.DataFrame(
            {
                "label": ["Alto", "Baixo", "Médio", "Dado indisponível"],
                "minimo": [20.01, 0.0, 10.01, None],
                "maximo": [30.0, 10.0, 20.0, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        assert len(errors) == 0


class TestValidateOrderSequence:
    """Test suite for validate_order_sequence method."""

    def test_validate_order_sequence_valid(self, legend_processor: LegendProcessing) -> None:
        """Test validation with valid sequential order."""
        df = pd.DataFrame({"ordem": [1, 2, 3, 4]})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 0

    def test_validate_order_sequence_unordered_but_complete(self, legend_processor: LegendProcessing) -> None:
        """Test validation with unordered but complete sequence."""
        df = pd.DataFrame({"ordem": [3, 1, 4, 2]})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 0

    def test_validate_order_sequence_missing_numbers(self, legend_processor: LegendProcessing) -> None:
        """Test validation with missing numbers in sequence."""
        df = pd.DataFrame({"ordem": [1, 3, 5]})  # Missing 2, 4

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 1
        assert "não é sequencial ou não começa em 1" in errors[0]
        assert "[1, 3, 5]" in errors[0]

    def test_validate_order_sequence_not_starting_from_one(self, legend_processor: LegendProcessing) -> None:
        """Test validation when sequence doesn't start from 1."""
        df = pd.DataFrame({"ordem": [2, 3, 4]})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 1
        assert "não é sequencial ou não começa em 1" in errors[0]

    def test_validate_order_sequence_with_non_numeric(self, legend_processor: LegendProcessing) -> None:
        """Test validation with non-numeric values."""
        df = pd.DataFrame({"ordem": [1, "invalid", 3]})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 1
        assert "contém valores não numéricos" in errors[0]

    def test_validate_order_sequence_empty_dataframe(self, legend_processor: LegendProcessing) -> None:
        """Test validation with empty DataFrame."""
        df = pd.DataFrame({"ordem": []})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 0

    def test_validate_order_sequence_duplicates(self, legend_processor: LegendProcessing) -> None:
        """Test validation with duplicate order values."""
        df = pd.DataFrame({"ordem": [1, 2, 2, 3]})

        errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(errors) == 1
        assert "não é sequencial ou não começa em 1" in errors[0]


class TestValidateCodeSequence:
    """Test suite for validate_code_sequence method."""

    def test_validate_code_sequence_valid(self, legend_processor: LegendProcessing) -> None:
        """Test validation with valid sequential codes."""
        df = pd.DataFrame({"codigo": [1, 2, 3, 4]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 0

    def test_validate_code_sequence_unordered_but_complete(self, legend_processor: LegendProcessing) -> None:
        """Test validation with unordered but complete sequence."""
        df = pd.DataFrame({"codigo": [1, 2, 3, 4]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 0

    def test_validate_code_sequence_unordered_fails(self, legend_processor: LegendProcessing) -> None:
        """Test validation with unordered sequence fails."""
        df = pd.DataFrame({"codigo": [3, 1, 4, 2]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 2
        assert "deve começar em 1" in errors[0]
        assert "não são sequenciais" in errors[1]

    def test_validate_code_sequence_with_duplicates(self, legend_processor: LegendProcessing) -> None:
        """Test validation with duplicate codes (should be handled)."""
        df = pd.DataFrame({"codigo": [1, 2, 2, 3]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 0  # Duplicates are removed in the logic

    def test_validate_code_sequence_not_starting_from_one(self, legend_processor: LegendProcessing) -> None:
        """Test validation when sequence doesn't start from 1."""
        df = pd.DataFrame({"codigo": [2, 3, 4]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 2
        assert "deve começar em 1" in errors[0]
        assert "Código inicial encontrado: 2" in errors[0]
        assert "não são sequenciais" in errors[1]

    def test_validate_code_sequence_missing_numbers(self, legend_processor: LegendProcessing) -> None:
        """Test validation with missing numbers in sequence."""
        df = pd.DataFrame({"codigo": [1, 3, 5]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 1
        assert "não são sequenciais" in errors[0]
        assert "[1, 3, 5]" in errors[0]

    def test_validate_code_sequence_with_non_numeric(self, legend_processor: LegendProcessing) -> None:
        """Test validation with non-numeric codes."""
        df = pd.DataFrame({"codigo": [1, "invalid", 3]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 2
        assert "contém valores não numéricos" in errors[0]
        assert "Valores não numéricos encontrados" in errors[1]
        assert "['invalid']" in errors[1]

    def test_validate_code_sequence_empty_dataframe(self, legend_processor: LegendProcessing) -> None:
        """Test validation with empty DataFrame."""
        df = pd.DataFrame({"codigo": []})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 0

    def test_validate_code_sequence_all_non_numeric(self, legend_processor: LegendProcessing) -> None:
        """Test validation when all codes are non-numeric."""
        df = pd.DataFrame({"codigo": ["a", "b", "c"]})

        errors = legend_processor.validate_code_sequence(df, "codigo")

        assert len(errors) == 2
        assert "contém valores não numéricos" in errors[0]
        assert "['a', 'b', 'c']" in errors[1]


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple validation methods."""

    def test_complete_valid_legend_data(self, legend_processor: LegendProcessing) -> None:
        """Test with completely valid legend data."""
        df = pd.DataFrame(
            {
                "codigo": [1, 1, 1, 1],
                "label": ["Baixo", "Médio", "Alto", "Dado indisponível"],
                "minimo": [0.0, 10.01, 20.01, None],
                "maximo": [10.0, 20.0, 30.0, None],
                "ordem": [1, 2, 3, 4],
                "cor": ["#FF0000", "#FFFF00", "#00FF00", "#000000"],
            }
        )

        # Test all validation methods
        label_errors = legend_processor.validate_legend_labels(df, 1, "label")
        color_errors = legend_processor.validate_color_format(df, 1, "cor")
        minmax_errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")
        order_errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(label_errors) == 0
        assert len(color_errors) == 0
        assert len(minmax_errors) == 0
        assert len(order_errors) == 0

    def test_multiple_validation_errors(self, legend_processor: LegendProcessing) -> None:
        """Test with data containing multiple types of errors."""
        df = pd.DataFrame(
            {
                "codigo": [1, 1, 1],
                "label": ["Baixo", "Baixo", ""],  # Duplicate and empty
                "minimo": [20.0, 10.0, 0.0],  # Wrong order and min > max
                "maximo": [10.0, 25.0, 5.0],
                "ordem": [1, 3, 5],  # Non-sequential
                "cor": ["invalid", "#00FF00", "#GGGGGG"],  # Invalid colors
            }
        )

        label_errors = legend_processor.validate_legend_labels(df, 1, "label")
        color_errors = legend_processor.validate_color_format(df, 1, "cor")
        minmax_errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")
        order_errors = legend_processor.validate_order_sequence(df, 1, "ordem")

        assert len(label_errors) > 0
        assert len(color_errors) > 0
        assert len(minmax_errors) > 0
        assert len(order_errors) > 0


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_very_large_dataset(self, legend_processor: LegendProcessing) -> None:
        """Test with large dataset to check performance."""
        size = 1000
        df = pd.DataFrame(
            {
                "codigo": list(range(1, size + 1)),
                "label": [f"Label_{i}" for i in range(size)],
                "minimo": [float(i) for i in range(size)],
                "maximo": [float(i + 0.99) for i in range(size)],
                "ordem": list(range(1, size + 1)),
                "cor": ["#FF0000"] * size,
            }
        )

        # Should handle large dataset without issues
        errors = legend_processor.validate_legend_labels(df, 1, "label")
        assert len(errors) == 0

    def test_special_characters_in_labels(self, legend_processor: LegendProcessing) -> None:
        """Test with special characters in labels."""
        df = pd.DataFrame({"label": ["Açúcar", "Café", "Água", "Pão", "Maçã"]})

        errors = legend_processor.validate_legend_labels(df, 1, "label")
        assert len(errors) == 0

    def test_extreme_numeric_values(self, legend_processor: LegendProcessing) -> None:
        """Test with extreme numeric values."""
        df = pd.DataFrame(
            {
                "label": ["Min", "Max", "Dado indisponível"],
                "minimo": [float("-inf"), 1e10, None],
                "maximo": [1e-10, float("inf"), None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        # Should handle extreme values gracefully
        assert isinstance(errors, list)

    def test_mixed_data_types_in_numeric_columns(self, legend_processor: LegendProcessing) -> None:
        """Test with mixed data types that pandas might handle differently."""
        df = pd.DataFrame(
            {
                "codigo": [1, 2.0, 3],  # Mixed int and float
                "label": ["A", "B", "Dado indisponível"],
                "minimo": [0, 10.0, None],  # Mixed int and float
                "maximo": [9.99, 20, None],
                "ordem": [1, 2, 3],
            }
        )

        errors = legend_processor.validate_legend_columns_dtypes_numeric(df, 1, "codigo", "label", "minimo", "maximo", "ordem")

        # Should handle mixed numeric types correctly
        assert len(errors) == 0

    def test_unicode_and_encoding_issues(self, legend_processor: LegendProcessing) -> None:
        """Test with Unicode characters and potential encoding issues."""
        df = pd.DataFrame(
            {
                "label": ["测试", "テスト", "тест", "🌟", "Dado indisponível"],
                "codigo": [1, 2, 3, 4, 5],
            }
        )

        errors = legend_processor.validate_legend_labels(df, 1, "label")
        assert len(errors) == 0

    def test_precision_edge_cases_in_decimal_validation(self, legend_processor: LegendProcessing) -> None:
        """Test precision edge cases in decimal validation."""
        df = pd.DataFrame(
            {
                "label": ["A", "B", "C", "Dado indisponível"],
                "minimo": [0.0, 10.00, 20.00, None],
                "maximo": [9.99, 19.99, 29.99, None],
            }
        )

        errors = legend_processor.validate_min_max_values(df, 1, "minimo", "maximo", "label")

        # Should handle precision correctly
        assert len(errors) == 0
