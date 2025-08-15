import re
from typing import List, Set

from common.utils.formatting.number_formatting import check_cell_integer


def categorize_strings_by_id_pattern_from_list(items_to_categorize, allowed_scenario_suffixes=None):
    """
    Categorizes a list of items (converted to strings) based on predefined ID patterns.

    Items can match a base 'ID-YEAR' pattern or an extended 'ID-YEAR-SCENARIO_SUFFIX' pattern
    if scenario suffixes are provided.

    Args:
        items_to_categorize (list): A list of items to be categorized.
                                   Items will be converted to strings.
        allowed_scenario_suffixes (list, optional): A list of allowed scenario suffixes.
                                                   Defaults to None, meaning no scenario pattern matching.

    Returns:
        tuple: A tuple containing two lists:
            - matched_by_pattern (list): Items that matched one of the ID patterns.
            - not_matched_by_pattern (list): Items that did not match any ID pattern.
    """
    if allowed_scenario_suffixes is None:
        allowed_scenario_suffixes = []

    base_pattern_id_year = re.compile(r"^\d{1,}-\d{4}$")

    # Compile scenario pattern only if scenario suffixes are provided
    if allowed_scenario_suffixes:
        # Ensure all scenario suffixes are strings for re.escape and join
        escaped_suffixes = [re.escape(str(s)) for s in allowed_scenario_suffixes]
        scenario_pattern_id_year_suffix = re.compile(r'^\d{1,}-\d{4}-(?:' + '|'.join(escaped_suffixes) + ')$')
    else:
        # Create a regex that matches nothing if no scenario suffixes are provided
        scenario_pattern_id_year_suffix = re.compile(r"(?!)")  # (?!) is a negative lookahead that always fails

    # Convert all input items to strings
    string_items_to_categorize = [str(item) for item in items_to_categorize]

    matched_by_pattern = []
    not_matched_by_pattern = []

    for current_item_str in string_items_to_categorize:
        # Check against basic ID-Year pattern first
        if base_pattern_id_year.match(current_item_str):
            matched_by_pattern.append(current_item_str)
        # Then, if scenarios are provided, check against ID-Year-Scenario pattern
        elif allowed_scenario_suffixes and scenario_pattern_id_year_suffix.match(current_item_str):
            matched_by_pattern.append(current_item_str)
        # If neither pattern matches, it's an unmatched item
        else:
            not_matched_by_pattern.append(current_item_str)

    return matched_by_pattern, not_matched_by_pattern


def extract_numeric_integer_ids_from_list(id_values_list):
    """
    Extract and categorize valid and invalid IDs from a list of values.

    Validates each value as a numeric ID and separates them into valid integers
    and invalid values that couldn't be processed.

    Args:
        id_values_list: List of values to validate and categorize as IDs

    Returns:
        tuple: (valid_ids_set, invalid_ids_set) where:
            - valid_ids_set: Set of valid integer IDs
            - invalid_ids_set: Set of invalid values that couldn't be converted
    """
    valid_ids = set()
    invalid_ids = set()

    for value in id_values_list:
        is_valid, _ = check_cell_integer(value, 1)

        if is_valid:
            valid_ids.add(int(value))
        else:
            invalid_ids.add(value)

    return valid_ids, invalid_ids


def extract_numeric_ids_and_unmatched_strings_from_list(source_list=None, strings_to_ignore=None,
                                                        suffixes_for_matching=None):
    """
    Extracts numeric IDs from a list of strings that match specific patterns
    and returns a list of strings that do not match or are not ignored.

    Args:
        source_list (list, optional): The list of source strings to process. Defaults to None (empty list).
        strings_to_ignore (list, optional): A list of strings to ignore from the unmatched items.
                                           Defaults to None (empty list).
        suffixes_for_matching (list, optional): A list of scenario suffixes used for pattern matching.
                                                       Defaults to None (empty list).

    Returns:
        tuple: A tuple containing:
            - extracted_numeric_ids (set): A set of unique integer IDs extracted from pattern-matched strings.
            - final_unmatched_strings (list): A list of strings that did not match patterns and are not in strings_to_ignore.
    """
    if source_list is None:
        source_list = []
    if strings_to_ignore is None:
        strings_to_ignore = []
    if suffixes_for_matching is None:
        suffixes_for_matching = []

    # Convert strings_to_ignore items to strings and store in a set for efficient lookup
    set_of_strings_to_ignore = {str(item) for item in strings_to_ignore}

    # Categorize strings from the source_list based on patterns
    pattern_matched_strings, initially_unmatched_strings = categorize_strings_by_id_pattern_from_list(
        source_list,
        suffixes_for_matching
    )

    # Filter initially_unmatched_strings based on the set_of_strings_to_ignore
    final_unmatched_strings = [
        unmatched_str for unmatched_str in initially_unmatched_strings if unmatched_str not in set_of_strings_to_ignore
    ]

    # Extract unique integer IDs from the 'ID' part of pattern_matched_strings
    # e.g., "123-2023" -> 123, "45-2024-SCN" -> 45
    # The regex in categorize_strings_by_id_pattern ensures `matched_string.split('-', 1)[0]` is a number.
    extracted_numeric_ids = {
        int(matched_string.split('-', 1)[0]) for matched_string in pattern_matched_strings
    }

    return extracted_numeric_ids, final_unmatched_strings

def find_differences_in_two_set(first_set: Set, label_1: str, second_set: Set, label_2: str) -> List[str]:
    """
    Compares two sets and identifies missing elements in each set.

    Args:
        first_set (set): First set to compare
        second_set (set): Second set to compare
        label_1 (str): Label for the first set (used in error messages)
        label_2 (str): Label for the second set (used in error messages)

    Returns:
        list: List of error messages describing missing elements in each set
    """
    errors = []

    if first_set is None:
        first_set = []
    if second_set is None:
        second_set = []

    # Elements in set_a but not in set_b
    missing_in_b = first_set - second_set
    if missing_in_b:
        errors.append(
            f"{label_1}: Códigos dos indicadores ausentes em {label_2}: {sorted(list(missing_in_b))}."
        )

    # Elements in set_b but not in set_a
    missing_in_a = second_set - first_set
    if missing_in_a:
        errors.append(
            f"{label_2}: Códigos dos indicadores ausentes emn {label_1}: {sorted(list(missing_in_a))}."
        )

    return errors