#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

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
