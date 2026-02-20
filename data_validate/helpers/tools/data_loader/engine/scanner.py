#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/scanner.py
"""
Escaneia diretório de entrada e valida existência de arquivos.
"""

from pathlib import Path

from ..common.config import Config


class FileScanner:
    def __init__(self, directory: Path):
        self.dir = directory
        self.config = Config()

    def scan(self):
        found = {}
        qmls = []
        for f in self.dir.iterdir():
            base, ext = f.stem, f.suffix.lower()
            if base in self.config.file_specs and ext in self.config.extensions:
                if ext == ".qml":
                    qmls.append(f)
                else:
                    # prefere .csv sobre .xlsx
                    if base in found and found[base].suffix == ".csv":
                        continue
                    if base in found and ext == ".csv":
                        found[base] = f
                    elif base not in found:
                        found[base] = f
        missing = [name for name, (req, _, _) in self.config.file_specs.items() if req and name not in found]

        return found, qmls, missing
