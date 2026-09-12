#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Property-based round-trip tests for CSVReader (TST-005).

Uses `hypothesis` to generate single-header, `|`-separated frames of string
cells, writes them with `DataFrame.to_csv`, reads them back through the public
`CSVReader.read()` API, and checks the frame round-trips.

Note on NaN normalisation (probed against the real reader, documented here
rather than assumed): `CSVReader` reads with `dtype=str`, but pandas applies
its default NA-sentinel detection *before* the dtype cast, so any cell whose
raw text matches one of `pandas._libs.parsers.STR_NA_VALUES` (notably the
empty string `""`, but also `"NA"`, `"NULL"`, `"null"`, `"NaN"`, `"nan"`,
`"None"`, `"N/A"`, `"n/a"`, ...) comes back as `NaN`, not as that literal
string -- even though the column dtype is otherwise `str`. The round-trip
property below therefore excludes those sentinel strings from generated cell
content (that is the input space where round-trip equality holds) and a
separate, explicit test documents the empty-string-becomes-NaN behaviour.
"""

from pathlib import Path

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from data_validate.helpers.tools.data_loader.readers.csv_reader import CSVReader
from data_validate.helpers.tools.data_loader.strategies.header import SingleHeaderStrategy

# pandas' default NA sentinels (pandas._libs.parsers.STR_NA_VALUES) -- hardcoded
# rather than imported from a private pandas module, so this test does not break
# if that private symbol moves.
NA_SENTINELS = {
    "",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",
    "N/A",
    "NA",
    "NULL",
    "NaN",
    "None",
    "n/a",
    "nan",
    "null",
}

# Letters, digits, space, accented pt-BR characters, comma, dot, dash -- explicitly
# without "|" (the CSV separator) or newlines, per the round-trip contract.
CELL_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 áéíóúÁÉÍÓÚçÇãõÃÕêÊ,.-"
COLUMN_NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

cell_strategy = st.text(alphabet=CELL_ALPHABET, min_size=1, max_size=15).filter(lambda s: s not in NA_SENTINELS)
column_name_strategy = st.text(alphabet=COLUMN_NAME_ALPHABET, min_size=1, max_size=12)


@st.composite
def single_header_dataframe(draw, min_cols: int = 2, max_cols: int = 8, max_rows: int = 20) -> pd.DataFrame:
    """Build a small single-header DataFrame of string cells for the CSV round-trip.

    `min_cols` defaults to 2 (not 1): with exactly one column and no `|` separator on
    the line, a row whose sole cell is a whitespace-only string collides with pandas'
    default `skip_blank_lines=True` and the row silently disappears on read -- see
    `TestCSVReaderSingleColumnBlankLineBugCandidate` below, which documents that
    edge case separately rather than making this property flaky.
    """
    num_cols = draw(st.integers(min_value=min_cols, max_value=max_cols))
    num_rows = draw(st.integers(min_value=1, max_value=max_rows))
    columns = draw(st.lists(column_name_strategy, min_size=num_cols, max_size=num_cols, unique=True))

    data = {column: draw(st.lists(cell_strategy, min_size=num_rows, max_size=num_rows)) for column in columns}
    return pd.DataFrame(data)


class TestCSVReaderRoundtrip:
    """`CSVReader.read()` must reproduce a written single-header, '|'-separated frame."""

    @given(dataframe=single_header_dataframe())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_roundtrip_preserves_columns_and_values(self, dataframe: pd.DataFrame, tmp_path: Path) -> None:
        """Writing then reading a frame with no NA-sentinel cells reproduces it exactly."""
        csv_path = tmp_path / "descricao.csv"
        dataframe.to_csv(csv_path, sep="|", index=False)

        result = CSVReader(csv_path, SingleHeaderStrategy()).read()

        assert list(result.columns) == list(dataframe.columns)
        assert result.shape == dataframe.shape
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            dataframe.reset_index(drop=True),
            check_dtype=False,
        )


class TestCSVReaderNaNNormalisation:
    """Document the empty-string/NA-sentinel normalisation applied by pandas on read."""

    def test_empty_string_cell_becomes_nan_not_empty_string(self, tmp_path: Path) -> None:
        """A cell written as an empty string round-trips as NaN, not as ''."""
        dataframe = pd.DataFrame({"a": ["x", "", "y"], "b": ["1", "2", "3"]})
        csv_path = tmp_path / "descricao.csv"
        dataframe.to_csv(csv_path, sep="|", index=False)

        result = CSVReader(csv_path, SingleHeaderStrategy()).read()

        assert result.loc[1, "a"] != ""
        assert pd.isna(result.loc[1, "a"])

    def test_whitespace_only_cell_is_preserved_literally(self, tmp_path: Path) -> None:
        """A cell that is only whitespace (not an NA sentinel) is preserved, unlike ''."""
        dataframe = pd.DataFrame({"a": ["x", " ", "y"], "b": ["1", "2", "3"]})
        csv_path = tmp_path / "descricao.csv"
        dataframe.to_csv(csv_path, sep="|", index=False)

        result = CSVReader(csv_path, SingleHeaderStrategy()).read()

        assert result.loc[1, "a"] == " "


class TestCSVReaderSingleColumnBlankLineBugCandidate:
    """BUG candidate found while probing the round-trip property (TST-005).

    In a single-column CSV (no `|` on the line at all), a row whose sole cell is a
    whitespace-only string is indistinguishable, to pandas' `skip_blank_lines=True`
    default, from a genuinely blank line -- so the row is silently dropped on read,
    even though `CSVReader` always passes `dtype=str` and never asks for blank lines
    to be skipped explicitly. Multi-column rows are unaffected (the `|` separator(s)
    make the line non-blank). Real bundle sheets (`descricao`, `composicao`, ...)
    always have >= 2 columns, so production impact is likely low, but the reader
    has no size/shape invariant guarding against silent row loss.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "BUG candidate (TST-005 property finding): CSVReader silently drops a row "
            "in a single-column CSV when that row's only cell is whitespace-only, "
            "because pandas' read_csv default skip_blank_lines=True treats a line with "
            "no separator and only whitespace as blank. "
            'Repro: pd.DataFrame({"0": [" "]}).to_csv(path, sep="|", index=False) then '
            "CSVReader(path, SingleHeaderStrategy()).read() returns shape (0, 1), not (1, 1)."
        ),
    )
    def test_single_column_whitespace_row_is_dropped(self, tmp_path: Path) -> None:
        """A single-column frame with a whitespace-only row loses that row on read."""
        dataframe = pd.DataFrame({"0": [" "]})
        csv_path = tmp_path / "descricao.csv"
        dataframe.to_csv(csv_path, sep="|", index=False)

        result = CSVReader(csv_path, SingleHeaderStrategy()).read()

        assert result.shape == dataframe.shape
