"""
Unit tests for the message catalog parity between locales.

Guards `static/locales/{pt_BR,en_US}/messages.json` against the drift described in
BUG-016: keys missing from one locale, mismatched named placeholders, or an entry
that does not follow the `{"message": "..."}` shape.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from __future__ import annotations

import json
import string
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOCALES_DIR = _REPO_ROOT / "data_validate" / "static" / "locales"
_LOCALE_NAMES = ("pt_BR", "en_US")


def _load_catalog(locale: str) -> dict[str, Any]:
    """Load one locale's `messages.json`.

    Args:
        locale: Locale directory name (e.g. `"pt_BR"`).

    Returns:
        dict[str, Any]: The parsed catalog (key -> `{"message": "..."}`).
    """
    return json.loads((_LOCALES_DIR / locale / "messages.json").read_text(encoding="utf-8"))


def _message_placeholders(message: str) -> set[str]:
    """Extract named `str.format` placeholders from a message template.

    Args:
        message: The message template (e.g. `"Missing {count} items"`).

    Returns:
        set[str]: The set of named fields found in the template.
    """
    return {field_name for _, field_name, _, _ in string.Formatter().parse(message) if field_name}


@pytest.fixture(scope="module")
def catalogs() -> dict[str, dict[str, Any]]:
    """Load every locale catalog once for the test module.

    Returns:
        dict[str, dict[str, Any]]: Locale name -> parsed catalog.
    """
    return {locale: _load_catalog(locale) for locale in _LOCALE_NAMES}


class TestCatalogLoading:
    """Test suite for loading the catalog files themselves."""

    @pytest.mark.parametrize("locale", _LOCALE_NAMES)
    def test_catalog_loads_as_valid_json(self, locale: str) -> None:
        """Each locale's `messages.json` parses as a JSON object."""
        catalog = _load_catalog(locale)

        assert isinstance(catalog, dict)
        assert catalog


class TestCatalogKeyParity:
    """Test suite for key-set parity between locales."""

    def test_all_locales_expose_the_same_key_set(self, catalogs: dict[str, dict[str, Any]]) -> None:
        """Every key present in one locale is present in every other locale."""
        key_sets = {locale: set(catalog) for locale, catalog in catalogs.items()}
        pt_br_keys, en_us_keys = key_sets["pt_BR"], key_sets["en_US"]

        assert pt_br_keys - en_us_keys == set()
        assert en_us_keys - pt_br_keys == set()


class TestCatalogEntryShape:
    """Test suite for the `{"message": str}` entry shape."""

    @pytest.mark.parametrize("locale", _LOCALE_NAMES)
    def test_every_entry_is_a_message_dict(self, catalogs: dict[str, dict[str, Any]], locale: str) -> None:
        """Every catalog entry is a `{"message": "<str>"}` mapping."""
        catalog = catalogs[locale]

        for key, entry in catalog.items():
            assert isinstance(entry, dict), f"{locale}:{key} is not a dict"
            assert set(entry) == {"message"}, f"{locale}:{key} has unexpected fields: {entry.keys()}"
            assert isinstance(entry["message"], str), f"{locale}:{key} message is not a string"


class TestCatalogPlaceholderParity:
    """Test suite for named-placeholder parity between locales."""

    def test_every_key_uses_the_same_placeholders_in_every_locale(self, catalogs: dict[str, dict[str, Any]]) -> None:
        """Each key's message template uses the same named placeholders in every locale."""
        shared_keys = set(catalogs["pt_BR"]) & set(catalogs["en_US"])
        mismatches: dict[str, dict[str, set[str]]] = {}

        for key in shared_keys:
            placeholders_per_locale = {
                locale: _message_placeholders(catalogs[locale][key]["message"]) for locale in _LOCALE_NAMES
            }
            if len({frozenset(placeholders) for placeholders in placeholders_per_locale.values()}) > 1:
                mismatches[key] = placeholders_per_locale

        assert mismatches == {}
