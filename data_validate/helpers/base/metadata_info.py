#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

"""
Package metadata
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import tomllib


from data_validate.helpers.base.constant_base import ConstantBase


class MetadataInfo(ConstantBase):
    def __init__(self):
        super().__init__()

        # Base metadata
        self.__text_dev__ = "Development"
        self.__text_prod__ = "Production/Stable"
        self.__date_now__ = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Locate the pyproject.toml file (3 levels up from this file)
        pyproject_toml_file: Path = (
            Path(__file__).resolve().parents[3] / "pyproject.toml"
        )

        if not pyproject_toml_file.exists() or not pyproject_toml_file.is_file():
            raise FileNotFoundError(
                f"pyproject.toml file not found: {pyproject_toml_file}"
            )

        data_toml = {}
        with open(pyproject_toml_file, "rb") as f:
            data_toml = tomllib.load(f)

        if "project" not in data_toml:
            raise RuntimeError(
                "pyproject.toml file does not contain a 'project' section"
            )

        # PROJECT INFO METADATA
        self.__name__ = data_toml["project"].get("name", "data_validate")
        self.__project_name__ = data_toml["project"].get("project_name", "Canoa")
        self.__description__ = data_toml["project"].get(
            "description", "Parser and validate data easily for Canoa."
        )
        self.__url__ = (
            data_toml["project"]
            .get("urls", {})
            .get("Repository", "https://github.com/AdaptaBrasil/data_validate.git")
        )
        self.__author__ = (
            data_toml["project"]
            .get("authors", [{}])[0]
            .get("name", "Mário de Araújo Carvalho")
        )
        self.__author_email__ = (
            data_toml["project"]
            .get("authors", [{}])[0]
            .get("email", "mariodearaujocarvalho@gmail.com")
        )
        self.__maintainer_email__ = self.__author_email__

        # PROJECT MAINTAINER INFO
        self.__license__ = data_toml["project"].get("license", "unknown")
        self.__python_version__ = data_toml["project"].get("requires-python", "unknown")

        # PROJECT MAINTAINER VERSION
        self.__version_base__ = data_toml["project"].get("version", "0.0.0")
        self.__release_level__ = data_toml["project"].get("release_level", "beta")
        self.__serial__ = data_toml["project"].get("serial", 0)
        self.__status_dev__ = data_toml["project"].get("status_dev", 0)

        # CONFIGURE VAR FOR VERSION
        self._major, self._minor, self._micro = map(
            int, self.__version_base__.split(".")[:3]
        )

        # Create config data
        version_info = (
            self._major,
            self._minor,
            self._micro,
            self.__release_level__,
            self.__serial__,
            self.__status_dev__,
        )
        self.__version__ = MetadataInfo._make_version(*version_info)
        self.__status__ = (
            self.__text_prod__ if self.__status_dev__ == 0 else self.__text_dev__
        )

        self.__text_init__ = f"The {self.__project_name__} {self.__name__} version {self.__version__} initialized.\n"

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
