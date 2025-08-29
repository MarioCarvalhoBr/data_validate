
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_loader/readers/base_reader.py
"""
Template Method: define passo de leitura comum.
"""

from abc import ABC, abstractmethod

class BaseReader(ABC):
    def __init__(self, file_path, header_strategy):
        self.file_path = file_path
        self.header_strategy = header_strategy

    def read(self):
        return self._read_file()

    @abstractmethod
    def _read_file(self):
        pass

