#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/exceptions.py
"""
Errores customizados do pacote.

BUG-015/ARC-009: `MissingFileError` was deleted -- grep confirmed it was never raised anywhere in
`data_validate/`, only exported from this package's `__init__.py`; a missing required file is
reported as a structural issue (`FileScanner.scan()`'s `missing` list, surfaced by
`FileStructureValidator`), not by raising an exception.
"""


class ReaderNotFoundError(ValueError):
    """Quando não existe leitor para uma dada extensão."""

    pass
