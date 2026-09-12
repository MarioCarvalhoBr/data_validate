#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Single source of truth for sheet definitions (ARC-003, ADR-0003).

See ``data_validate.specs.sheet_specs`` for the full registry and the divergences it
documents between the three legacy sources it supersedes.
"""

from data_validate.specs.sheet_specs import (
    ALLOWED_EXTENSIONS,
    SHEET_SPECS,
    ColumnKind,
    ColumnSpec,
    HeaderLayout,
    SheetSpec,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    "SHEET_SPECS",
    "ColumnKind",
    "ColumnSpec",
    "HeaderLayout",
    "SheetSpec",
]
