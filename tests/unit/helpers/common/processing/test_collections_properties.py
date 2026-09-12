#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Property-based tests for collections_processing.py (TST-005).

Uses `hypothesis` to explore `CollectionsProcessing.categorize_strings_by_id_pattern_from_list`
and `extract_numeric_ids_and_unmatched_strings_from_list` over the
`CÓDIGO-ANO[-CENÁRIO]` id-pattern input space, including scenario suffixes that
contain regex-special characters.
"""

from collections import Counter

from hypothesis import given, settings, strategies as st

from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing

# Suffixes intentionally include regex-special characters (`+`, `(`, `)`, `.`, `*`) to
# prove `categorize_strings_by_id_pattern_from_list` escapes them via `re.escape`.
SCENARIO_SUFFIXES = ["A", "B", "P+", "SSP1", "O(1)", "R.5", "X*"]

ID_STRATEGY = st.integers(min_value=0, max_value=999_999)
YEAR_STRATEGY = st.integers(min_value=1000, max_value=9999)
SUFFIX_STRATEGY = st.sampled_from(SCENARIO_SUFFIXES)


class TestCategorizeMatchesValidIdYearPattern:
    """Strings shaped like `ID-YEAR` always match, with or without suffixes configured."""

    @given(item_id=ID_STRATEGY, year=YEAR_STRATEGY)
    @settings(max_examples=200, deadline=None)
    def test_id_year_always_matches(self, item_id: int, year: int) -> None:
        """A bare `ID-YEAR` string matches regardless of allowed suffixes."""
        item = f"{item_id}-{year}"
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list([item], SCENARIO_SUFFIXES)
        assert matched == [item]
        assert unmatched == []

    @given(item_id=ID_STRATEGY, year=YEAR_STRATEGY, suffix=SUFFIX_STRATEGY)
    @settings(max_examples=200, deadline=None)
    def test_id_year_suffix_matches_when_suffix_is_allowed(self, item_id: int, year: int, suffix: str) -> None:
        """`ID-YEAR-SUFFIX` matches when SUFFIX is in the allowed list, including regex-special suffixes."""
        item = f"{item_id}-{year}-{suffix}"
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list([item], SCENARIO_SUFFIXES)
        assert matched == [item]
        assert unmatched == []


class TestCategorizeRejectsWrongShapes:
    """Strings that do not conform to either accepted shape never match."""

    @given(item_id=ID_STRATEGY, year=YEAR_STRATEGY, suffix=SUFFIX_STRATEGY)
    @settings(max_examples=200, deadline=None)
    def test_suffix_not_in_allowed_list_never_matches(self, item_id: int, year: int, suffix: str) -> None:
        """A suffix outside the allowed list is rejected."""
        item = f"{item_id}-{year}-{suffix}"
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list([item], [])
        assert matched == []
        assert unmatched == [item]

    @given(item_id=ID_STRATEGY, year=st.integers(min_value=0, max_value=999).filter(lambda y: y < 1000))
    @settings(max_examples=200, deadline=None)
    def test_year_shorter_than_four_digits_never_matches(self, item_id: int, year: int) -> None:
        """A year with fewer than 4 digits breaks the base pattern."""
        item = f"{item_id}-{year}"
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list([item], SCENARIO_SUFFIXES)
        assert matched == []
        assert unmatched == [item]

    @given(item_id=ID_STRATEGY, year=YEAR_STRATEGY)
    @settings(max_examples=200, deadline=None)
    def test_missing_separator_never_matches(self, item_id: int, year: int) -> None:
        """A string with no '-' separator (concatenated id+year) never matches."""
        item = f"{item_id}{year}"
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list([item], SCENARIO_SUFFIXES)
        assert matched == []
        assert unmatched == [item]


class TestCategorizePartitionsInput:
    """matched + unmatched must always be a permutation of the input."""

    @given(
        items=st.lists(
            st.one_of(
                st.builds(lambda i, y: f"{i}-{y}", ID_STRATEGY, YEAR_STRATEGY),
                st.builds(lambda i, y, s: f"{i}-{y}-{s}", ID_STRATEGY, YEAR_STRATEGY, SUFFIX_STRATEGY),
                st.text(alphabet="abcXYZ-0123456789", min_size=0, max_size=6),
            ),
            min_size=0,
            max_size=25,
        )
    )
    @settings(max_examples=200, deadline=None)
    def test_matched_and_unmatched_partition_the_input(self, items: list) -> None:
        """The union (as a multiset) of matched and unmatched equals the input strings."""
        matched, unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(items, SCENARIO_SUFFIXES)
        assert Counter(matched) + Counter(unmatched) == Counter(str(item) for item in items)


class TestExtractNumericIdsMatchesCategorization:
    """`extract_numeric_ids_and_unmatched_strings_from_list` ids must equal matched ids."""

    @given(
        items=st.lists(
            st.one_of(
                st.builds(lambda i, y: f"{i}-{y}", ID_STRATEGY, YEAR_STRATEGY),
                st.builds(lambda i, y, s: f"{i}-{y}-{s}", ID_STRATEGY, YEAR_STRATEGY, SUFFIX_STRATEGY),
                st.text(alphabet="abcXYZ-0123456789", min_size=0, max_size=6),
            ),
            min_size=0,
            max_size=25,
        )
    )
    @settings(max_examples=200, deadline=None)
    def test_extracted_ids_equal_ids_of_matched_subset(self, items: list) -> None:
        """Extracted numeric ids equal the ids parsed from the matched (categorized) subset."""
        matched, _ = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(items, SCENARIO_SUFFIXES)
        expected_ids = {int(entry.split("-", 1)[0]) for entry in matched}

        extracted_ids, _ = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
            items, strings_to_ignore=[], suffixes_for_matching=SCENARIO_SUFFIXES
        )

        assert extracted_ids == expected_ids
