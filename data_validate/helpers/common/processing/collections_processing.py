#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for processing and analyzing collections of data.

This module defines the `CollectionsProcessing` class, which offers utility static
methods for grouping list elements, categorizing specific string patterns (like IDs),
extracting numeric identifiers, and comparing sets to find differences.
"""

import re
from typing import List, Set, Any, Tuple

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class CollectionsProcessing:
    """
    Utility class for processing collections (Lists, Sets) of data.

    Provides static methods for grouping, pattern extraction, ID validation,
    and set difference analysis commonly required in data validation logic.
    """

    def __init__(self) -> None:
        """Initialize the CollectionsProcessing class."""
        pass

    @staticmethod
    def generate_group_from_list(items: List) -> List[List]:
        """
        Group consecutive identical elements in a list.

        Iterates through the list and groups sequential items that are equal.

        Args:
            items (List): List of elements to group.

        Returns:
            List[List]: List of lists, where each sublist contains consecutive identical elements.

        Raises:
            ValueError: If the input list is empty.
        """
        if not items:
            raise ValueError("Input list must not be empty.")

        grouped: List[List] = []
        current_group: List = [items[0]]

        for element in items[1:]:
            if element == current_group[0]:
                current_group.append(element)
            else:
                grouped.append(current_group)
                current_group = [element]

        grouped.append(current_group)
        return grouped

    @staticmethod
    def categorize_strings_by_id_pattern_from_list(
        items_to_categorize: List[Any], allowed_scenario_suffixes: List[Any] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Categorizes a list of items (converted to strings) based on predefined ID patterns.

        Items can match a base 'ID-YEAR' pattern (e.g., '1-2020') or an extended
        'ID-YEAR-SCENARIO_SUFFIX' pattern (e.g., '1-2030-SSP1') if scenario suffixes are provided.

        Args:
            items_to_categorize (List[Any]): List of items to be categorized (converted to strings).
            allowed_scenario_suffixes (List[Any], optional): List of allowed scenario suffixes. Defaults to None.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing:
                - List[str]: Items matched by the pattern.
                - List[str]: Items NOT natural by the pattern.
        """
        if allowed_scenario_suffixes is None:
            allowed_scenario_suffixes = []

        base_pattern_id_year = re.compile(r"^\d{1,}-\d{4}$")

        if allowed_scenario_suffixes:
            escaped_suffixes = [re.escape(str(s)) for s in allowed_scenario_suffixes]
            scenario_pattern_id_year_suffix = re.compile(r"^\d{1,}-\d{4}-(?:" + "|".join(escaped_suffixes) + ")$")
        else:
            scenario_pattern_id_year_suffix = re.compile(r"(?!)")

        string_items_to_categorize = [str(item) for item in items_to_categorize]
        matched_by_pattern: List[str] = []
        not_matched_by_pattern: List[str] = []

        for current_item_str in string_items_to_categorize:
            if base_pattern_id_year.match(current_item_str):
                matched_by_pattern.append(current_item_str)
            elif allowed_scenario_suffixes and scenario_pattern_id_year_suffix.match(current_item_str):
                matched_by_pattern.append(current_item_str)
            else:
                not_matched_by_pattern.append(current_item_str)

        return matched_by_pattern, not_matched_by_pattern

    @staticmethod
    def extract_numeric_integer_ids_from_list(
        id_values_list: List[Any],
    ) -> Tuple[Set[int], Set[Any]]:
        """
        Extracts and categorizes valid and invalid IDs from a list of values.

        Valid IDs must be positive integers >= 1.

        Args:
            id_values_list (List[Any]): List of values to validate and categorize as IDs.

        Returns:
            Tuple[Set[int], Set[Any]]: A tuple containing:
                - Set[int]: Set of valid integer IDs.
                - Set[Any]: Set of invalid values found.
        """
        valid_ids: Set[int] = set()
        invalid_ids: Set[Any] = set()

        for value in id_values_list:
            is_valid, _ = NumberFormattingProcessing.check_cell_integer(value, 1)
            if is_valid:
                valid_ids.add(int(value))
            else:
                invalid_ids.add(value)
        return valid_ids, invalid_ids

    @staticmethod
    def extract_numeric_ids_and_unmatched_strings_from_list(
        source_list: List[Any] = None,
        strings_to_ignore: List[Any] = None,
        suffixes_for_matching: List[Any] = None,
    ) -> Tuple[Set[int], List[str]]:
        """
        Extracts numeric IDs from a list of strings that match specific patterns and returns a list of strings
        that do not match or are not ignored.

        First attempts to match items against 'ID-YEAR[-SCENARIO]' patterns to extract the ID part.
        Unmatched items are returned unless they are in the ignore list.

        Args:
            source_list (List[Any], optional): List of source strings to process. Defaults to None.
            strings_to_ignore (List[Any], optional): List of strings to exclude if unmatched. Defaults to None.
            suffixes_for_matching (List[Any], optional): List of scenario suffixes for pattern matching. Defaults to None.

        Returns:
            Tuple[Set[int], List[str]]: A tuple containing:
                - Set[int]: Set of unique integer IDs extracted from matched strings.
                - List[str]: List of unmatched strings that were not ignored.
        """
        if source_list is None:
            source_list = []
        if strings_to_ignore is None:
            strings_to_ignore = []
        if suffixes_for_matching is None:
            suffixes_for_matching = []

        set_of_strings_to_ignore = {str(item) for item in strings_to_ignore}
        pattern_matched_strings, initially_unmatched_strings = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            source_list, suffixes_for_matching
        )
        final_unmatched_strings = [unmatched_str for unmatched_str in initially_unmatched_strings if unmatched_str not in set_of_strings_to_ignore]
        extracted_numeric_ids = {int(matched_string.split("-", 1)[0]) for matched_string in pattern_matched_strings}
        return extracted_numeric_ids, final_unmatched_strings

    @staticmethod
    def find_differences_in_two_set(first_set: Set[Any], second_set: Set[Any]) -> Tuple[Set[Any], Set[Any]]:
        """
        Compares two sets and identifies missing elements in each set relative to the other.

        Args:
            first_set (Set[Any]): First set to compare.
            second_set (Set[Any]): Second set to compare.

        Returns:
            Tuple[Set[Any], Set[Any]]: A tuple containing:
                - Set[Any]: Elements present in first_set but MISSING in second_set.
                - Set[Any]: Elements present in second_set but MISSING in first_set.
        """
        if first_set is None:
            first_set = set()
        if second_set is None:
            second_set = set()
        missing_in_b = first_set - second_set
        missing_in_a = second_set - first_set
        return missing_in_b, missing_in_a

    @staticmethod
    def find_differences_in_two_set_with_message(first_set: Set[Any], label_1: str, second_set: Set[Any], label_2: str) -> List[str]:
        """
        Compares two sets and returns formatted error messages for missing elements.

        Wraps `find_differences_in_two_set` to generate human-readable error messages
        identifying which elements are missing from which set.

        Args:
            first_set (Set[Any]): First set to compare.
            label_1 (str): Label for the first set (for error messages).
            second_set (Set[Any]): Second set to compare.
            label_2 (str): Label for the second set (for error messages).

        Returns:
            List[str]: List of error strings describing the set differences found.
        """
        errors: List[str] = []
        if first_set is None:
            first_set = set()
        if second_set is None:
            second_set = set()
        missing_in_b, missing_in_a = CollectionsProcessing.find_differences_in_two_set(first_set, second_set)
        if missing_in_b:
            errors.append(f"{label_1}: Códigos dos indicadores ausentes em {label_2}: {sorted(list(missing_in_b))}.")
        if missing_in_a:
            errors.append(f"{label_2}: Códigos dos indicadores ausentes em {label_1}: {sorted(list(missing_in_a))}.")

        return errors
