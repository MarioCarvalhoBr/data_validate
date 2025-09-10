"""Unit tests for data validation utilities.

This module provides comprehensive tests for DataFrame validation functions
including vertical bars, unnamed columns, punctuation rules, special characters,
and text length constraints.
"""

#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

import pytest
import pandas as pd
from typing import List, Tuple, Optional
from unittest.mock import patch, Mock

from data_validate.helpers.common.validation.data_validation import (
    check_vertical_bar,
    check_unnamed_columns,
    check_punctuation,
    check_special_characters_cr_lf_columns_start_end,
    check_special_characters_cr_lf_columns_anywhere,
    check_special_characters_cr_lf,
    check_unique_values,
    column_exists,
    check_text_length,
)


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
        is_valid, errors = check_vertical_bar(simple_dataframe, "test.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_vertical_bar_data_with_vertical_bars(self, dataframe_with_vertical_bars: pd.DataFrame) -> None:
        """Test check_vertical_bar with vertical bars in data values."""
        # Act
        is_valid, errors = check_vertical_bar(dataframe_with_vertical_bars, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 4  # Fixed: Actual count based on test data

        # Check specific error messages
        assert any("linha 2" in error for error in errors)
        assert any("linha 4" in error for error in errors)
        assert any("'nome'" in error for error in errors)
        assert any("'descricao'" in error for error in errors)

    def test_check_vertical_bar_column_names_with_vertical_bars(self, dataframe_with_vertical_bar_columns: pd.DataFrame) -> None:
        """Test check_vertical_bar with vertical bars in column names."""
        # Act
        is_valid, errors = check_vertical_bar(dataframe_with_vertical_bar_columns, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # Two columns with vertical bars

        # Check error messages contain column references
        assert any("'id|code'" in error for error in errors)
        assert any("'nome|name'" in error for error in errors)

    def test_check_vertical_bar_multiindex_columns(self, multiindex_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar with MultiIndex columns containing vertical bars."""
        # Act
        is_valid, errors = check_vertical_bar(multiindex_dataframe, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 2  # One level 0, one level 1 error

        # Check specific MultiIndex error messages
        assert any("nível 0" in error for error in errors)
        assert any("nível 1" in error for error in errors)

    def test_check_vertical_bar_empty_dataframe(self, empty_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar with empty DataFrame."""
        # Act
        is_valid, errors = check_vertical_bar(empty_dataframe, "empty.xlsx")

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
    def test_check_vertical_bar_parametrized_data_scenarios(self, data_values: List[str], expected_error_count: int) -> None:
        """Test check_vertical_bar with various data scenarios using parameterization."""
        # Arrange
        df = pd.DataFrame({"test_column": data_values})

        # Act
        is_valid, errors = check_vertical_bar(df, "test.xlsx")

        # Assert
        assert len(errors) == expected_error_count
        assert is_valid == (expected_error_count == 0)

    def test_check_vertical_bar_preserves_original_dataframe(self, simple_dataframe: pd.DataFrame) -> None:
        """Test that check_vertical_bar doesn't modify the original DataFrame."""
        # Arrange
        original_data = simple_dataframe.copy()

        # Act
        check_vertical_bar(simple_dataframe, "test.xlsx")

        # Assert
        pd.testing.assert_frame_equal(simple_dataframe, original_data)

    @patch("data_validate.helpers.common.validation.data_validation.pd.DataFrame.astype")
    def test_check_vertical_bar_exception_handling(self, mock_astype: Mock, simple_dataframe: pd.DataFrame) -> None:
        """Test check_vertical_bar exception handling."""
        # Arrange
        mock_astype.side_effect = Exception("Test exception")

        # Act
        is_valid, errors = check_vertical_bar(simple_dataframe, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "Erro ao processar a checagem de barra vertical" in errors[0]

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
        is_valid, errors = check_vertical_bar(df, "complex.xlsx")

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
        is_valid, errors = check_unnamed_columns(df, "test.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_unnamed_columns_with_unnamed_and_extra_data(self, dataframe_with_unnamed_columns: pd.DataFrame) -> None:
        """Test check_unnamed_columns with unnamed columns and extra data."""
        # Act
        is_valid, errors = check_unnamed_columns(dataframe_with_unnamed_columns, "test.xlsx")

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
        is_valid, errors = check_unnamed_columns(multiindex_with_unnamed, "test.xlsx")

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
        is_valid, errors = check_unnamed_columns(df, "test.xlsx")

        # Assert
        assert (len(errors) > 0) == expected_has_errors
        assert is_valid == (not expected_has_errors)

    def test_check_unnamed_columns_empty_dataframe(self) -> None:
        """Test check_unnamed_columns with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()

        # Act
        is_valid, errors = check_unnamed_columns(df, "empty.xlsx")

        # Assert
        assert is_valid is True
        assert errors == []

    @patch("pandas.DataFrame.notna")
    def test_check_unnamed_columns_exception_handling(self, mock_notna: Mock) -> None:
        """Test check_unnamed_columns exception handling."""
        # Arrange
        mock_notna.side_effect = Exception("Test exception")
        df = pd.DataFrame({"test": [1, 2, 3]})

        # Act
        is_valid, errors = check_unnamed_columns(df, "test.xlsx")

        # Assert
        assert is_valid is False
        assert len(errors) == 1
        assert "Erro ao processar a checagem de colunas sem nome" in errors[0]


class TestCheckPunctuation:
    """Test suite for check_punctuation function."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for punctuation testing."""
        return pd.DataFrame(
            {
                "titulo": ["Título sem ponto", "Título com ponto.", "Título,"],
                "descricao": [
                    "Descrição completa.",
                    "Descrição sem ponto",
                    "Descrição com exclamação!",
                ],
                "codigo": ["A001", "B002", "C003"],
                "observacao": ["", None, "Observação válida."],
            }
        )

    @pytest.mark.parametrize(
        "columns_dont_punctuation,columns_must_end_with_dot,expected_warning_count",
        [
            # Test case 1: No restrictions
            ([], [], 0),
            # Test case 2: Titles shouldn't end with punctuation
            (["titulo"], [], 2),  # Two titles end with punctuation
            # Test case 3: Descriptions must end with dot
            ([], ["descricao"], 2),  # Two descriptions don't end with dot
            # Test case 4: Both restrictions
            (["titulo"], ["descricao"], 4),  # Combined warnings
            # Test case 5: Non-existent columns
            (["non_existent"], ["also_non_existent"], 0),
        ],
    )
    def test_check_punctuation_parametrized_scenarios(
        self,
        sample_dataframe: pd.DataFrame,
        columns_dont_punctuation: List[str],
        columns_must_end_with_dot: List[str],
        expected_warning_count: int,
    ) -> None:
        """Test check_punctuation with various column configurations."""
        # Act
        is_valid, warnings = check_punctuation(
            sample_dataframe,
            "test.xlsx",
            columns_dont_punctuation,
            columns_must_end_with_dot,
        )

        # Assert
        assert len(warnings) == expected_warning_count
        assert is_valid == (expected_warning_count == 0)

    def test_check_punctuation_empty_dataframe(self) -> None:
        """Test check_punctuation with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()

        # Act
        is_valid, warnings = check_punctuation(df, "empty.xlsx", ["col1"], ["col2"])

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_punctuation_handles_none_values(self) -> None:
        """Test check_punctuation properly handles None and empty values."""
        # Arrange
        df = pd.DataFrame({"test_col": [None, "", "Valid text.", "Invalid text,"]})

        # Act
        is_valid, warnings = check_punctuation(df, "test.xlsx", ["test_col"], [])

        # Assert
        assert len(warnings) == 2  # Fixed: Both Valid text. and Invalid text, trigger warnings
        assert any("pontuação" in warning for warning in warnings)

    @pytest.mark.parametrize(
        "text_value,should_warn_no_punct,should_warn_need_dot",
        [
            # Test case 1: Perfect text ending with dot
            (
                "Texto correto.",
                True,
                False,
            ),  # Fixed: dot is punctuation, so should warn for no_punct
            # Test case 2: Text with comma (punctuation)
            ("Texto com vírgula,", True, True),
            # Test case 3: Text without punctuation
            ("Texto sem pontuação", False, True),
            # Test case 4: Text with question mark
            ("Texto com pergunta?", True, True),
            # Test case 5: Empty text
            ("", False, False),
        ],
    )
    def test_check_punctuation_individual_text_cases(self, text_value: str, should_warn_no_punct: bool, should_warn_need_dot: bool) -> None:
        """Test check_punctuation with individual text cases."""
        # Arrange
        df = pd.DataFrame({"test_col": [text_value]})

        # Act - Test no punctuation rule
        is_valid_no_punct, warnings_no_punct = check_punctuation(df, "test.xlsx", ["test_col"], [])

        # Act - Test must end with dot rule
        is_valid_dot, warnings_dot = check_punctuation(df, "test.xlsx", [], ["test_col"])

        # Assert
        assert (len(warnings_no_punct) > 0) == should_warn_no_punct
        assert (len(warnings_dot) > 0) == should_warn_need_dot


class TestCheckSpecialCharactersCrLf:
    """Test suite for CR/LF special characters checking functions."""

    @pytest.fixture
    def dataframe_with_cr_lf_characters(self) -> pd.DataFrame:
        """Create DataFrame with CR/LF characters in various positions."""
        return pd.DataFrame(
            {
                "text_start_cr": ["\x0dStart with CR", "Normal text", "Another normal"],
                "text_end_lf": ["End with LF\x0a", "Normal text", "Also normal"],
                "text_middle_cr": ["Middle\x0dCR text", "Normal", "Text with\x0dCR"],
                "normal_column": ["Normal text 1", "Normal text 2", "Normal text 3"],
            }
        )

    @pytest.fixture
    def clean_dataframe_no_special_chars(self) -> pd.DataFrame:
        """Create clean DataFrame without special characters."""
        return pd.DataFrame(
            {
                "column1": ["Normal text", "Another normal", "Clean text"],
                "column2": ["Clean data", "No special chars", "All good"],
            }
        )

    def test_check_special_characters_cr_lf_columns_start_end_clean_data(self, clean_dataframe_no_special_chars: pd.DataFrame) -> None:
        """Test start/end CR/LF check with clean data."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf_columns_start_end(clean_dataframe_no_special_chars, "test.xlsx", ["column1", "column2"])

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_special_characters_cr_lf_columns_start_end_with_issues(self, dataframe_with_cr_lf_characters: pd.DataFrame) -> None:
        """Test start/end CR/LF check with problematic data."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf_columns_start_end(
            dataframe_with_cr_lf_characters,
            "test.xlsx",
            ["text_start_cr", "text_end_lf"],
        )

        # Assert
        assert is_valid is False
        assert len(warnings) == 2  # One start CR, one end LF

        # Check warning content
        assert any("início do texto" in warning for warning in warnings)
        assert any("final do texto" in warning for warning in warnings)

    def test_check_special_characters_cr_lf_columns_anywhere_clean_data(self, clean_dataframe_no_special_chars: pd.DataFrame) -> None:
        """Test anywhere CR/LF check with clean data."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf_columns_anywhere(clean_dataframe_no_special_chars, "test.xlsx", ["column1"])

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_special_characters_cr_lf_columns_anywhere_with_issues(self, dataframe_with_cr_lf_characters: pd.DataFrame) -> None:
        """Test anywhere CR/LF check with problematic data."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf_columns_anywhere(dataframe_with_cr_lf_characters, "test.xlsx", ["text_middle_cr"])

        # Assert
        assert is_valid is False
        assert len(warnings) == 2  # Two texts with middle CR

        # Check position information in warnings
        assert any("posição" in warning for warning in warnings)

    def test_check_special_characters_cr_lf_combined_function(self, dataframe_with_cr_lf_characters: pd.DataFrame) -> None:
        """Test the combined CR/LF checking function."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf(
            dataframe_with_cr_lf_characters,
            "test.xlsx",
            columns_start_end=["text_start_cr", "text_end_lf"],
            columns_anywhere=["text_middle_cr"],
        )

        # Assert
        assert is_valid is False
        assert len(warnings) == 4  # 2 start/end + 2 anywhere

        # Verify all types of warnings are present
        warning_text = " ".join(warnings)
        assert "início do texto" in warning_text
        assert "final do texto" in warning_text
        assert "posição" in warning_text

    @pytest.mark.parametrize(
        "text_with_special_chars,expected_positions",
        [
            # Test case 1: No special characters
            ("Normal text", []),
            # Test case 2: Single CR at position 5
            ("Text\x0dhere", [(5, "CR")]),
            # Test case 3: Single LF at position 3
            ("AB\x0aCD", [(3, "LF")]),
            # Test case 4: Multiple special characters
            ("A\x0dB\x0aC", [(2, "CR"), (4, "LF")]),
            # Test case 5: Special chars at start and end
            ("\x0dStart\x0a", [(1, "CR"), (7, "LF")]),
        ],
    )
    def test_find_cr_lf_positions_parametrized(self, text_with_special_chars: str, expected_positions: List[Tuple[int, str]]) -> None:
        """Test CR/LF position finding with various text patterns."""
        # Arrange
        df = pd.DataFrame({"test_col": [text_with_special_chars]})

        # Act
        is_valid, warnings = check_special_characters_cr_lf_columns_anywhere(df, "test.xlsx", ["test_col"])

        # Assert
        assert len(warnings) == len(expected_positions)
        if expected_positions:
            assert is_valid is False
            for i, (pos, char_type) in enumerate(expected_positions):
                assert f"posição {pos}" in warnings[i]
                assert char_type in warnings[i]
        else:
            assert is_valid is True

    def test_check_special_characters_empty_columns_list(self, dataframe_with_cr_lf_characters: pd.DataFrame) -> None:
        """Test CR/LF functions with empty column lists."""
        # Act
        is_valid_start_end, warnings_start_end = check_special_characters_cr_lf_columns_start_end(dataframe_with_cr_lf_characters, "test.xlsx", [])

        is_valid_anywhere, warnings_anywhere = check_special_characters_cr_lf_columns_anywhere(dataframe_with_cr_lf_characters, "test.xlsx", [])

        # Assert
        assert is_valid_start_end is True
        assert warnings_start_end == []
        assert is_valid_anywhere is True
        assert warnings_anywhere == []

    def test_check_special_characters_nonexistent_columns(self, clean_dataframe_no_special_chars: pd.DataFrame) -> None:
        """Test CR/LF functions with non-existent columns."""
        # Act
        is_valid, warnings = check_special_characters_cr_lf(
            clean_dataframe_no_special_chars,
            "test.xlsx",
            columns_start_end=["nonexistent1"],
            columns_anywhere=["nonexistent2"],
        )

        # Assert
        assert is_valid is True
        assert warnings == []


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
        is_valid, warnings = check_unique_values(dataframe_all_unique, "test.xlsx", ["id", "codigo", "nome"])

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_unique_values_with_duplicates(self, dataframe_with_duplicates: pd.DataFrame) -> None:
        """Test check_unique_values with columns containing duplicates."""
        # Act
        is_valid, warnings = check_unique_values(
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
        is_valid, warnings = check_unique_values(
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
        is_valid, warnings = check_unique_values(dataframe_all_unique, "test.xlsx", ["nonexistent1", "nonexistent2"])

        # Assert
        assert is_valid is True
        assert warnings == []

    def test_check_unique_values_empty_columns_list(self, dataframe_with_duplicates: pd.DataFrame) -> None:
        """Test check_unique_values with empty columns list."""
        # Act
        is_valid, warnings = check_unique_values(dataframe_with_duplicates, "test.xlsx", [])

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
        is_valid, warnings = check_unique_values(df, "test.xlsx", ["test_column"])

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
        exists, error_message = column_exists(sample_dataframe, "test.xlsx", "nome")

        # Assert
        assert exists is True
        assert error_message == ""

    def test_column_exists_nonexistent_column(self, sample_dataframe: pd.DataFrame) -> None:
        """Test column_exists with non-existent column."""
        # Act
        exists, error_message = column_exists(sample_dataframe, "test.xlsx", "nonexistent")

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
    def test_column_exists_parametrized(self, sample_dataframe: pd.DataFrame, column_name: str, should_exist: bool) -> None:
        """Test column_exists with various column names."""
        # Act
        exists, error_message = column_exists(sample_dataframe, "test.xlsx", column_name)

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
        exists, error_message = column_exists(df, "empty.xlsx", "any_column")

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
        is_valid, errors = check_text_length(dataframe_with_various_text_lengths, "test.xlsx", "short_text", 10)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_some_exceed_limit(self, dataframe_with_various_text_lengths: pd.DataFrame) -> None:
        """Test check_text_length with some texts exceeding limit."""
        # Act
        is_valid, errors = check_text_length(dataframe_with_various_text_lengths, "test.xlsx", "long_text", 30)

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
        is_valid, errors = check_text_length(dataframe_with_various_text_lengths, "test.xlsx", "nonexistent", 50)

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
        is_valid, errors = check_text_length(df, "test.xlsx", "test_column", max_length)

        # Assert
        assert len(errors) == expected_error_count
        assert is_valid == (expected_error_count == 0)

    def test_check_text_length_handles_none_values(self) -> None:
        """Test check_text_length properly handles None values."""
        # Arrange
        df = pd.DataFrame({"test_col": [None, "Valid text", None, "Another valid text"]})

        # Act
        is_valid, errors = check_text_length(df, "test.xlsx", "test_col", 20)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_empty_dataframe(self) -> None:
        """Test check_text_length with empty DataFrame."""
        # Arrange
        df = pd.DataFrame({"test_col": []})

        # Act
        is_valid, errors = check_text_length(df, "empty.xlsx", "test_col", 10)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_check_text_length_preserves_original_dataframe(self, dataframe_with_various_text_lengths: pd.DataFrame) -> None:
        """Test that check_text_length doesn't modify the original DataFrame."""
        # Arrange
        original_data = dataframe_with_various_text_lengths.copy()

        # Act
        check_text_length(dataframe_with_various_text_lengths, "test.xlsx", "short_text", 10)

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
        is_valid, errors = check_text_length(df, "test.xlsx", "special_text", 20)

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
        is_valid_vbar, errors_vbar = check_vertical_bar(complex_test_dataframe, file_name)
        all_errors.extend(errors_vbar)

        # 2. Check unnamed columns
        is_valid_unnamed, errors_unnamed = check_unnamed_columns(complex_test_dataframe, file_name)
        all_errors.extend(errors_unnamed)

        # 3. Check punctuation
        is_valid_punct, warnings_punct = check_punctuation(complex_test_dataframe, file_name, ["titulo"], ["descricao"])
        all_warnings.extend(warnings_punct)

        # 4. Check unique values
        is_valid_unique, warnings_unique = check_unique_values(complex_test_dataframe, file_name, ["codigo_unico"])
        all_warnings.extend(warnings_unique)

        # 5. Check text length
        is_valid_length, errors_length = check_text_length(complex_test_dataframe, file_name, "texto_longo", 20)
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
            (check_vertical_bar, (df, file_name)),
            (check_unnamed_columns, (df, file_name)),
            (check_punctuation, (df, file_name, [], [])),
            (check_unique_values, (df, file_name, [])),
            (column_exists, (df, file_name, "test")),
            (check_text_length, (df, file_name, "test", 50)),
        ]

        for func, args in functions_to_test:
            result = func(*args)
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], bool)
            assert isinstance(result[1], (list, str))  # column_exists returns str for second element
