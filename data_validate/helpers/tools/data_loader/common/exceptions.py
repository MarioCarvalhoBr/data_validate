
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

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

