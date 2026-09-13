#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/exceptions.py
"""Custom exceptions for the data loader package.

BUG-015/ARC-009: `MissingFileError` was deleted -- grep confirmed it was never raised anywhere in
`data_validate/`, only exported from this package's `__init__.py`; a missing required file is
reported as a structural issue (`FileScanner.scan()`'s `missing` list, surfaced by
`data_validate.rules.structure.check_required_files_present`, STRUCT-005), not by raising an
exception.
"""


class ReaderNotFoundError(ValueError):
    """Raised when no reader is registered for a given file extension."""

    pass
