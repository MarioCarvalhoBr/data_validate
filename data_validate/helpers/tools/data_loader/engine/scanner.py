#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

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
