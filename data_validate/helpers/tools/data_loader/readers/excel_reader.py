#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/excel_reader.py
"""
Lê XLSX com pandas.
"""

import pandas as pd

from .base_reader import BaseReader


class ExcelReader(BaseReader):
    def _read_file(self):
        header = self.header_strategy.get_header(self.file_path)
        return pd.read_excel(self.file_path, header=header, dtype=str, engine="calamine")
