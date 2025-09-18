"""Unit tests for column validation utilities."""

#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

import pytest
import pandas as pd
from typing import List

from src.helpers.common.validation.column_validation import check_column_names


class TestCheckColumnNames:
    """Test suite for check_column_names function using Data Driven Tests approach."""

    @pytest.fixture
    def empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame for testing."""
        return pd.DataFrame()

    @pytest.fixture
    def simple_dataframe(self) -> pd.DataFrame:
        """Create a simple DataFrame with basic columns."""
        return pd.DataFrame({"id": [1, 2, 3], "nome": ["A", "B", "C"], "valor": [10, 20, 30]})

    @pytest.fixture
    def dataframe_with_unnamed_columns(self) -> pd.DataFrame:
        """Create DataFrame with unnamed columns that should be filtered out."""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nome": ["A", "B", "C"],
                "Unnamed: 0": [0, 1, 2],
                "unnamed: 3": [10, 20, 30],
                "UNNAMED: 5": [100, 200, 300],
            }
        )
        return df

    @pytest.fixture
    def dataframe_with_mixed_case_columns(self) -> pd.DataFrame:
        """Create DataFrame with mixed case column names."""
        return pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Nome": ["A", "B", "C"],
                "VALOR": [10, 20, 30],
                "codigo_pai": [100, 200, 300],
            }
        )

    @pytest.mark.parametrize(
        "expected_columns,expected_missing,expected_extra",
        [
            # Test case 1: Perfect match - no missing or extra columns
            (["id", "nome", "valor"], [], []),
            # Test case 2: Missing columns only
            (["id", "nome", "valor", "categoria"], ["categoria"], []),
            # Test case 3: Extra columns only
            (["id", "nome"], [], ["valor"]),
            # Test case 4: Both missing and extra columns
            (["id", "nome", "categoria", "status"], ["categoria", "status"], ["valor"]),
            # Test case 5: All columns missing
            (
                ["categoria", "status", "tipo"],
                ["categoria", "status", "tipo"],
                ["id", "nome", "valor"],
            ),
            # Test case 6: Empty expected columns list
            ([], [], ["id", "nome", "valor"]),
            # Test case 7: Single column match
            (["id"], [], ["nome", "valor"]),
            # Test case 8: Multiple missing columns
            (
                ["id", "nome", "valor", "cat1", "cat2", "cat3"],
                ["cat1", "cat2", "cat3"],
                [],
            ),
        ],
    )
    def test_check_column_names_with_simple_dataframe(
        self,
        simple_dataframe: pd.DataFrame,
        expected_columns: List[str],
        expected_missing: List[str],
        expected_extra: List[str],
    ) -> None:
        """Test check_column_names with various column combinations using simple DataFrame."""
        # Act
        missing_columns, extra_columns = check_column_names(simple_dataframe, expected_columns)

        # Assert
        assert missing_columns == expected_missing, f"Expected missing: {expected_missing}, got: {missing_columns}"
        assert extra_columns == expected_extra, f"Expected extra: {expected_extra}, got: {extra_columns}"
        assert isinstance(missing_columns, list), "Missing columns should be a list"
        assert isinstance(extra_columns, list), "Extra columns should be a list"

    @pytest.mark.parametrize(
        "expected_columns,expected_missing,expected_extra",
        [
            # Test case 1: Empty DataFrame with expected columns
            (["id", "nome"], ["id", "nome"], []),
            # Test case 2: Empty DataFrame with empty expected columns
            ([], [], []),
            # Test case 3: Empty DataFrame with single expected column
            (["categoria"], ["categoria"], []),
        ],
    )
    def test_check_column_names_with_empty_dataframe(
        self,
        empty_dataframe: pd.DataFrame,
        expected_columns: List[str],
        expected_missing: List[str],
        expected_extra: List[str],
    ) -> None:
        """Test check_column_names with empty DataFrame scenarios."""
        # Act
        missing_columns, extra_columns = check_column_names(empty_dataframe, expected_columns)

        # Assert
        assert missing_columns == expected_missing
        assert extra_columns == expected_extra
        assert len(extra_columns) == 0, "Empty DataFrame should have no extra columns"

    def test_check_column_names_filters_unnamed_columns(self, dataframe_with_unnamed_columns: pd.DataFrame) -> None:
        """Test that unnamed columns are properly filtered out from extra columns."""
        # Arrange
        expected_columns = ["id", "nome"]

        # Act
        missing_columns, extra_columns = check_column_names(dataframe_with_unnamed_columns, expected_columns)

        # Assert
        assert missing_columns == []
        assert extra_columns == [], "Unnamed columns should be filtered out"

        # Verify that unnamed columns are not in the result
        for col in extra_columns:
            assert not col.lower().startswith("unnamed"), f"Column {col} should be filtered out"

    @pytest.mark.parametrize(
        "unnamed_column_name",
        [
            "Unnamed: 0",
            "unnamed: 1",
            "UNNAMED: 2",
            "UnNaMeD: 3",
            "unnamed:4",
            "Unnamed:5",
        ],
    )
    def test_check_column_names_filters_various_unnamed_formats(self, unnamed_column_name: str) -> None:
        """Test that various formats of unnamed columns are filtered out."""
        # Arrange
        df = pd.DataFrame({"id": [1, 2, 3], unnamed_column_name: [10, 20, 30]})
        expected_columns = ["id"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == []
        assert extra_columns == [], f"Column '{unnamed_column_name}' should be filtered out"

    def test_check_column_names_case_sensitivity(self, dataframe_with_mixed_case_columns: pd.DataFrame) -> None:
        """Test that column name matching is case-sensitive."""
        # Arrange
        expected_columns = ["id", "nome", "valor"]  # lowercase

        # Act
        missing_columns, extra_columns = check_column_names(dataframe_with_mixed_case_columns, expected_columns)

        # Assert
        assert missing_columns == ["id", "nome", "valor"]
        assert set(extra_columns) == {"ID", "Nome", "VALOR", "codigo_pai"}

    def test_check_column_names_preserves_column_order(self) -> None:
        """Test that the order of missing columns matches the order in expected_columns."""
        # Arrange
        df = pd.DataFrame({"existing_col": [1, 2, 3]})
        expected_columns = ["col_a", "col_b", "existing_col", "col_c", "col_d"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == ["col_a", "col_b", "col_c", "col_d"]
        assert extra_columns == []

    def test_check_column_names_with_duplicate_expected_columns(self) -> None:
        """Test behavior with duplicate columns in expected_columns list."""
        # Arrange
        df = pd.DataFrame({"id": [1, 2, 3], "nome": ["A", "B", "C"]})
        expected_columns = ["id", "nome", "id", "valor"]  # 'id' appears twice

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == ["valor"], "Should only report 'valor' as missing once"
        assert extra_columns == []

    def test_check_column_names_with_special_characters(self) -> None:
        """Test with column names containing special characters."""
        # Arrange
        df = pd.DataFrame(
            {
                "código_pai": [1, 2, 3],
                "nome-simples": ["A", "B", "C"],
                "valor (%)": [10.5, 20.5, 30.5],
                "data/hora": ["2023-01-01", "2023-01-02", "2023-01-03"],
            }
        )
        expected_columns = ["código_pai", "nome-simples", "categoria"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == ["categoria"]
        assert set(extra_columns) == {"valor (%)", "data/hora"}

    def test_check_column_names_with_numeric_column_names(self) -> None:
        """Test with numeric column names (converted to strings)."""
        # Arrange
        df = pd.DataFrame({0: [1, 2, 3], 1: ["A", "B", "C"], "nome": ["X", "Y", "Z"]})
        expected_columns = [
            0,
            1,
        ]  # numeric columns as integers (how pandas stores them)

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == []
        assert extra_columns == ["nome"]

    def test_check_column_names_returns_correct_types(self) -> None:
        """Test that function returns correct types."""
        # Arrange
        df = pd.DataFrame({"test": [1, 2, 3]})
        expected_columns = ["test", "missing"]

        # Act
        result = check_column_names(df, expected_columns)

        # Assert
        assert isinstance(result, tuple), "Function should return a tuple"
        assert len(result) == 2, "Tuple should have exactly 2 elements"

        missing_columns, extra_columns = result
        assert isinstance(missing_columns, list), "First element should be a list"
        assert isinstance(extra_columns, list), "Second element should be a list"

    def test_check_column_names_with_large_dataframe(self) -> None:
        """Test performance and correctness with larger DataFrame."""
        # Arrange
        num_cols = 100
        df_columns = [f"col_{i}" for i in range(num_cols)]
        df = pd.DataFrame({col: range(10) for col in df_columns})

        expected_columns = [f"col_{i}" for i in range(0, num_cols, 2)]  # Even numbered columns
        expected_missing = [f"col_{i}" for i in range(1, num_cols, 2)]  # Odd numbered columns

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == []
        assert set(extra_columns) == set(expected_missing)

    @pytest.mark.parametrize(
        "df_data,expected_cols,should_have_missing,should_have_extra",
        [
            # Test case 1: Brazilian Portuguese column names
            (
                {"código": [1, 2], "descrição": ["A", "B"], "nível": [1, 2]},
                ["código", "descrição"],
                False,
                True,
            ),
            # Test case 2: Mixed language columns
            (
                {"id": [1, 2], "nome": ["A", "B"], "category": ["X", "Y"]},
                ["id", "nome", "categoria"],
                True,
                True,
            ),
            # Test case 3: Scientific data columns
            (
                {
                    "temperatura": [25.5, 26.0],
                    "umidade": [60, 65],
                    "pressão": [1013, 1015],
                },
                ["temperatura", "umidade", "pressão", "vento"],
                True,
                False,
            ),
        ],
    )
    def test_check_column_names_with_domain_specific_data(
        self,
        df_data: dict,
        expected_cols: List[str],
        should_have_missing: bool,
        should_have_extra: bool,
    ) -> None:
        """Test with domain-specific column names (environmental/scientific data)."""
        # Arrange
        df = pd.DataFrame(df_data)

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_cols)

        # Assert
        if should_have_missing:
            assert len(missing_columns) > 0, "Should have missing columns"
        else:
            assert len(missing_columns) == 0, "Should not have missing columns"

        if should_have_extra:
            assert len(extra_columns) > 0, "Should have extra columns"
        else:
            assert len(extra_columns) == 0, "Should not have extra columns"

    def test_check_column_names_edge_case_whitespace_columns(self) -> None:
        """Test with columns containing whitespace."""
        # Arrange
        df = pd.DataFrame({" id ": [1, 2, 3], "nome": ["A", "B", "C"], "  valor  ": [10, 20, 30]})
        expected_columns = ["id", "nome", "valor"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == ["id", "valor"]
        assert set(extra_columns) == {" id ", "  valor  "}

    def test_check_column_names_comprehensive_integration(self) -> None:
        """Comprehensive integration test combining multiple scenarios."""
        # Arrange - Complex DataFrame with various column types
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "código_pai": [100, 200, 300],
                "descrição": ["Desc A", "Desc B", "Desc C"],
                "valor (R$)": [10.50, 20.75, 30.25],
                "Unnamed: 0": [0, 1, 2],
                "unnamed: 5": [50, 60, 70],
                "UNNAMED: 10": [100, 200, 300],
                "categoria_extra": ["X", "Y", "Z"],
            }
        )

        expected_columns = ["id", "código_pai", "descrição", "nível", "status", "tipo"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        expected_missing = ["nível", "status", "tipo"]
        expected_extra = [
            "valor (R$)",
            "categoria_extra",
        ]  # Unnamed columns should be filtered

        assert missing_columns == expected_missing
        assert set(extra_columns) == set(expected_extra)

        # Verify unnamed columns are properly filtered
        for col in extra_columns:
            assert not col.lower().startswith("unnamed")


# Additional edge case tests
class TestCheckColumnNamesEdgeCases:
    """Additional edge case tests for check_column_names function."""

    def test_check_column_names_with_none_values(self) -> None:
        """Test that function handles None values appropriately."""
        # Note: This test verifies the function doesn't break with unexpected input
        # In a real scenario, you might want to add validation to handle None inputs
        df = pd.DataFrame({"test": [1, 2, 3]})

        with pytest.raises(TypeError):
            check_column_names(df, None)  # type: ignore

    def test_check_column_names_empty_string_columns(self) -> None:
        """Test with empty string column names."""
        # Arrange
        df = pd.DataFrame({"": [1, 2, 3], "nome": ["A", "B", "C"]})
        expected_columns = ["", "nome"]

        # Act
        missing_columns, extra_columns = check_column_names(df, expected_columns)

        # Assert
        assert missing_columns == []
        assert extra_columns == []

    def test_check_column_names_maintains_original_dataframe(self) -> None:
        """Test that the original DataFrame is not modified."""
        # Arrange
        original_data = {"id": [1, 2, 3], "nome": ["A", "B", "C"]}
        df = pd.DataFrame(original_data)
        original_columns = df.columns.tolist().copy()
        original_shape = df.shape

        # Act
        check_column_names(df, ["id", "nome", "extra"])

        # Assert
        assert df.columns.tolist() == original_columns, "Original DataFrame should not be modified"
        assert df.shape == original_shape, "DataFrame shape should not change"
        # Compare data more appropriately
        assert list(df["id"]) == original_data["id"], "ID column data should not be modified"
        assert list(df["nome"]) == original_data["nome"], "Nome column data should not be modified"
