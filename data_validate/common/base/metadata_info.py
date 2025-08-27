#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

"""
Package metadata
"""

from __future__ import annotations
from datetime import datetime

from common.base.constant_base import ConstantBase


class MetadataInfo(ConstantBase):
    def __init__(self):
        super().__init__()

        # Config
        version_info = (0, 6, 0, "beta", 0)
        _dev = 0

        # Project metadata
        self.__name__ = "Canoa"
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
        self.__status__ = "Development"
        self.__date_now__ = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        self._finalize_initialization()

    @staticmethod
    def _make_version(
            major: int,
            minor: int,
            micro: int,
            releaselevel: str = "final",
            serial: int = 0,
            dev: int = 0,
    ) -> str:
        """Create a readable version string from version_info tuple components."""
        assert releaselevel in ["alpha", "beta", "candidate", "final"]
        version = "%d.%d.%d" % (major, minor, micro)
        if releaselevel != "final":
            short = {"alpha": "a", "beta": "b", "candidate": "rc"}[releaselevel]
            version += f"{short}{serial}"
        if dev != 0:
            version += f".dev{dev}"
        return version

    @staticmethod
    def _make_url(
            major: int,
            minor: int,
            micro: int,
            releaselevel: str,
            serial: int = 0,
            dev: int = 0,
    ) -> str:
        """Make the URL people should start at for this version of coverage.py."""
        return (
                "https://coverage.readthedocs.io/en/"
                + MetadataInfo._make_version(major, minor, micro, releaselevel, serial, dev)
        )

METADATA = MetadataInfo()

