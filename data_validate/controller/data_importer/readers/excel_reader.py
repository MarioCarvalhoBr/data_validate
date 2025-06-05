
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_importer/readers/excel_reader.py
"""
Lê XLSX com pandas.
"""

import pandas as pd
from .base_reader import BaseReader

class ExcelReader(BaseReader):
    def _read_file(self):
        header = self.header_strategy.get_header(self.file_path)
        return pd.read_excel(self.file_path, header=header)

