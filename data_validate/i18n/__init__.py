#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Message catalog seam for rendering `Issue`s into localised text (ARC-004, ADR-0004).

See `data_validate.i18n.catalog` for `MessageCatalog`, `default_catalog_dir`, and the two
catalog-loading error types.
"""

from data_validate.i18n.catalog import (
    CatalogInvalidError,
    CatalogNotFoundError,
    MessageCatalog,
    default_catalog_dir,
)

__all__ = [
    "CatalogInvalidError",
    "CatalogNotFoundError",
    "MessageCatalog",
    "default_catalog_dir",
]
