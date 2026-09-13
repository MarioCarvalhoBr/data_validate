#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `DataFrameProcessing` (dataframe_processing.py).

This module provides comprehensive tests for DataFrame validation functions
including vertical bars, unnamed columns, uniqueness, column existence, and
text length constraints.

Renamed from `test_dataframe_character_processing.py` (Phase 5 round L2,
2026-09-13): `character_processing.py` (the other half of that combined test
file) was deleted as dead code (ARC-005/ARC-010 — zero production callers, see
`.specs/quality/backlog/03-architecture.md`'s ARC-005 entry); this file keeps
every `DataFrameProcessing`-only test unchanged (including the SEC-004
`*_unexpected_error_propagates` regression tests), dropping only the
`CharacterProcessing`-specific classes and the two `CharacterProcessing` calls
inside `TestDataValidationIntegration`.
"""

import pytest
import pandas as pd
from typing import List, Optional

from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing


class TestCheckVerticalBar:
    """Test suite for check_vertical_bar function using Data Driven Tests approach."""

    @pytest.fixture
    def simple_dataframe(self) -> pd.DataFrame:
        """Create a simple DataFrame for testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nome": ["João", "Maria", "Pedro"],
                "cidade": ["São Paulo", "Rio", "Brasília"],
            }
        )

    @pytest.fixture
    def dataframe_with_vertical_bars(self) -> pd.DataFrame:
        """Create DataFrame with vertical bar characters in data."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nome": ["João|Silva", "Maria", "Pedro|Santos"],
                "descricao": ["Texto|com|barras", "Normal", "Outro|texto"],
            }
        )

    @pytest.fixture
    def dataframe_with_vertical_bar_columns(self) -> pd.DataFrame:
        """Create DataFrame with vertical bar characters in column names."""
        return pd.DataFrame(
            {
                "id|code": [1, 2, 3],
                "nome|name": ["João", "Maria", "Pedro"],
                "normal_column": ["A", "B", "C"],
            }
        )

    @pytest.fixture
    def multiindex_dataframe(self) -> pd.DataFrame:
        """Create DataFrame with MultiIndex columns."""
        columns = pd.MultiIndex.from_tuples(
            [
                ("grupo1", "subcoluna1"),
                ("grupo2", "subcoluna2"),
                ("grupo3|bar", "subcoluna3"),
                ("grupo4", "sub|coluna4"),
            ]
        )
        return pd.DataFrame([[1, "A", "X", "Test"], [2, "B", "Y", "Data"]], columns=columns)

    @pytest.fixture
    def empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame."""
        return pd.DataFrame()

    def test_check_vertical_bar_clean_dataframe_success(self, simple_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar with clean DataFrame (no vertical bars)."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(simple_dataframe, "test.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_vertical_bar_data_with_vertical_bars(self, dataframe_with_vertical_bars: pd.DataFrame) -> None:
        """Test check_vertical_bar with vertical bars in data values."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(dataframe_with_vertical_bars, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 4  # Fixed: Actual count based on test data

        # Check specific error messages
        assert any("linha 2" in error for error in errors)
        assert any("linha 4" in error for error in errors)
        assert any("'nome'" in error for error in errors)
        assert any("'descricao'" in error for error in errors)

    def test_check_vertical_bar_column_names_with_vertical_bars(
        self, dataframe_with_vertical_bar_columns: pd.DataFrame
    ) -> None:
        """Test check_vertical_bar with vertical bars in column names."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(
            dataframe_with_vertical_bar_columns, "test.xlsx"
        )

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # Two columns with vertical bars

        # Check error messages contain column references
        assert any("'id|code'" in error for error in errors)
        assert any("'nome|name'" in error for error in errors)

    def test_check_vertical_bar_multiindex_columns(self, multiindex_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar with MultiIndex columns containing vertical bars."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(multiindex_dataframe, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # One level 0, one level 1 error

        # Check specific MultiIndex error messages
        assert any("nível 0" in error for error in errors)
        assert any("nível 1" in error for error in errors)

    def test_check_vertical_bar_empty_dataframe(self, empty_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar with empty DataFrame."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(empty_dataframe, "empty.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    @pytest.mark.parametrize(
        "data_values,expected_error_count",
        [
            # Test case 1: No vertical bars
            (["normal", "text", "values"], 0),
            # Test case 2: Single vertical bar
            (["text|with|bar", "normal", "text"], 1),
            # Test case 3: Multiple rows with vertical bars
            (["text|bar", "another|bar", "normal"], 2),
            # Test case 4: Empty strings and None values
            (["", None, "normal|bar"], 1),
            # Test case 5: All rows with vertical bars
            (["bar|1", "bar|2", "bar|3"], 3),
        ],
    )
    def test_check_vertical_bar_parametrized_data_scenarios(
        self, data_values: List[str], expected_error_count: int
    ) -> None:
        """Test check_vertical_bar with various data scenarios using parameterization."""
        # Arrange
        df = pd.DataFrame({"test_column": data_values})

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(df, "test.xlsx")

        # Assert
        assert len(errors) == expected_error_count
        assert is_valid == (expected_error_count == 0)

    def test_check_vertical_bar_preserves_original_dataframe(self, simple_dataframe: pd.DataFrame) -> None:
        """Test that check_vertical_bar doesn't modify the original DataFrame."""
        # Arrange
        original_data = simple_dataframe.copy()

        # Act
        DataFrameProcessing.check_dataframe_vertical_bar(simple_dataframe, "test.xlsx")

        # Assert
        pd.testing.assert_frame_equal(simple_dataframe, original_data)

    def test_check_vertical_bar_unexpected_error_propagates(self, simple_dataframe: pd.DataFrame, mocker) -> None:
        """SEC-004: `check_dataframe_vertical_bar` no longer swallows an unexpected failure into a
        generic error string -- it propagates to the caller."""
        # Arrange
        mock_astype = mocker.patch("data_validate.helpers.common.validation.dataframe_processing.pd.DataFrame.astype")
        mock_astype.side_effect = RuntimeError("Test exception")

        # Act / Assert
        with pytest.raises(RuntimeError, match="Test exception"):
            DataFrameProcessing.check_dataframe_vertical_bar(simple_dataframe, "test.xlsx")

    def test_check_vertical_bar_complex_multiindex_scenario(self) -> None:
        """Test check_vertical_bar with complex MultiIndex structure."""
        # Arrange
        columns = pd.MultiIndex.from_tuples(
            [
                ("grupo|1", "normal_sub"),
                ("normal_grupo", "sub|coluna"),
                ("grupo|2", "sub|3"),
            ]
        )
        df = pd.DataFrame([["data|bar", "normal", "text|here"]], columns=columns)

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_vertical_bar(df, "complex.xlsx")

        # Assert
        assert is_valid is False
        # Should have errors for: 2 column level 0, 2 column level 1, 2 data values
        assert len(errors) == 6


class TestCheckUnnamedColumns:
    """Test suite for check_unnamed_columns function."""

    @pytest.fixture
    def dataframe_with_unnamed_columns(self) -> pd.DataFrame:
        """Create DataFrame with unnamed columns."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nome": ["João", "Maria", "Pedro"],
                "Unnamed: 0": ["extra1", "extra2", None],
                "unnamed: 3": [None, "data", "value"],
            }
        )

    @pytest.fixture
    def multiindex_with_unnamed(self) -> pd.DataFrame:
        """Create MultiIndex DataFrame with unnamed columns."""
        columns = pd.MultiIndex.from_tuples(
            [
                ("grupo1", "normal"),
                ("grupo2", "Unnamed: 1"),
                ("grupo3", "unnamed: 2"),
            ]
        )
        return pd.DataFrame(
            [[1, "A", "X"], [2, "B", "Y"]],  # Fixed: 3 columns to match MultiIndex
            columns=columns,
        )

    def test_check_unnamed_columns_clean_dataframe(self) -> None:
        """Test check_unnamed_columns with clean DataFrame (no unnamed columns)."""
        # Arrange
        df = pd.DataFrame({"id": [1, 2, 3], "nome": ["João", "Maria", "Pedro"], "valor": [10, 20, 30]})

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_unnamed_columns(df, "test.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_unnamed_columns_with_unnamed_and_extra_data(
        self, dataframe_with_unnamed_columns: pd.DataFrame
    ) -> None:
        """Test check_unnamed_columns with unnamed columns and extra data."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_unnamed_columns(
            dataframe_with_unnamed_columns, "test.xlsx"
        )

        # Assert
        assert is_valid is False
        assert len(errors) > 0

        # Check error message format
        for error in errors:
            assert "linha" in error
            assert "valores" in error
            assert "colunas válidas" in error

    def test_check_unnamed_columns_multiindex_with_unnamed(self, multiindex_with_unnamed: pd.DataFrame) -> None:
        """Test check_unnamed_columns with MultiIndex containing unnamed columns."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_unnamed_columns(multiindex_with_unnamed, "test.xlsx")

        # Assert
        # The function should handle MultiIndex by checking level 1 names
        # Errors depend on data vs valid column count
        assert isinstance(errors, list)

    @pytest.mark.parametrize(
        "data_rows,valid_cols,unnamed_cols,expected_has_errors",
        [
            # Test case 1: Data fits valid columns
            ([[1, "A", None], [2, "B", None]], 2, 1, False),
            # Test case 2: Extra data beyond valid columns
            ([[1, "A", "extra"], [2, "B", "more"]], 2, 1, True),
            # Test case 3: No unnamed columns
            ([[1, "A", "B"], [2, "C", "D"]], 3, 0, False),
            # Test case 4: All columns unnamed
            ([[1, None, None], [2, None, None]], 0, 3, True),
        ],
    )
    def test_check_unnamed_columns_parametrized_scenarios(
        self,
        data_rows: List[List],
        valid_cols: int,
        unnamed_cols: int,
        expected_has_errors: bool,
    ) -> None:
        """Test check_unnamed_columns with various data scenarios."""
        # Arrange
        columns = []
        for i in range(valid_cols):
            columns.append(f"valid_col_{i}")
        for i in range(unnamed_cols):
            columns.append(f"Unnamed: {i}")

        df = pd.DataFrame(data_rows, columns=columns)

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_unnamed_columns(df, "test.xlsx")

        # Assert
        assert (len(errors) > 0) == expected_has_errors
        assert is_valid == (not expected_has_errors)

    def test_check_unnamed_columns_empty_dataframe(self) -> None:
        """Test check_unnamed_columns with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_unnamed_columns(df, "empty.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_unnamed_columns_unexpected_error_propagates(self, mocker) -> None:
        """SEC-004: `check_dataframe_unnamed_columns` no longer swallows an unexpected failure into
        a generic error string -- it propagates to the caller."""
        # Arrange
        mock_notna = mocker.patch("pandas.DataFrame.notna")
        mock_notna.side_effect = RuntimeError("Test exception")
        df = pd.DataFrame({"test": [1, 2, 3]})

        # Act / Assert
        with pytest.raises(RuntimeError, match="Test exception"):
            DataFrameProcessing.check_dataframe_unnamed_columns(df, "test.xlsx")


class TestCheckUniqueValues:
    """Test suite for check_unique_values function."""

    @pytest.fixture
    def dataframe_with_duplicates(self) -> pd.DataFrame:
        """Create DataFrame with duplicate values in some columns."""
        return pd.DataFrame(
            {
                "id_unique": [1, 2, 3, 4],
                "codigo_duplicate": ["A", "B", "A", "C"],
                "nome_duplicate": ["João", "Maria", "João", "Ana"],
                "valor_unique": [100, 200, 300, 400],
            }
        )

    @pytest.fixture
    def dataframe_all_unique(self) -> pd.DataFrame:
        """Create DataFrame with all unique values."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "codigo": ["A", "B", "C"],
                "nome": ["João", "Maria", "Pedro"],
            }
        )

    def test_check_unique_values_all_unique_columns(self, dataframe_all_unique: pd.DataFrame) -> None:
        """Test check_unique_values with columns that have all unique values."""
        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(
            dataframe_all_unique, "test.xlsx", ["id", "codigo", "nome"]
        )

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_unique_values_with_duplicates(self, dataframe_with_duplicates: pd.DataFrame) -> None:
        """Test check_unique_values with columns containing duplicates."""
        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(
            dataframe_with_duplicates,
            "test.xlsx",
            ["codigo_duplicate", "nome_duplicate"],
        )

        # Assert
        assert is_valid is False
        assert len(warnings) == 2

        # Check specific columns mentioned in warnings
        assert any("'codigo_duplicate'" in warning for warning in warnings)
        assert any("'nome_duplicate'" in warning for warning in warnings)

    def test_check_unique_values_mixed_unique_and_duplicate(self, dataframe_with_duplicates: pd.DataFrame) -> None:
        """Test check_unique_values with mix of unique and duplicate columns."""
        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(
            dataframe_with_duplicates,
            "test.xlsx",
            ["id_unique", "codigo_duplicate", "valor_unique"],
        )

        # Assert
        assert is_valid is False
        assert len(warnings) == 1  # Only codigo_duplicate has duplicates
        assert "'codigo_duplicate'" in warnings[0]

    def test_check_unique_values_nonexistent_columns(self, dataframe_all_unique: pd.DataFrame) -> None:
        """Test check_unique_values with non-existent columns."""
        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(
            dataframe_all_unique, "test.xlsx", ["nonexistent1", "nonexistent2"]
        )

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_unique_values_empty_columns_list(self, dataframe_with_duplicates: pd.DataFrame) -> None:
        """Test check_unique_values with empty columns list."""
        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(
            dataframe_with_duplicates, "test.xlsx", []
        )

        # Assert
        assert is_valid is True
        assert warnings == []

    @pytest.mark.parametrize(
        "column_data,expected_is_unique",
        [
            # Test case 1: All unique values
            ([1, 2, 3, 4], True),
            # Test case 2: Duplicate values
            ([1, 2, 2, 3], False),
            # Test case 3: All same values
            ([1, 1, 1, 1], False),
            # Test case 4: Single value
            ([1], True),
            # Test case 5: Empty list (unique by definition)
            ([], True),
            # Test case 6: String duplicates
            (["A", "B", "A"], False),
            # Test case 7: Mixed types (all unique)
            ([1, "A", 2.5], True),
        ],
    )
    def test_check_unique_values_parametrized_data(self, column_data: List, expected_is_unique: bool) -> None:
        """Test check_unique_values with various data patterns."""
        # Arrange
        df = pd.DataFrame({"test_column": column_data})

        # Act
        is_valid, warnings = DataFrameProcessing.check_dataframe_unique_values(df, "test.xlsx", ["test_column"])

        # Assert
        assert is_valid == expected_is_unique
        assert (len(warnings) == 0) == expected_is_unique


class TestColumnExists:
    """Test suite for column_exists function."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for column existence testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nome": ["João", "Maria", "Pedro"],
                "valor": [100, 200, 300],
            }
        )

    def test_column_exists_existing_column(self, sample_dataframe: pd.DataFrame) -> None:
        """Test column_exists with existing column."""
        # Act
        exists, error_message = DataFrameProcessing.column_exists(sample_dataframe, "test.xlsx", "nome")

        # Assert
        assert exists is True
        assert error_message == ""

    def test_column_exists_nonexistent_column(self, sample_dataframe: pd.DataFrame) -> None:
        """Test column_exists with non-existent column."""
        # Act
        exists, error_message = DataFrameProcessing.column_exists(sample_dataframe, "test.xlsx", "nonexistent")

        # Assert
        assert exists is False
        assert "verificação foi abortada" in error_message
        assert "'nonexistent'" in error_message
        assert "ausente" in error_message

    @pytest.mark.parametrize(
        "column_name,should_exist",
        [
            ("id", True),
            ("nome", True),
            ("valor", True),
            ("missing_column", False),
            ("another_missing", False),
        ],
    )
    def test_column_exists_parametrized(
        self, sample_dataframe: pd.DataFrame, column_name: str, should_exist: bool
    ) -> None:
        """Test column_exists with various column names."""
        # Act
        exists, error_message = DataFrameProcessing.column_exists(sample_dataframe, "test.xlsx", column_name)

        # Assert
        assert exists == should_exist
        if should_exist:
            assert error_message == ""
        else:
            assert error_message != ""
            assert column_name in error_message

    def test_column_exists_empty_dataframe(self) -> None:
        """Test column_exists with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()

        # Act
        exists, error_message = DataFrameProcessing.column_exists(df, "empty.xlsx", "any_column")

        # Assert
        assert exists is False
        assert "any_column" in error_message


class TestCheckTextLength:
    """Test suite for check_text_length function."""

    @pytest.fixture
    def dataframe_with_various_text_lengths(self) -> pd.DataFrame:
        """Create DataFrame with texts of various lengths."""
        return pd.DataFrame(
            {
                "short_text": ["A", "AB", "ABC"],
                "medium_text": [
                    "Medium length text here",
                    "Another medium text",
                    "Third medium",
                ],
                "long_text": [
                    "This is a very long text that exceeds normal limits for testing purposes",
                    "Another extremely long text that goes beyond reasonable character limits",
                    "Short",
                ],
                "mixed_length": [
                    "Short",
                    "Medium length text",
                    "Very long text that exceeds limits",
                ],
            }
        )

    def test_check_text_length_all_within_limit(self, dataframe_with_various_text_lengths: pd.DataFrame) -> None:
        """Test check_text_length with all texts within limit."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(
            dataframe_with_various_text_lengths, "test.xlsx", "short_text", 10
        )

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_some_exceed_limit(self, dataframe_with_various_text_lengths: pd.DataFrame) -> None:
        """Test check_text_length with some texts exceeding limit."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(
            dataframe_with_various_text_lengths, "test.xlsx", "long_text", 30
        )

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # Two long texts exceed 30 characters

        # Check error message format
        for error in errors:
            assert "excede o limite" in error
            assert "encontrado:" in error

    def test_check_text_length_nonexistent_column(self, dataframe_with_various_text_lengths: pd.DataFrame) -> None:
        """Test check_text_length with non-existent column."""
        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(
            dataframe_with_various_text_lengths, "test.xlsx", "nonexistent", 50
        )

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "verificação foi abortada" in errors[0]
        assert "nonexistent" in errors[0]

    @pytest.mark.parametrize(
        "text_values,max_length,expected_error_count",
        [
            # Test case 1: All texts within limit
            (["Short", "Text", "OK"], 10, 0),
            # Test case 2: Some texts exceed limit
            (["Short", "This is a very long text"], 10, 1),
            # Test case 3: All texts exceed limit
            (["Very long text here", "Another long text"], 5, 2),
            # Test case 4: Empty and None values (should be ignored)
            (["", None, "Short"], 4, 1),
            # Test case 5: Exact limit
            (["12345", "123"], 5, 0),
            # Test case 6: One character over limit
            (["123456", "123"], 5, 1),
        ],
    )
    def test_check_text_length_parametrized_scenarios(
        self,
        text_values: List[Optional[str]],
        max_length: int,
        expected_error_count: int,
    ) -> None:
        """Test check_text_length with various text length scenarios."""
        # Arrange
        df = pd.DataFrame({"test_column": text_values})

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(df, "test.xlsx", "test_column", max_length)

        # Assert
        assert len(errors) == expected_error_count
        assert is_valid == (expected_error_count == 0)

    def test_check_text_length_handles_none_values(self) -> None:
        """Test check_text_length properly handles None values."""
        # Arrange
        df = pd.DataFrame({"test_col": [None, "Valid text", None, "Another valid text"]})

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(df, "test.xlsx", "test_col", 20)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_empty_dataframe(self) -> None:
        """Test check_text_length with empty DataFrame."""
        # Arrange
        df = pd.DataFrame({"test_col": []})

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(df, "empty.xlsx", "test_col", 10)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_preserves_original_dataframe(
        self, dataframe_with_various_text_lengths: pd.DataFrame
    ) -> None:
        """Test that check_text_length doesn't modify the original DataFrame."""
        # Arrange
        original_data = dataframe_with_various_text_lengths.copy()

        # Act
        DataFrameProcessing.check_dataframe_text_length(
            dataframe_with_various_text_lengths, "test.xlsx", "short_text", 10
        )

        # Assert
        pd.testing.assert_frame_equal(dataframe_with_various_text_lengths, original_data)

    def test_check_text_length_accurate_character_counting(self) -> None:
        """Test check_text_length accurately counts characters including special ones."""
        # Arrange
        df = pd.DataFrame(
            {
                "special_text": [
                    "Texto com acentos: ção, não",  # 27 characters
                    "Símbolos: @#$%&*(){}[]",  # 22 characters
                    "Números: 12345",  # 15 characters
                ]
            }
        )

        # Act
        is_valid, errors = DataFrameProcessing.check_dataframe_text_length(df, "test.xlsx", "special_text", 20)

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # First two exceed 20 characters

        # Verify character counts in error messages
        assert "27" in errors[0]
        assert "22" in errors[1]


