#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/readers/qml_reader.py
"""
Retorna o conteúdo textual de um arquivo QML.
"""

from .base_reader import BaseReader


class QMLReader(BaseReader):
    def _read_file(self):
        return self.file_path.read_text()
