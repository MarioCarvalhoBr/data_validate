
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_importer/readers/__init__.py
"""
Pacote de leitores de arquivos.
"""

from .base_reader import BaseReader
from .csv_reader import CSVReader
from .excel_reader import ExcelReader
from .qml_reader import QMLReader

__all__ = ["BaseReader", "CSVReader", "ExcelReader", "QMLReader"]

