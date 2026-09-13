#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import importlib.metadata
import logging
from typing import Final

from data_validate.helpers.base.constant_base import ConstantBase

logger = logging.getLogger(__name__)


class MetadataInfo(ConstantBase):
    """
    Class holding immutable metadata and version information for the project.

    Retrieves metadata from the installed package (if available) or falls back
    to default values. TOOL-005: the version is read verbatim from
    `importlib.metadata.version(dist_name)` — there is no hand-maintained
    `serial`/`release_level` composition anymore, so a release only ever needs
    a `pyproject.toml` version bump.

    Attributes:
        __version__ (str): Installed distribution version (e.g., '0.7.65'), or
            `"0.0.0+unknown"` when the package is not installed.
        __name__ (str): Distribution package name.
        __project_name__ (str): Human-readable project name.
        __description__ (str): Project summary/description.
        __license__ (str): License type (e.g., 'MIT').
        __python_version__ (str): Supported Python version requirements.
        __author__ (str): Author's name.
        __author_email__ (str): Author's email address.
        __url__ (str): Project repository URL.
        __status__ (str): Development status (always 'Production/Stable' now
            that there is no hand-maintained dev/beta serial).
        __protocol_version__ (str): Version of the AdaptaBrasil protocol the
            validator implements (DOC-006), e.g. '1.16'.
        __welcome__ (str): Standard welcome message string.
    """

    PROTOCOL_VERSION: Final = "1.16"
    """Version of the AdaptaBrasil protocol this validator implements (DOC-006).

    See `.specs/business-rules/protocol-changelog.md` for the version history
    and the protocol ↔ code gap list. Bumping this constant is a protocol
    version change and follows the process documented there (ADR + spec
    update + reviewed golden re-baseline).
    """

    _FALLBACK_VERSION: Final = "0.0.0+unknown"

    def __init__(self) -> None:
        """
        Initialize MetadataInfo with package metadata.

        Attempts to load metadata from `importlib.metadata`. If the package is not
        installed, a debug log entry is recorded and default values are used.
        Finalizes initialization to make attributes immutable.
        """
        super().__init__()

        project_name: Final = "Canoa"
        dist_name: Final = "canoa_data_validate"

        self.__version__ = self._FALLBACK_VERSION
        self.__name__ = dist_name
        self.__project_name__ = project_name
        self.__description__ = "DEFAULT DESCRIPTION: This is the default description."
        self.__license__ = "DEFAULT LICENSE: MIT"
        self.__python_version__ = "DEFAULT PYTHON VERSION: >=3.12"
        self.__author__ = "DEFAULT AUTHOR: Mário Carvalho"
        self.__author_email__ = "DEFAULT EMAIL: mariodearaujocarvalho@gmail.com"
        self.__url__ = "DEFAULT URL: https://github.com/AdaptaBrasil/data_validate.git"
        self.__status_dev__ = "Development"
        self.__status_prod__ = "Production/Stable"
        self.__protocol_version__ = self.PROTOCOL_VERSION

        try:
            meta = importlib.metadata.metadata(dist_name)

            self.__version__ = importlib.metadata.version(dist_name)
            self.__name__ = meta.get("Name", dist_name)
            self.__description__ = meta.get("Summary", "Descrição padrão.")
            self.__license__ = meta.get("License", "MIT")
            self.__python_version__ = meta.get("Requires-Python", ">=3.12")
            self.__author__ = meta.get("Author", "Autor desconhecido")
            self.__author_email__ = meta.get("Author-Email", "email@desconhecido.com")

            project_urls = {entry.split(", ")[0]: entry.split(", ")[1] for entry in meta.get_all("Project-URL", [])}
            self.__url__ = project_urls.get("Repository", "URL não encontrada")

        except importlib.metadata.PackageNotFoundError:
            logger.debug('Package "%s" not found. Using default metadata values.', dist_name)

        # CONFIGURE URL, STATUS AND WELCOME MESSAGE
        self.__maintainer_email__ = self.__author_email__
        self.__status__ = self.__status_prod__
        self.__welcome__ = f"The {self.__project_name__} {self.__name__} version {self.__version__} initialized.\n"

        self._finalize_initialization()


METADATA = MetadataInfo()
