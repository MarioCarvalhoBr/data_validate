#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
# File: data_loader/__init__.py
"""
Pacote principal que expõe a API de alto nível.
"""

from .api.facade import DataLoaderFacade, DataLoaderModel
from .common.config import Config
from .common.exceptions import MissingFileError, ReaderNotFoundError

__all__ = [
    "DataLoaderFacade",
    "Config",
    "MissingFileError",
    "ReaderNotFoundError",
    "DataLoaderModel",
]