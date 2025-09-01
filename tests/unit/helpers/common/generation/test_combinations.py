import pytest
from data_validate.helpers.common.generation.combinations import (
    generate_combinations,
    find_extra_combinations
)


class TestCombinations:
    """Test cases for combinations generation functions."""

    def test_generate_combinations_basic(self):
        """Test basic combination generation."""
        code = "TEST"
        start_year = 2020
        temporal_symbols = [2020, 2021, 2022]
        scenario_symbols = ["A", "B"]

        result = generate_combinations(code, start_year, temporal_symbols, scenario_symbols)

        expected = [
            "TEST-2020",
            "TEST-2021-A",
            "TEST-2021-B",
            "TEST-2022-A",
            "TEST-2022-B"
        ]
        assert result == expected

    def test_generate_combinations_single_year(self):
        """Test combination generation with single year."""
        code = "SINGLE"
        start_year = 2023
        temporal_symbols = [2023]
        scenario_symbols = ["X", "Y", "Z"]

        result = generate_combinations(code, start_year, temporal_symbols, scenario_symbols)

        expected = ["SINGLE-2023"]
        assert result == expected

    def test_generate_combinations_no_scenarios(self):
        """Test combination generation with no scenario symbols."""
        code = "NOSCEN"
        start_year = 2024
        temporal_symbols = [2024, 2025]
        scenario_symbols = []

        result = generate_combinations(code, start_year, temporal_symbols, scenario_symbols)

        expected = ["NOSCEN-2024"]
        assert result == expected

    def test_generate_combinations_empty_temporal(self):
        """Test combination generation with empty temporal symbols."""
        code = "EMPTY"
        start_year = 2025
        temporal_symbols = []
        scenario_symbols = ["A", "B"]

        result = generate_combinations(code, start_year, temporal_symbols, scenario_symbols)

        expected = ["EMPTY-2025"]
        assert result == expected

    def test_generate_combinations_string_symbols(self):
        """Test combination generation with string symbols."""
        code = "STR"
        start_year = 2026
        temporal_symbols = [2026, "2027", "2028"]
        scenario_symbols = ["SCEN1", "SCEN2"]

        result = generate_combinations(code, start_year, temporal_symbols, scenario_symbols)

        expected = [
            "STR-2026",
            "STR-2027-SCEN1",
            "STR-2027-SCEN2",
            "STR-2028-SCEN1",
            "STR-2028-SCEN2"
        ]
        assert result == expected

    def test_find_extra_combinations_no_extras(self):
        """Test finding extra combinations when none exist."""
        expected = ["TEST-2020", "TEST-2021-A", "TEST-2021-B"]
        actual = ["TEST-2020", "TEST-2021-A", "TEST-2021-B"]

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is False
        assert extras == []

    def test_find_extra_combinations_with_extras(self):
        """Test finding extra combinations when they exist."""
        expected = ["TEST-2020", "TEST-2021-A"]
        actual = ["TEST-2020", "TEST-2021-A", "TEST-2021-B", "TEST-2022-A"]

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is True
        assert set(extras) == {"TEST-2021-B", "TEST-2022-A"}

    def test_find_extra_combinations_empty_expected(self):
        """Test finding extra combinations with empty expected list."""
        expected = []
        actual = ["TEST-2020", "TEST-2021-A"]

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is True
        assert set(extras) == {"TEST-2020", "TEST-2021-A"}

    def test_find_extra_combinations_empty_actual(self):
        """Test finding extra combinations with empty actual list."""
        expected = ["TEST-2020", "TEST-2021-A"]
        actual = []

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is False
        assert extras == []

    def test_find_extra_combinations_both_empty(self):
        """Test finding extra combinations with both lists empty."""
        expected = []
        actual = []

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is False
        assert extras == []

    def test_find_extra_combinations_duplicates_in_actual(self):
        """Test finding extra combinations with duplicates in actual list."""
        expected = ["TEST-2020", "TEST-2021-A"]
        actual = ["TEST-2020", "TEST-2021-A", "TEST-2021-A", "TEST-2022-B"]

        has_extras, extras = find_extra_combinations(expected, actual)

        assert has_extras is True
        assert extras == ["TEST-2022-B"] 