#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Pacote principal que expõe a API de alto nível.
"""

from .api.facade import DataLoaderFacade, DataLoaderModel, LoadResult
from .common.exceptions import ReaderNotFoundError

__all__ = [
    "DataLoaderFacade",
    "DataLoaderModel",
    "LoadResult",
    "ReaderNotFoundError",
]
