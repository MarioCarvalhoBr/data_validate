#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_loader/factory.py
"""
Factory Method para instanciar leitores adequados.
"""

from pathlib import Path

from ..common.exceptions import ReaderNotFoundError
from ..readers.csv_reader import CSVReader
from ..readers.excel_reader import ExcelReader
from ..readers.qml_reader import QMLReader
from ..strategies.header import HeaderStrategy


class ReaderFactory:
    _registry = {
        ".csv": CSVReader,
        ".xlsx": ExcelReader,
        ".qml": QMLReader,
    }

    @classmethod
    def get_reader(cls, file_path: Path, header_strategy: HeaderStrategy):
        ext = file_path.suffix.lower()
        reader_cls = cls._registry.get(ext)
        if not reader_cls:
            raise ReaderNotFoundError(f"Nenhum leitor para extensão '{ext}'")
        return reader_cls(file_path, header_strategy)
