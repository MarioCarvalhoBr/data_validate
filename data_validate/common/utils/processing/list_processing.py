import re

def categorize_strings_by_id_pattern(items_to_categorize, allowed_scenario_suffixes=None):
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
        scenario_pattern_id_year_suffix = re.compile(r"(?!)") # (?!) is a negative lookahead that always fails

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

def extract_numeric_ids_and_unmatched_strings(source_list=None, strings_to_ignore=None, scenario_suffixes_for_matching=None):
    """
    Extracts numeric IDs from a list of strings that match specific patterns
    and returns a list of strings that do not match or are not ignored.

    Args:
        source_list (list, optional): The list of source strings to process. Defaults to None (empty list).
        strings_to_ignore (list, optional): A list of strings to ignore from the unmatched items.
                                           Defaults to None (empty list).
        scenario_suffixes_for_matching (list, optional): A list of scenario suffixes used for pattern matching.
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
    if scenario_suffixes_for_matching is None:
        scenario_suffixes_for_matching = []

    # Convert strings_to_ignore items to strings and store in a set for efficient lookup
    set_of_strings_to_ignore = {str(item) for item in strings_to_ignore}

    # Categorize strings from the source_list based on patterns
    pattern_matched_strings, initially_unmatched_strings = categorize_strings_by_id_pattern(
        source_list,
        scenario_suffixes_for_matching
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

if __name__ == '__main__':
    # Example usage
    list_values = ['ID', 'ABABA', '18888-2020', '2-2021', '3-2022', '4-2023', '5-2024']
    list_ignore = ['ID']
    lista_cenarios = ['M', 'O', 'P']

    ids_valids, filtered_extras_columns = extract_numeric_ids_and_unmatched_strings(list_values, list_ignore, lista_cenarios)

    print("Valid IDs:", ids_valids)
    print("Filtered Extra Columns:", filtered_extras_columns)


    # TEste 2:
    list_values = ['id', '5000-2015', '5000-2080-M', '5000-2050-O', '5000-2030-P',
       '5000-2050-P', '5001-2015', '5002-2015', '5003-2015', '5003-2030-O',
       '5003-2050-O', '5003-2030-P', '5003-2050-P', '5004-2015', '5005-2015',
       '5006-2015', '5007-2015', '5008-2015', '5009-2015', '5010-2015',
       '5011-2015', '5012-2015', '5013-2015', '5014-2015', '5015-2017',
       '5016-2017', '5017-2017', '5018-2017']
    list_ignore = ['id']

    lista_cenarios = ['O', 'P','O']
    ids_valids, filtered_extras_columns = extract_numeric_ids_and_unmatched_strings(list_values, list_ignore, lista_cenarios)
    print("\n\n\nTeste 2: \nValid IDs:", ids_valids)
    print("Filtered Extra Columns:", filtered_extras_columns)