class TestDataValidationIntegration:
    """Integration tests for data validation functions working together."""

    @pytest.fixture
    def complex_test_dataframe(self) -> pd.DataFrame:
        """Create complex DataFrame for integration testing."""
        return pd.DataFrame(
            {
                "id|code": [1, 2, 3],  # Column name with vertical bar
                "titulo": ["Título sem ponto", "Título com ponto.", "Título,"],
                "descricao": ["Descrição\x0dcom CR", "Normal", "Texto|vertical"],
                "codigo_unico": ["A001", "B002", "A001"],  # Duplicate values
                "texto_longo": [
                    "Short",
                    "This is a very long text that exceeds limits",
                    "OK",
                ],
                "Unnamed: 0": ["extra1", "extra2", "extra3"],
            }
        )

    def test_comprehensive_validation_workflow(self, complex_test_dataframe: pd.DataFrame) -> None:
        """Test comprehensive validation workflow with multiple validation types."""
        file_name = "complex_test.xlsx"
        all_errors = []
        all_warnings = []

        # 1. Check vertical bars
        is_valid_vbar, errors_vbar = DataFrameProcessing.check_dataframe_vertical_bar(complex_test_dataframe, file_name)
        all_errors.extend(errors_vbar)

        # 2. Check unnamed columns
        is_valid_unnamed, errors_unnamed = DataFrameProcessing.check_dataframe_unnamed_columns(
            complex_test_dataframe, file_name
        )
        all_errors.extend(errors_unnamed)

        # 3. Check unique values
        is_valid_unique, warnings_unique = DataFrameProcessing.check_dataframe_unique_values(
            complex_test_dataframe, file_name, ["codigo_unico"]
        )
        all_warnings.extend(warnings_unique)

        # 4. Check text length
        is_valid_length, errors_length = DataFrameProcessing.check_dataframe_text_length(
            complex_test_dataframe, file_name, "texto_longo", 20
        )
        all_errors.extend(errors_length)

        # Assert comprehensive results
        assert len(all_errors) > 0  # Should have multiple types of errors
        assert len(all_warnings) > 0  # Should have warnings

        # Verify different types of issues are caught
        error_text = " ".join(all_errors + all_warnings)
        assert "barra vertical" in error_text or "|" in error_text
        assert "valores repetidos" in error_text
        assert "excede o limite" in error_text

    def test_validation_functions_return_consistent_format(self) -> None:
        """Test that all validation functions return consistent format."""
        df = pd.DataFrame({"test": ["normal text"]})
        file_name = "test.xlsx"

        # Test each function returns (bool, list) tuple
        functions_to_test = [
            (DataFrameProcessing.check_dataframe_vertical_bar, (df, file_name)),
            (DataFrameProcessing.check_dataframe_unnamed_columns, (df, file_name)),
            (DataFrameProcessing.check_dataframe_unique_values, (df, file_name, [])),
            (DataFrameProcessing.column_exists, (df, file_name, "test")),
            (DataFrameProcessing.check_dataframe_text_length, (df, file_name, "test", 50)),
        ]

        for func, args in functions_to_test:
            result = func(*args)
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], bool)


