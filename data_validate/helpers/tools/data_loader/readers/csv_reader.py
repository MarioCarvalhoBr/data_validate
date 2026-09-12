#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/csv_reader.py
"""
Lê CSV com pandas, corrige cabeçalho duplo e separador explícito.

BUG-018: the separator is received as an explicit constructor parameter (`sep`), sourced by the
caller (`DataLoaderFacade`) from the sheet's `SheetSpec.csv_separator` -- this reader no longer
imports any config module or guesses a separator from the file's stem; a sheet with no known spec
simply cannot reach this reader with a wrong separator, because the facade only calls it for names
present in `SHEET_SPECS`.

BUG-029: reads with `skip_blank_lines=False`. Pandas' own blank-line detection strips whitespace
before checking a line is blank, so with the pandas default (`skip_blank_lines=True`) a row whose
only cell is whitespace-only text is indistinguishable from a genuinely empty line and silently
disappears -- this collides badly with a single-column sheet (`dicionario`), where there is no `|`
separator to make the line visibly non-blank. Turning that default off makes such a row survive.

The trade-off: a *genuinely* empty trailing line (0 characters, common when a file was saved with
a trailing newline) now round-trips as an all-NaN row instead of being skipped. `_read_file` trims
that back out with `_drop_trailing_blank_rows`, which removes only a *contiguous run of fully-NaN
rows at the end* of the frame -- an interior fully-NaN row (e.g. a blank line in the middle of the
file) is preserved untouched, and a trailing row is only dropped when literally every cell in it is
NaN (a whitespace-only cell is not NaN, so a trailing whitespace-only row is kept).
"""

import numpy as np
import pandas as pd

from .base_reader import BaseReader
from ..strategies.header import DoubleHeaderStrategy


def _drop_trailing_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop a trailing run of fully-NaN rows, keeping any earlier (interior) ones untouched.

    Args:
        df: The frame as read by pandas, potentially ending in blank-line artefacts.

    Returns:
        pd.DataFrame: `df` unchanged, or sliced to drop only the trailing fully-NaN rows.
    """
    if df.empty:
        return df

    is_blank_row = df.isna().all(axis=1).to_numpy()
    if not is_blank_row.any():
        return df

    non_blank_positions = (~is_blank_row).nonzero()[0]
    if non_blank_positions.size == 0:
        return df.iloc[0:0]

    last_non_blank_position = non_blank_positions[-1]
    return df.iloc[: last_non_blank_position + 1]


class CSVReader(BaseReader):
    def __init__(self, file_path, header_strategy, sep: str = "|"):
        """Initialize the reader.

        Args:
            file_path: Path to the CSV file to read.
            header_strategy: Header-row strategy (`SingleHeaderStrategy`/`DoubleHeaderStrategy`).
            sep: Field separator, explicit per BUG-018 (defaults to the protocol's `|`).
        """
        super().__init__(file_path, header_strategy)
        self.sep = sep

    def _read_file(self):
        header = self.header_strategy.get_header(self.file_path)
        df = pd.read_csv(
            self.file_path, header=header, sep=self.sep, low_memory=False, dtype=str, skip_blank_lines=False
        )
        if isinstance(self.header_strategy, DoubleHeaderStrategy):
            lvl0 = df.columns.get_level_values(0)
            lvl1 = df.columns.get_level_values(1)
            s0 = pd.Series(lvl0)
            s0 = s0.replace(to_replace=r"Unnamed:.*", value=np.nan, regex=True)
            s0 = s0.replace("", np.nan)
            s0 = s0.ffill()
            filled0 = s0.tolist()
            # garante rótulo no primeiro
            if pd.isna(filled0[0]):
                filled0[0] = lvl0[0] or "Unnamed: 0_level_0"
            df.columns = pd.MultiIndex.from_tuples(list(zip(filled0, lvl1)))
        return _drop_trailing_blank_rows(df)
