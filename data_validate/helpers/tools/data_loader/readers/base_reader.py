#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/base_reader.py
"""Base class implementing the Template Method pattern for file readers."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from ..strategies.header import HeaderStrategy


class BaseReader(ABC):
    def __init__(self, file_path: Path, header_strategy: HeaderStrategy) -> None:
        self.file_path = file_path
        self.header_strategy = header_strategy

    def read(self) -> pd.DataFrame:
        return self._read_file()

    @abstractmethod
    def _read_file(self) -> pd.DataFrame:
        pass
