"""
# Data Validate (canoa_data_validate)

Validates AdaptaBrasil climate-indicator spreadsheet bundles against Protocol v1.13, producing an
HTML/PDF report and a JSON summary. See `.specs/00-overview.md` in the source repository for the
full specification.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from data_validate.config.metadata_info import MetadataInfo


# Lazy loading - imports only when necessary
def get_metadata() -> "MetadataInfo":
    """Get package metadata lazily."""
    from data_validate.config.metadata_info import METADATA

    return METADATA


# Package metadata - using lazy loading
def __getattr__(name: str) -> Any:
    """Lazy attribute access for metadata."""
    """Get package metadata lazily."""
    metadata = get_metadata()

    attr_map = {
        "__name__": "__name__",
        "__project_name__": "__project_name__",
        "__version__": "__version__",
        "__url__": "__url__",
        "__description__": "__description__",
        "__author__": "__author__",
        "__author_email__": "__author_email__",
        "__maintainer_email__": "__maintainer_email__",
        "__license__": "__license__",
        "__python_version__": "__python_version__",
        "__status__": "__status__",
        "__protocol_version__": "__protocol_version__",
        "__welcome__": "__welcome__",
    }

    if name in attr_map:
        return getattr(metadata, attr_map[name])

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
