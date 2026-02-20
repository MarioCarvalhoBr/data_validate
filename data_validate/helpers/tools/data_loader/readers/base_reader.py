#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

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
