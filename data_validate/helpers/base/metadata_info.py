#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

"""
Package metadata
"""

from __future__ import annotations
from datetime import datetime

from data_validate.helpers.base.constant_base import ConstantBase


class MetadataInfo(ConstantBase):
    def __init__(self):
        super().__init__()

        # CONFIGURE METADATA
        _major: int = 0
        _minor: int = 7
        _micro: int = 2
        _release_level: str = "beta"
        _serial: int = 0
        _dev: int = 2  # 0 for production, >0 for development builds

        # Create config data
        version_info = (_major, _minor, _micro, _release_level, _serial)

        # Other constants
        self.STATUS_DEVELOPMENT = "Development"
        self.STATUS_PRODUCTION = "Production/Stable"

        # Project metadata
        self.__name__ = "data_validate"
        self.__project_name__ = "Canoa"
        self.__version__ = MetadataInfo._make_version(*version_info, _dev)
        self.__url__ = MetadataInfo._make_url(*version_info, _dev)
        self.__description__ = "A simple parser for Canoa project"

        # Author and maintainer metadata
        self.__author__ = "Mário de Araújo Carvalho"
        self.__author_email__ = "mariodearaujocarvalho@gmail.com"
        self.__maintainer_email__ = "mariodearaujocarvalho@gmail.com"

        # Other metadata
        self.__license__ = "MIT"
        self.__url__ = "https://github.com/AdaptaBrasil/data_validate"
        self.__python__ = "3.12"
        self.__python_version__ = self.__python__

        self.__status__ = self.STATUS_PRODUCTION if _dev == 0 else self.STATUS_DEVELOPMENT
        self.__date_now__ = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
        return "https://data_validate.readthedocs.io/en/" + MetadataInfo._make_version(
            major, minor, micro, release_level, serial, dev
        )


METADATA = MetadataInfo()
