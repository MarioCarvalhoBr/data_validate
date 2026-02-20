#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/strategies/header.py
"""
Define como extrair o parâmetro `header` para pandas.read_*.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class HeaderStrategy(ABC):
    @abstractmethod
    def get_header(self, file_path: Path):
        pass


class SingleHeaderStrategy(HeaderStrategy):
    def get_header(self, file_path: Path):
        return 0


class DoubleHeaderStrategy(HeaderStrategy):
    def get_header(self, file_path: Path):
        return [0, 1]
