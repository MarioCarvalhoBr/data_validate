#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
# File: data_importer/__init__.py
"""
Pacote principal que expõe a API de alto nível.
"""

from .api.facade import DataImporterFacade, DataModelImporter
from .common.config import Config
from .common.exceptions import MissingFileError, ReaderNotFoundError

__all__ = [
    "DataImporterFacade",
    "Config",
    "MissingFileError",
    "ReaderNotFoundError",
    "DataModelImporter",
]