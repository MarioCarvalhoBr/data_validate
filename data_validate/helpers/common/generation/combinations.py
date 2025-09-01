from typing import List, Tuple, Any


def generate_combinations(
    code: str, start_year: int, temporal_symbols: List[Any], scenario_symbols: List[Any]
) -> List[str]:
    """
    Generate combinations using the base code, start year, temporal symbols, and scenario symbols.

    Args:
        code: Base code for combinations.
        start_year: Initial year for combinations.
        temporal_symbols: List of temporal symbols.
        scenario_symbols: List of scenario symbols.

    Returns:
        List of generated combinations in the format 'code-year-scenario'.
    """
    combinations = [f"{code}-{start_year}"]
    for year in temporal_symbols[1:]:
        for symbol in scenario_symbols:
            combinations.append(f"{code}-{year}-{symbol}")
    return combinations


def find_extra_combinations(
    expected_combinations: List[str], actual_combinations: List[str]
) -> Tuple[bool, List[str]]:
    """
    Find extra combinations present in actual_combinations but not in expected_combinations.

    Args:
        expected_combinations: List of expected combinations.
        actual_combinations: List of actual combinations.

    Returns:
        Tuple with a boolean indicating if extras exist and a list of extra combinations.
    """
    extras = list(set(actual_combinations) - set(expected_combinations))
    return bool(extras), extras
