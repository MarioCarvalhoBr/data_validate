
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_importer/readers/qml_reader.py
"""
Retorna o conteúdo textual de um arquivo QML.
"""
from .base_reader import BaseReader

class QMLReader(BaseReader):
    def _read_file(self):
        return self.file_path.read_text()

