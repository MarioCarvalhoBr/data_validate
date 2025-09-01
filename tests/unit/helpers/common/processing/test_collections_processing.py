import pytest
from data_validate.helpers.common.processing.collections_processing import (
    categorize_strings_by_id_pattern_from_list,
    extract_numeric_integer_ids_from_list,
    extract_numeric_ids_and_unmatched_strings_from_list,
    find_differences_in_two_set,
    find_differences_in_two_set_with_message
)


class TestCollectionsProcessing:
    """Test cases for collections processing functions."""

    def test_categorize_strings_by_id_pattern_from_list_basic(self):
        """Test basic categorization of strings by ID pattern."""
        items = ["1-2020", "2-2021", "invalid", "3-2022"]
        allowed_suffixes = ["A", "B"]
        
        matched, not_matched = categorize_strings_by_id_pattern_from_list(items, allowed_suffixes)
        
        assert set(matched) == {"1-2020", "2-2021", "3-2022"}
        assert set(not_matched) == {"invalid"}

    def test_categorize_strings_by_id_pattern_from_list_with_scenarios(self):
        """Test categorization with scenario suffixes."""
        items = ["1-2020", "2-2021-A", "3-2022-B", "4-2023-C", "invalid"]
        allowed_suffixes = ["A", "B"]
        
        matched, not_matched = categorize_strings_by_id_pattern_from_list(items, allowed_suffixes)
        
        assert set(matched) == {"1-2020", "2-2021-A", "3-2022-B"}
        assert set(not_matched) == {"4-2023-C", "invalid"}

    def test_categorize_strings_by_id_pattern_from_list_no_suffixes(self):
        """Test categorization without scenario suffixes."""
        items = ["1-2020", "2-2021-A", "3-2022-B", "invalid"]
        allowed_suffixes = None
        
        matched, not_matched = categorize_strings_by_id_pattern_from_list(items, allowed_suffixes)
        
        assert set(matched) == {"1-2020"}
        assert set(not_matched) == {"2-2021-A", "3-2022-B", "invalid"}

    def test_categorize_strings_by_id_pattern_from_list_empty_suffixes(self):
        """Test categorization with empty scenario suffixes."""
        items = ["1-2020", "2-2021-A", "3-2022-B", "invalid"]
        allowed_suffixes = []
        
        matched, not_matched = categorize_strings_by_id_pattern_from_list(items, allowed_suffixes)
        
        assert set(matched) == {"1-2020"}
        assert set(not_matched) == {"2-2021-A", "3-2022-B", "invalid"}

    def test_categorize_strings_by_id_pattern_from_list_mixed_types(self):
        """Test categorization with mixed data types."""
        items = [1, "2-2021", 3, "4-2022-A", "invalid"]
        allowed_suffixes = ["A"]
        
        matched, not_matched = categorize_strings_by_id_pattern_from_list(items, allowed_suffixes)
        
        assert set(matched) == {"2-2021", "4-2022-A"}
        assert set(not_matched) == {"1", "3", "invalid"}

    def test_extract_numeric_integer_ids_from_list_valid_ids(self):
        """Test extracting valid integer IDs from list."""
        id_values = [1, "2", 3, "4", 5]
        
        valid_ids, invalid_ids = extract_numeric_integer_ids_from_list(id_values)
        
        assert valid_ids == {1, 2, 3, 4, 5}
        assert invalid_ids == set()

    def test_extract_numeric_integer_ids_from_list_invalid_ids(self):
        """Test extracting IDs with invalid values."""
        id_values = [1, "invalid", 3, "not_a_number", 5]
        
        valid_ids, invalid_ids = extract_numeric_integer_ids_from_list(id_values)
        
        assert valid_ids == {1, 3, 5}
        assert invalid_ids == {"invalid", "not_a_number"}

    def test_extract_numeric_integer_ids_from_list_with_min_value(self):
        """Test extracting IDs with minimum value constraint."""
        id_values = [1, 2, 3, 4, 5]
        
        valid_ids, invalid_ids = extract_numeric_integer_ids_from_list(id_values)
        
        assert valid_ids == {1, 2, 3, 4, 5}
        assert invalid_ids == set()

    def test_extract_numeric_integer_ids_from_list_empty(self):
        """Test extracting IDs from empty list."""
        id_values = []
        
        valid_ids, invalid_ids = extract_numeric_integer_ids_from_list(id_values)
        
        assert valid_ids == set()
        assert invalid_ids == set()

    def test_extract_numeric_ids_and_unmatched_strings_from_list_basic(self):
        """Test basic extraction of numeric IDs and unmatched strings."""
        source_list = ["1-2020", "2-2021", "invalid", "3-2022"]
        strings_to_ignore = ["ignore_this"]
        suffixes_for_matching = ["A", "B"]
        
        numeric_ids, unmatched = extract_numeric_ids_and_unmatched_strings_from_list(
            source_list, strings_to_ignore, suffixes_for_matching
        )
        
        assert numeric_ids == {1, 2, 3}
        assert set(unmatched) == {"invalid"}

    def test_extract_numeric_ids_and_unmatched_strings_from_list_with_ignored(self):
        """Test extraction with strings to ignore."""
        source_list = ["1-2020", "2-2021", "ignore_this", "3-2022"]
        strings_to_ignore = ["ignore_this"]
        suffixes_for_matching = ["A", "B"]
        
        numeric_ids, unmatched = extract_numeric_ids_and_unmatched_strings_from_list(
            source_list, strings_to_ignore, suffixes_for_matching
        )
        
        assert numeric_ids == {1, 2, 3}
        assert set(unmatched) == set()  # All unmatched are ignored

    def test_extract_numeric_ids_and_unmatched_strings_from_list_none_values(self):
        """Test extraction with None values (defaults)."""
        numeric_ids, unmatched = extract_numeric_ids_and_unmatched_strings_from_list()
        
        assert numeric_ids == set()
        assert unmatched == []

    def test_extract_numeric_ids_and_unmatched_strings_from_list_mixed_patterns(self):
        """Test extraction with mixed ID patterns."""
        source_list = ["1-2020", "2-2021-A", "3-2022-B", "4-2023", "invalid"]
        strings_to_ignore = []
        suffixes_for_matching = ["A", "B"]
        
        numeric_ids, unmatched = extract_numeric_ids_and_unmatched_strings_from_list(
            source_list, strings_to_ignore, suffixes_for_matching
        )
        
        assert numeric_ids == {1, 2, 3, 4}
        assert set(unmatched) == {"invalid"}

    def test_find_differences_in_two_set_basic(self):
        """Test finding differences between two sets."""
        set_a = {1, 2, 3, 4}
        set_b = {3, 4, 5, 6}
        
        missing_in_b, missing_in_a = find_differences_in_two_set(set_a, set_b)
        
        assert missing_in_b == {1, 2}
        assert missing_in_a == {5, 6}

    def test_find_differences_in_two_set_no_differences(self):
        """Test finding differences when sets are identical."""
        set_a = {1, 2, 3, 4}
        set_b = {1, 2, 3, 4}
        
        missing_in_b, missing_in_a = find_differences_in_two_set(set_a, set_b)
        
        assert missing_in_b == set()
        assert missing_in_a == set()

    def test_find_differences_in_two_set_one_empty(self):
        """Test finding differences when one set is empty."""
        set_a = {1, 2, 3, 4}
        set_b = set()
        
        missing_in_b, missing_in_a = find_differences_in_two_set(set_a, set_b)
        
        assert missing_in_b == {1, 2, 3, 4}
        assert missing_in_a == set()

    def test_find_differences_in_two_set_both_empty(self):
        """Test finding differences when both sets are empty."""
        set_a = set()
        set_b = set()
        
        missing_in_b, missing_in_a = find_differences_in_two_set(set_a, set_b)
        
        assert missing_in_b == set()
        assert missing_in_a == set()

    def test_find_differences_in_two_set_none_values(self):
        """Test finding differences with None values."""
        missing_in_b, missing_in_a = find_differences_in_two_set(None, None)
        
        assert missing_in_b == set()
        assert missing_in_a == set()

    def test_find_differences_in_two_set_with_message_basic(self):
        """Test finding differences with error messages."""
        set_a = {1, 2, 3, 4}
        set_b = {3, 4, 5, 6}
        label_1 = "File A"
        label_2 = "File B"
        
        errors = find_differences_in_two_set_with_message(set_a, label_1, set_b, label_2)
        
        assert len(errors) == 2
        assert "File A: Códigos dos indicadores ausentes em File B" in errors[0]
        assert "File B: Códigos dos indicadores ausentes em File A" in errors[1]

    def test_find_differences_in_two_set_with_message_no_differences(self):
        """Test finding differences with messages when no differences exist."""
        set_a = {1, 2, 3, 4}
        set_b = {1, 2, 3, 4}
        label_1 = "File A"
        label_2 = "File B"
        
        errors = find_differences_in_two_set_with_message(set_a, label_1, set_b, label_2)
        
        assert len(errors) == 0

    def test_find_differences_in_two_set_with_message_one_difference(self):
        """Test finding differences with messages when only one set has missing items."""
        set_a = {1, 2, 3, 4}
        set_b = {1, 2, 3, 4, 5, 6}
        label_1 = "File A"
        label_2 = "File B"
        
        errors = find_differences_in_two_set_with_message(set_a, label_1, set_b, label_2)
        
        assert len(errors) == 1
        assert "File B: Códigos dos indicadores ausentes em File A" in errors[0]

    def test_find_differences_in_two_set_with_message_none_values(self):
        """Test finding differences with messages when sets are None."""
        label_1 = "File A"
        label_2 = "File B"
        
        errors = find_differences_in_two_set_with_message(None, label_1, None, label_2)
        
        assert len(errors) == 0

    def test_find_differences_in_two_set_with_message_empty_sets(self):
        """Test finding differences with messages when sets are empty."""
        set_a = set()
        set_b = set()
        label_1 = "File A"
        label_2 = "File B"
        
        errors = find_differences_in_two_set_with_message(set_a, label_1, set_b, label_2)
        
        assert len(errors) == 0 