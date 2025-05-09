def generate_combinations(code, start_year, temporal_symbols, scenario_symbols):
    """
    Generates a list of combinations based on the provided code, start year, temporal symbols, and scenario symbols.

    Args:
        code (str): The base code to be used in the combinations.
        start_year (int): The starting year for the combinations.
        temporal_symbols (list): A list of temporal symbols (e.g., years).
        scenario_symbols (list): A list of scenario symbols.

    Returns:
        list: A list of generated combinations in the format `code-year-scenario`.

    Example:
        >>> generate_combinations("ABC", 2023, [2023, 2024], ["X", "Y"])
        ['ABC-2023', 'ABC-2024-X', 'ABC-2024-Y']
    """
    combinations = [f"{code}-{start_year}"]

    # Skip the first temporal symbol
    for year in temporal_symbols[1:]:
        for symbol in scenario_symbols:
            combinations.append(f"{code}-{year}-{symbol}")

    return combinations