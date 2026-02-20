#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/__init__.py
"""
Pacote de leitores de arquivos.
"""

from .base_reader import BaseReader
from .csv_reader import CSVReader
from .excel_reader import ExcelReader
from .qml_reader import QMLReader

__all__ = ["BaseReader", "CSVReader", "ExcelReader", "QMLReader"]
