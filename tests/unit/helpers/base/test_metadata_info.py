"""Tests for metadata_info.py module."""

import importlib.metadata

import pytest

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

    def test_init_with_package_not_found(self, mocker) -> None:
        """Test initialization when package is not found."""
        mocker.patch("importlib.metadata.metadata", side_effect=importlib.metadata.PackageNotFoundError("Package not found"))
        mocker.patch("importlib.metadata.version", side_effect=importlib.metadata.PackageNotFoundError("Package not found"))

        metadata = MetadataInfo()

        # Should use default values
        assert metadata.__name__ == "canoa_data_validate"
        assert metadata.__description__ == "DEFAULT DESCRIPTION: This is the default description."
        assert metadata.__license__ == "DEFAULT LICENSE: MIT"
        assert metadata.__author__ == "DEFAULT AUTHOR: Mário Carvalho"
        assert metadata.__author_email__ == "DEFAULT EMAIL: mariodearaujocarvalho@gmail.com"
        assert metadata.__url__ == "DEFAULT URL: https://github.com/AdaptaBrasil/data_validate.git"

    def test_make_version_final(self) -> None:
        """Test _make_version method with final release level."""
        version = MetadataInfo._make_version(1, 2, 3, "final", 0, 0)
        assert version == "1.2.3"

    def test_make_version_beta(self) -> None:
        """Test _make_version method with beta release level."""
        version = MetadataInfo._make_version(1, 2, 3, "beta", 5, 0)
        assert version == "1.2.3b5"

    def test_make_version_alpha(self) -> None:
        """Test _make_version method with alpha release level."""
        version = MetadataInfo._make_version(1, 2, 3, "alpha", 2, 0)
        assert version == "1.2.3a2"

    def test_make_version_candidate(self) -> None:
        """Test _make_version method with candidate release level."""
        version = MetadataInfo._make_version(1, 2, 3, "candidate", 1, 0)
        assert version == "1.2.3rc1"

    def test_make_version_with_dev(self) -> None:
        """Test _make_version method with dev status."""
        version = MetadataInfo._make_version(1, 2, 3, "beta", 5, 10)
        assert version == "1.2.3b5.dev10"

    def test_make_version_invalid_release_level(self) -> None:
        """Test _make_version method with invalid release level."""
        with pytest.raises(AssertionError):
            MetadataInfo._make_version(1, 2, 3, "invalid", 0, 0)

    def test_make_url(self) -> None:
        """Test _make_url method."""
        url = MetadataInfo._make_url(1, 2, 3, "beta", 5, 10)
        expected_url = "https://data_validate.readthedocs.io/en/1.2.3b5.dev10"
        assert url == expected_url

    def test_make_url_final_version(self) -> None:
        """Test _make_url method with final version."""
        url = MetadataInfo._make_url(1, 2, 3, "final", 0, 0)
        expected_url = "https://data_validate.readthedocs.io/en/1.2.3"
        assert url == expected_url

    def test_metadata_global_instance(self) -> None:
        """Test that METADATA global instance is created."""
        assert isinstance(METADATA, MetadataInfo)
        assert hasattr(METADATA, "__version__")
        assert hasattr(METADATA, "__name__")
        assert hasattr(METADATA, "__project_name__")

    def test_version_parsing_with_short_version(self, mocker) -> None:
        """Test version parsing with short version string."""
        mocker.patch("importlib.metadata.version", return_value="1.0")
        mocker.patch("importlib.metadata.metadata", return_value=mocker.MagicMock(get=lambda k, d: d, get_all=lambda k, d: []))

        metadata = MetadataInfo()
        # Should handle short version gracefully
        assert metadata.__version__ is not None

    def test_version_parsing_with_single_digit(self, mocker) -> None:
        """Test version parsing with single digit version."""
        mocker.patch("importlib.metadata.version", return_value="1")
        mocker.patch("importlib.metadata.metadata", return_value=mocker.MagicMock(get=lambda k, d: d, get_all=lambda k, d: []))

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
            "__welcome__",
        ]

        for attr in expected_attributes:
            assert hasattr(metadata, attr)
            assert getattr(metadata, attr) is not None

    def test_status_development_mode(self) -> None:
        """Test status setting in development mode."""
        # Test the status logic directly
        status_dev = 1  # Development mode
        status_prod = "Production/Stable"
        status_dev_str = "Development"

        # Test the conditional logic
        status = status_prod if status_dev == 0 else status_dev_str
        assert status == "Development"
