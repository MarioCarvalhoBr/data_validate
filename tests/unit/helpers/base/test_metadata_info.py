"""Tests for metadata_info.py module."""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import importlib.metadata


from data_validate.config.metadata_info import MetadataInfo, METADATA


class TestMetadataInfo:
    """Test suite for MetadataInfo class."""

    def test_init_with_package_found(self, mocker) -> None:
        """Test initialization when package is found."""
        # Mock the metadata
        mock_meta = mocker.MagicMock()
        mock_meta.get.side_effect = lambda key, default=None: {
            "Name": "canoa_data_validate",
            "Summary": "Test description",
            "License": "MIT",
            "Requires-Python": ">=3.12",
            "Author": "Test Author",
            "Author-Email": "test@example.com",
        }.get(key, default)

        mock_meta.get_all.return_value = ["Repository, https://github.com/test/repo.git"]

        mocker.patch("importlib.metadata.metadata", return_value=mock_meta)
        mocker.patch("importlib.metadata.version", return_value="1.0.0")

        metadata = MetadataInfo()

        assert metadata.__name__ == "canoa_data_validate"
        assert metadata.__description__ == "Test description"
        assert metadata.__license__ == "MIT"
        assert metadata.__author__ == "Test Author"
        assert metadata.__author_email__ == "test@example.com"
        assert metadata.__url__ == "https://github.com/test/repo.git"
        # TOOL-005: the version is now read verbatim, not composed from
        # major/minor/micro + a hand-maintained serial.
        assert metadata.__version__ == "1.0.0"

    def test_init_with_package_not_found(self, mocker, capsys) -> None:
        """Test initialization when package is not found."""
        mocker.patch(
            "importlib.metadata.metadata", side_effect=importlib.metadata.PackageNotFoundError("Package not found")
        )
        mocker.patch(
            "importlib.metadata.version", side_effect=importlib.metadata.PackageNotFoundError("Package not found")
        )

        metadata = MetadataInfo()

        # Should use default values
        assert metadata.__name__ == "canoa_data_validate"
        assert metadata.__description__ == "DEFAULT DESCRIPTION: This is the default description."
        assert metadata.__license__ == "DEFAULT LICENSE: MIT"
        assert metadata.__author__ == "DEFAULT AUTHOR: Mário Carvalho"
        assert metadata.__author_email__ == "DEFAULT EMAIL: mariodearaujocarvalho@gmail.com"
        assert metadata.__url__ == "DEFAULT URL: https://github.com/AdaptaBrasil/data_validate.git"

        # BUG-017: no print() side effect when the package is not installed.
        captured = capsys.readouterr()
        assert captured.out == ""

        # TOOL-005: no hand-maintained serial composition; a clearly-marked
        # fallback constant is used instead of a fake "0.0.0" release.
        assert metadata.__version__ == "0.0.0+unknown"

    def test_make_url_removed(self) -> None:
        """Test that the dead `_make_url` static method was removed (BUG-017)."""
        assert not hasattr(MetadataInfo, "_make_url")

    def test_make_version_removed(self) -> None:
        """TOOL-005: the hand-maintained version-composition helper is gone.

        The version is read verbatim from `importlib.metadata.version(...)`
        (or the `_FALLBACK_VERSION` constant) — there is no more
        major/minor/micro + release_level/serial/dev composition.
        """
        assert not hasattr(MetadataInfo, "_make_version")

    def test_protocol_version_constant(self) -> None:
        """DOC-006: the protocol version the validator implements is a stable constant."""
        assert MetadataInfo.PROTOCOL_VERSION == "1.16"

    def test_protocol_version_attribute_matches_constant(self) -> None:
        """DOC-006: the instance attribute mirrors the class constant."""
        metadata = MetadataInfo()
        assert metadata.__protocol_version__ == MetadataInfo.PROTOCOL_VERSION

    def test_metadata_global_instance(self) -> None:
        """Test that METADATA global instance is created."""
        assert isinstance(METADATA, MetadataInfo)
        assert hasattr(METADATA, "__version__")
        assert hasattr(METADATA, "__name__")
        assert hasattr(METADATA, "__project_name__")

    def test_version_parsing_with_short_version(self, mocker) -> None:
        """Test version parsing with short version string."""
        mocker.patch("importlib.metadata.version", return_value="1.0")
        mocker.patch(
            "importlib.metadata.metadata", return_value=mocker.MagicMock(get=lambda k, d: d, get_all=lambda k, d: [])
        )

        metadata = MetadataInfo()
        # Should handle short version gracefully
        assert metadata.__version__ is not None

    def test_version_parsing_with_single_digit(self, mocker) -> None:
        """Test version parsing with single digit version."""
        mocker.patch("importlib.metadata.version", return_value="1")
        mocker.patch(
            "importlib.metadata.metadata", return_value=mocker.MagicMock(get=lambda k, d: d, get_all=lambda k, d: [])
        )

        metadata = MetadataInfo()
        # Should handle single digit version gracefully
        assert metadata.__version__ is not None

    def test_project_urls_parsing(self, mocker) -> None:
        """Test parsing of project URLs."""
        mock_meta = mocker.MagicMock()
        mock_meta.get.side_effect = lambda key, default=None: {"Name": "test_package"}.get(key, default)

        mock_meta.get_all.return_value = [
            "Repository, https://github.com/test/repo.git",
            "Homepage, https://test.com",
            "Documentation, https://docs.test.com",
        ]

        mocker.patch("importlib.metadata.metadata", return_value=mock_meta)
        mocker.patch("importlib.metadata.version", return_value="1.0.0")

        metadata = MetadataInfo()
        assert metadata.__url__ == "https://github.com/test/repo.git"

    def test_project_urls_parsing_no_repository(self, mocker) -> None:
        """Test parsing of project URLs when no repository URL is found."""
        mock_meta = mocker.MagicMock()
        mock_meta.get.side_effect = lambda key, default=None: {"Name": "test_package"}.get(key, default)

        mock_meta.get_all.return_value = ["Homepage, https://test.com", "Documentation, https://docs.test.com"]

        mocker.patch("importlib.metadata.metadata", return_value=mock_meta)
        mocker.patch("importlib.metadata.version", return_value="1.0.0")

        metadata = MetadataInfo()
        assert metadata.__url__ == "URL não encontrada"

    def test_metadata_attributes_initialization(self) -> None:
        """Test that all metadata attributes are properly initialized."""
        metadata = MetadataInfo()

        # Check that all expected attributes exist
        expected_attributes = [
            "__version__",
            "__name__",
            "__project_name__",
            "__description__",
            "__license__",
            "__python_version__",
            "__author__",
            "__author_email__",
            "__url__",
            "__maintainer_email__",
            "__status__",
            "__protocol_version__",
            "__welcome__",
        ]

        for attr in expected_attributes:
            assert hasattr(metadata, attr)
            assert getattr(metadata, attr) is not None

    def test_status_is_always_production_stable(self) -> None:
        """TOOL-005: without a hand-maintained dev/beta serial, status is always 'Production/Stable'."""
        metadata = MetadataInfo()
        assert metadata.__status__ == "Production/Stable"