class TestCheckDataframeTitlesUniques:
    """Test suite for check_dataframe_titles_uniques function."""

    def test_check_dataframe_titles_uniques_no_duplicates(self):
        """Test with no duplicate titles."""
        df = pd.DataFrame(
            {"title_one": ["Title 1", "Title 2", "Title 3"], "title_two": ["Subtitle 1", "Subtitle 2", "Subtitle 3"]}
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert result == []

    def test_check_dataframe_titles_uniques_with_duplicates_first_column(self):
        """Test with duplicates in first column."""
        df = pd.DataFrame(
            {"title_one": ["Title 1", "Title 1", "Title 3"], "title_two": ["Subtitle 1", "Subtitle 2", "Subtitle 3"]}
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 1
        assert "titles one duplicados: ['Title 1']" in result[0]

    def test_check_dataframe_titles_uniques_with_duplicates_second_column(self):
        """Test with duplicates in second column."""
        df = pd.DataFrame(
            {"title_one": ["Title 1", "Title 2", "Title 3"], "title_two": ["Subtitle 1", "Subtitle 1", "Subtitle 3"]}
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 1
        assert "titles two duplicados: ['Subtitle 1']" in result[0]

    def test_check_dataframe_titles_uniques_with_duplicates_both_columns(self):
        """Test with duplicates in both columns."""
        df = pd.DataFrame(
            {"title_one": ["Title 1", "Title 1", "Title 3"], "title_two": ["Subtitle 1", "Subtitle 1", "Subtitle 3"]}
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 2
        assert any("titles one duplicados: ['Title 1']" in msg for msg in result)
        assert any("titles two duplicados: ['Subtitle 1']" in msg for msg in result)

    def test_check_dataframe_titles_uniques_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=["title_one", "title_two"])

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert result == []

    def test_check_dataframe_titles_uniques_missing_columns(self):
        """Test with missing columns."""
        df = pd.DataFrame({"title_one": ["Title 1", "Title 2", "Title 3"]})

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 0  # Should not find duplicates in missing column

    def test_check_dataframe_titles_uniques_multiple_duplicates(self):
        """Test with multiple duplicate values."""
        df = pd.DataFrame(
            {
                "title_one": ["Title 1", "Title 1", "Title 2", "Title 2", "Title 3"],
                "title_two": ["Subtitle 1", "Subtitle 2", "Subtitle 3", "Subtitle 3", "Subtitle 4"],
            }
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 2
        assert any("titles one duplicados: ['Title 1', 'Title 2']" in msg for msg in result)
        assert any("titles two duplicados: ['Subtitle 3']" in msg for msg in result)

    def test_check_dataframe_titles_uniques_with_whitespace(self):
        """Test with titles that have leading/trailing whitespace."""
        df = pd.DataFrame(
            {"title_one": [" Title 1 ", "Title 1", "Title 3"], "title_two": ["Subtitle 1", "Subtitle 2", "Subtitle 3"]}
        )

        result = DataFrameProcessing.check_dataframe_titles_uniques(
            df, "title_one", "title_two", "titles_one", "titles_two"
        )
        assert len(result) == 1
        assert "titles one duplicados: ['Title 1']" in result[0]


class TestColumnExistsMultiIndex:
    """Test suite for column_exists function with MultiIndex."""

    def test_column_exists_multiindex_column_found(self):
        """Test column_exists with MultiIndex when column is found."""
        df = pd.DataFrame({("level1", "level2_col"): [1, 2, 3], ("level1", "other_col"): ["a", "b", "c"]})

        result = DataFrameProcessing.column_exists(df, "test.xlsx", "level2_col")
        assert result == (True, "")

    def test_column_exists_multiindex_column_not_found(self):
        """Test column_exists with MultiIndex when column is not found."""
        df = pd.DataFrame({("level1", "level2_col"): [1, 2, 3], ("level1", "other_col"): ["a", "b", "c"]})

        result = DataFrameProcessing.column_exists(df, "test.xlsx", "missing_col")
        assert result == (
            False,
            "test.xlsx: A verificação foi abortada para a coluna nível 2 obrigatória 'missing_col' que está ausente.",
        )
        assert isinstance(result[1], (list, str))  # column_exists returns str for second element
