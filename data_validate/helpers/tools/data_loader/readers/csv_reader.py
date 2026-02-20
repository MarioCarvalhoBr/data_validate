#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/csv_reader.py
"""
Lê CSV com pandas, corrige cabeçalho duplo e separador custom.
"""

import numpy as np
import pandas as pd

from .base_reader import BaseReader
from ..common.config import Config
from ..strategies.header import DoubleHeaderStrategy


class CSVReader(BaseReader):
    def _read_file(self):
        header = self.header_strategy.get_header(self.file_path)
        base = self.file_path.stem
        _, _, sep = Config().file_specs.get(base, (None, None, None))

        sep = sep or ","
        df = pd.read_csv(self.file_path, header=header, sep=sep, low_memory=False, dtype=str)
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
        return df
