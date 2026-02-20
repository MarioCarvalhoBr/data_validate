#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/exceptions.py
"""
Errores customizados do pacote.
"""


class MissingFileError(FileNotFoundError):
    """Quando um arquivo obrigatório não é encontrado."""

    pass


class ReaderNotFoundError(ValueError):
    """Quando não existe leitor para uma dada extensão."""

    pass
