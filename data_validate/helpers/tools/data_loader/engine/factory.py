#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/factory.py
"""Factory to instantiate file readers based on file extension.

BUG-015: `.qml` was removed from the registry along with `QMLReader` (ADR-0003) -- no evidence
was found that the protocol needs it, and nothing in `data_validate/` consumed the QML content the
old reader produced.
"""

from pathlib import Path

from ..common.exceptions import ReaderNotFoundError
from ..readers.base_reader import BaseReader
from ..readers.csv_reader import CSVReader
from ..readers.excel_reader import ExcelReader
from ..strategies.header import HeaderStrategy


class ReaderFactory:
    _registry: dict[str, type[BaseReader]] = {
        ".csv": CSVReader,
        ".xlsx": ExcelReader,
    }

    @classmethod
    def get_reader(cls, file_path: Path, header_strategy: HeaderStrategy, sep: str = "|") -> BaseReader:
        """Build the reader for `file_path`'s extension.

        Args:
            file_path: Path whose suffix selects the reader.
            header_strategy: Header-row strategy passed through to the reader.
            sep: CSV field separator (BUG-018: comes from the caller's `SheetSpec`, never guessed
                from the file stem); ignored by readers that don't need it (e.g. `ExcelReader`).

        Returns:
            The constructed reader instance.

        Raises:
            ReaderNotFoundError: When no reader is registered for `file_path`'s extension.
        """
        ext = file_path.suffix.lower()
        reader_cls = cls._registry.get(ext)
        if not reader_cls:
            raise ReaderNotFoundError(f"Nenhum leitor para extensão '{ext}'")
        if reader_cls is CSVReader:
            return reader_cls(file_path, header_strategy, sep=sep)
        return reader_cls(file_path, header_strategy)
