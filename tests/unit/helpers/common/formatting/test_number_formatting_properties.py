#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Property-based tests for number_formatting_processing.py (TST-005).

Uses `hypothesis` to explore the input space of `NumberFormattingProcessing`
static methods: integer-cell acceptance across textual representations,
truncation robustness/idempotency, decimal-place checking, and numeric
parsing round-trips.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing

# Letters-only alphabet guarantees a string can never be interpreted as a
# number (no digits, signs, "e"/"E" exponent marker ambiguity aside -- a
# lone "e"/"inf"/"nan" still fails float() or is caught by is_nan()).
NON_NUMERIC_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class TestCheckCellIntegerAcceptsIntegerRepresentations:
    """`check_cell_integer` must accept every textual shape of a valid integer."""

    @given(n=st.integers(min_value=0, max_value=10**9))
    @settings(max_examples=200, deadline=None)
    def test_check_cell_integer_accepts_all_string_representations(self, n: int) -> None:
        """str(n), f'{n}.0', padded, and comma-decimal representations are all accepted."""
        for representation in (str(n), f"{n}.0", f" {n} ", f"{n},0"):
            valid, message = NumberFormattingProcessing.check_cell_integer(representation)
            assert valid is True, f"expected {representation!r} to be accepted, got message={message!r}"
            assert message == ""

    @given(
        n=st.integers(min_value=-10_000, max_value=10_000), min_value=st.integers(min_value=-10_000, max_value=10_000)
    )
    @settings(max_examples=200, deadline=None)
    def test_check_cell_integer_respects_min_value_boundary(self, n: int, min_value: int) -> None:
        """Any integer >= min_value is accepted; any integer < min_value is rejected."""
        valid, message = NumberFormattingProcessing.check_cell_integer(n, min_value=min_value)
        if n >= min_value:
            assert valid is True
            assert message == ""
        else:
            assert valid is False
            assert message != ""

    @given(text=st.text(alphabet=NON_NUMERIC_ALPHABET, min_size=1, max_size=20))
    @settings(max_examples=200, deadline=None)
    def test_check_cell_integer_rejects_non_numeric_text_without_raising(self, text: str) -> None:
        """Arbitrary non-numeric text is rejected with a message and never raises."""
        valid, message = NumberFormattingProcessing.check_cell_integer(text)
        assert valid is False
        assert "não é um número" in message


class TestToDecimalTruncated:
    """`to_decimal_truncated` must be total (never raise) and idempotent."""

    @given(
        value=st.one_of(
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
            st.text(),
            st.none(),
        ),
        precision=st.integers(min_value=0, max_value=6),
    )
    @settings(max_examples=200, deadline=None)
    def test_to_decimal_truncated_never_raises(self, value, precision: int) -> None:
        """Any value/precision combination returns a Decimal, never raises."""
        result = NumberFormattingProcessing.to_decimal_truncated(value, "DI", precision)
        assert isinstance(result, Decimal)

    # str() on a float only ever falls back to scientific notation ("1e-05")
    # once its magnitude drops below 1e-4 (or grows past ~1e16); `to_decimal_truncated`
    # only truncates when a literal "." is present in `str(value_number)`, so those
    # magnitudes are a distinct, documented bug candidate (see
    # `test_to_decimal_truncated_scientific_notation_bug_candidate` below) and are
    # excluded from the "normal" properties to keep those properties meaningful.
    NORMAL_MAGNITUDE_FLOATS = st.floats(
        min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False
    ).filter(lambda v: v == 0 or abs(v) >= 1e-4)

    @given(value=NORMAL_MAGNITUDE_FLOATS, precision=st.integers(min_value=0, max_value=6))
    @settings(max_examples=200, deadline=None)
    def test_to_decimal_truncated_is_idempotent(self, value: float, precision: int) -> None:
        """Truncating an already-truncated value returns the same Decimal."""
        truncated_once = NumberFormattingProcessing.to_decimal_truncated(value, "DI", precision)
        truncated_twice = NumberFormattingProcessing.to_decimal_truncated(str(truncated_once), "DI", precision)
        assert truncated_twice == truncated_once

    @given(value=NORMAL_MAGNITUDE_FLOATS, precision=st.integers(min_value=0, max_value=6))
    @settings(max_examples=200, deadline=None)
    def test_truncated_value_never_exceeds_requested_decimal_places(self, value: float, precision: int) -> None:
        """A value truncated to `precision` decimals never reports more than `precision` decimals."""
        truncated = NumberFormattingProcessing.to_decimal_truncated(value, "DI", precision)
        assert NumberFormattingProcessing.check_n_decimals_places(truncated, "DI", precision) is False

    @given(value_to_ignore=st.text(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_to_decimal_truncated_ignores_the_sentinel_value(self, value_to_ignore: str) -> None:
        """The configured sentinel ('DI'-like) value always truncates to zero."""
        result = NumberFormattingProcessing.to_decimal_truncated(value_to_ignore, value_to_ignore, 2)
        assert result == Decimal("0")

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "BUG candidate (TST-005 property finding): to_decimal_truncated() truncates by "
            "string-splitting on a literal '.', so any value whose str() representation uses "
            "scientific notation with no fractional mantissa digit (abs(value) < 1e-4, e.g. "
            "str(1e-05) == '1e-05', no '.') skips truncation entirely -- "
            "to_decimal_truncated(1e-05, 'DI', 0) returns Decimal('0.00001') instead of Decimal('0'). "
            "Used by proportionality_processing.py on real (unbounded) float weights, so a very "
            "small proportionality value silently bypasses the precision truncation. "
            "Repro: NumberFormattingProcessing.to_decimal_truncated(1e-05, 'DI', 0)."
        ),
    )
    @pytest.mark.parametrize(
        "value, precision",
        [
            (1e-05, 0),
            (2e-05, 2),
            (5e-06, 4),
            (9e-05, 1),
            (1e-06, 0),
        ],
    )
    def test_to_decimal_truncated_scientific_notation_bug_candidate(self, value: float, precision: int) -> None:
        """Values whose str() uses scientific notation are silently not truncated (bug)."""
        truncated = NumberFormattingProcessing.to_decimal_truncated(value, "DI", precision)
        assert NumberFormattingProcessing.check_n_decimals_places(truncated, "DI", precision) is False


class TestParseNumeric:
    """`parse_numeric` must round-trip floats and never raise on arbitrary text."""

    @given(value=st.floats(min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=None)
    def test_parse_numeric_roundtrips_float_via_str(self, value: float) -> None:
        """str(value) parses back to (True, value) within a tight tolerance."""
        ok, parsed = NumberFormattingProcessing.parse_numeric(str(value))
        assert ok is True
        assert parsed == pytest.approx(value, rel=1e-9, abs=1e-9)

    @given(value=st.floats(min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200, deadline=None)
    def test_parse_numeric_roundtrips_comma_decimal_representation(self, value: float) -> None:
        """A comma-decimal string representation parses to the same float."""
        comma_representation = str(value).replace(".", ",")
        ok, parsed = NumberFormattingProcessing.parse_numeric(comma_representation)
        assert ok is True
        assert parsed == pytest.approx(value, rel=1e-9, abs=1e-9)

    @given(text=st.text(max_size=30))
    @settings(max_examples=200, deadline=None)
    def test_parse_numeric_never_raises_on_arbitrary_text(self, text: str) -> None:
        """Arbitrary text never raises; failure is reported as (False, 0.0)."""
        ok, parsed = NumberFormattingProcessing.parse_numeric(text)
        assert isinstance(ok, bool)
        if not ok:
            assert parsed == 0.0
