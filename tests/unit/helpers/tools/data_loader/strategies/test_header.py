"""
Unit tests for header.py module.

This module tests the HeaderStrategy classes functionality including
single and double header strategies.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pytest
from pathlib import Path

from data_validate.helpers.tools.data_loader.strategies.header import HeaderStrategy, SingleHeaderStrategy, DoubleHeaderStrategy


class TestHeaderStrategy:
    """Test suite for HeaderStrategy abstract class."""

    def test_header_strategy_is_abstract(self, mocker) -> None:
        """Test that HeaderStrategy is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):  # type: ignore[misc]
            HeaderStrategy()  # type: ignore[abstract]

    def test_header_strategy_has_abstract_method(self, mocker) -> None:
        """Test that HeaderStrategy has abstract get_header method."""
        assert hasattr(HeaderStrategy, "get_header")
        assert getattr(HeaderStrategy.get_header, "__isabstractmethod__", False)


class TestSingleHeaderStrategy:
    """Test suite for SingleHeaderStrategy class."""

    def test_initialization(self, mocker) -> None:
        """Test SingleHeaderStrategy initialization."""
        strategy = SingleHeaderStrategy()
        assert isinstance(strategy, HeaderStrategy)

    def test_get_header_returns_zero(self, mocker) -> None:
        """Test that get_header returns 0 for single header."""
        strategy = SingleHeaderStrategy()
        file_path = Path("test.csv")

        result = strategy.get_header(file_path)

        assert result == 0

    def test_get_header_with_different_paths(self, mocker) -> None:
        """Test that get_header returns 0 regardless of file path."""
        strategy = SingleHeaderStrategy()

        paths = [Path("test.csv"), Path("test.xlsx"), Path("/absolute/path/test.csv"), Path("relative/path/test.xlsx")]

        for path in paths:
            result = strategy.get_header(path)
            assert result == 0

    def test_get_header_with_string_path(self, mocker) -> None:
        """Test get_header with string path."""
        strategy = SingleHeaderStrategy()
        file_path = "test.csv"

        result = strategy.get_header(file_path)

        assert result == 0

    def test_get_header_ignores_file_path(self, mocker) -> None:
        """Test that get_header ignores the file_path parameter."""
        strategy = SingleHeaderStrategy()

        # Should return 0 regardless of what file_path is
        assert strategy.get_header(None) == 0
        assert strategy.get_header("") == 0
        assert strategy.get_header(Path("any/path/file.csv")) == 0


class TestDoubleHeaderStrategy:
    """Test suite for DoubleHeaderStrategy class."""

    def test_initialization(self, mocker) -> None:
        """Test DoubleHeaderStrategy initialization."""
        strategy = DoubleHeaderStrategy()
        assert isinstance(strategy, HeaderStrategy)

    def test_get_header_returns_list(self, mocker) -> None:
        """Test that get_header returns [0, 1] for double header."""
        strategy = DoubleHeaderStrategy()
        file_path = Path("test.csv")

        result = strategy.get_header(file_path)

        assert result == [0, 1]

    def test_get_header_with_different_paths(self, mocker) -> None:
        """Test that get_header returns [0, 1] regardless of file path."""
        strategy = DoubleHeaderStrategy()

        paths = [Path("test.csv"), Path("test.xlsx"), Path("/absolute/path/test.csv"), Path("relative/path/test.xlsx")]

        for path in paths:
            result = strategy.get_header(path)
            assert result == [0, 1]

    def test_get_header_with_string_path(self, mocker) -> None:
        """Test get_header with string path."""
        strategy = DoubleHeaderStrategy()
        file_path = "test.csv"

        result = strategy.get_header(file_path)

        assert result == [0, 1]

    def test_get_header_ignores_file_path(self, mocker) -> None:
        """Test that get_header ignores the file_path parameter."""
        strategy = DoubleHeaderStrategy()

        # Should return [0, 1] regardless of what file_path is
        assert strategy.get_header(None) == [0, 1]
        assert strategy.get_header("") == [0, 1]
        assert strategy.get_header(Path("any/path/file.csv")) == [0, 1]

    def test_get_header_returns_correct_list_type(self, mocker) -> None:
        """Test that get_header returns a list with correct values."""
        strategy = DoubleHeaderStrategy()
        file_path = Path("test.csv")

        result = strategy.get_header(file_path)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == 0
        assert result[1] == 1


class TestHeaderStrategyIntegration:
    """Integration tests for header strategies."""

    def test_strategies_are_different(self, mocker) -> None:
        """Test that single and double header strategies return different values."""
        single_strategy = SingleHeaderStrategy()
        double_strategy = DoubleHeaderStrategy()
        file_path = Path("test.csv")

        single_result = single_strategy.get_header(file_path)
        double_result = double_strategy.get_header(file_path)

        assert single_result != double_result
        assert single_result == 0
        assert double_result == [0, 1]

    def test_strategies_are_consistent(self, mocker) -> None:
        """Test that strategies return consistent results across multiple calls."""
        single_strategy = SingleHeaderStrategy()
        double_strategy = DoubleHeaderStrategy()
        file_path = Path("test.csv")

        # Multiple calls should return the same result
        for _ in range(5):
            assert single_strategy.get_header(file_path) == 0
            assert double_strategy.get_header(file_path) == [0, 1]

    def test_strategies_with_pandas_compatibility(self, mocker) -> None:
        """Test that strategies return values compatible with pandas header parameter."""
        single_strategy = SingleHeaderStrategy()
        double_strategy = DoubleHeaderStrategy()
        file_path = Path("test.csv")

        single_result = single_strategy.get_header(file_path)
        double_result = double_strategy.get_header(file_path)

        # These should be valid header values for pandas.read_csv/read_excel
        assert isinstance(single_result, int)
        assert isinstance(double_result, list)
        assert all(isinstance(x, int) for x in double_result)
