#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import importlib.metadata
from typing import Final

from data_validate.helpers.base.constant_base import ConstantBase


class MetadataInfo(ConstantBase):
    def __init__(self):
        super().__init__()

        project_name: Final = "Canoa"
        dist_name: Final = "canoa_data_validate"
        release_level: Final = "beta"
        serial: Final = 641
        status_dev: Final = 0

        self.__version__ = "0.0.0"
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
            print(f'Warning: Package "{dist_name}" not found. Using default metadata values.')

        # CONFIGURE VAR FOR VERSION: MAJOR, MINOR, MICRO
        map_versions = list(map(int, self.__version__.split(".")))
        major_version: Final = map_versions[0] if len(map_versions) > 0 else 0
        minor_version: Final = map_versions[1] if len(map_versions) > 1 else 0
        micro_version: Final = map_versions[2] if len(map_versions) > 2 else 0

        # Finally, create the full version string
        self.__version__ = MetadataInfo._make_version(major_version, minor_version, micro_version, release_level, serial, status_dev)

        # CONFIGURE URL, STATUS AND WELCOME MESSAGE
        self.__maintainer_email__ = self.__author_email__
        self.__status__ = self.__status_prod__ if status_dev == 0 else self.__status_dev__
        self.__welcome__ = f"The {self.__project_name__} {self.__name__} version {self.__version__} initialized.\n"

        self._finalize_initialization()

    @staticmethod
    def _make_version(
        major: int,
        minor: int,
        micro: int,
        release_level: str = "final",
        serial: int = 0,
        dev: int = 0,
    ) -> str:
        """Create a readable version string from version_info tuple components."""
        assert release_level in ["alpha", "beta", "candidate", "final"]
        version = "%d.%d.%d" % (major, minor, micro)
        if release_level != "final":
            short = {"alpha": "a", "beta": "b", "candidate": "rc"}[release_level]
            version += f"{short}{serial}"
        if dev != 0:
            version += f".dev{dev}"
        return version

    @staticmethod
    def _make_url(
        major: int,
        minor: int,
        micro: int,
        release_level: str,
        serial: int = 0,
        dev: int = 0,
    ) -> str:
        """Make the URL people should start at for this version of data_validate.__init__.py."""
        return "https://data_validate.readthedocs.io/en/" + MetadataInfo._make_version(major, minor, micro, release_level, serial, dev)


METADATA = MetadataInfo()
