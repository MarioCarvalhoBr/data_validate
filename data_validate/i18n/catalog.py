#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""`MessageCatalog`: renders `Issue`s and catalog keys into localised text (ARC-004, ADR-0004).

Target replacement for `data_validate.helpers.tools.locale.language_manager.LanguageManager`
(see `.specs/architecture/module-map.md`): unlike `LanguageManager`, this class never reads or
writes `.config/store.locale`, never prints, and takes its locale and catalog directory explicitly
through the constructor instead of discovering them as a side effect of `__init__` — no work in
`__init__` beyond assigning/loading what was passed in (`.claude/rules/coding-standards.md`).

This module is model-only (Phase 1 step 2 of `08-migration-roadmap.md`): nothing here is wired
into the legacy pipeline yet. It depends only on `data_validate.specs` and the standard library,
per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_validate.specs.issues import Issue


def default_catalog_dir() -> Path:
    """Return the package's default locale catalog directory.

    Returns:
        Path: `data_validate/static/locales`, the directory containing one subdirectory per
            locale (`pt_BR`, `en_US`), each with a `messages.json`.
    """
    return Path(__file__).resolve().parent.parent / "static" / "locales"


class CatalogNotFoundError(Exception):
    """Raised when a locale's `messages.json` does not exist under the catalog directory."""


class CatalogInvalidError(Exception):
    """Raised when a locale's `messages.json` exists but is not valid JSON."""


class MessageCatalog:
    """Loads one locale's message catalog and renders catalog keys/`Issue`s into text.

    Attributes:
        locale: The locale this catalog was loaded for (e.g. `"pt_BR"`).
        catalog_dir: The directory `messages.json` was loaded from (`catalog_dir/locale`).
    """

    def __init__(self, locale: str, catalog_dir: Path) -> None:
        """Load `catalog_dir/locale/messages.json` for `locale`.

        Args:
            locale: Locale directory name (e.g. `"pt_BR"`, `"en_US"`).
            catalog_dir: Directory containing one subdirectory per locale.

        Raises:
            CatalogNotFoundError: If `catalog_dir/locale/messages.json` does not exist.
            CatalogInvalidError: If the file exists but is not valid JSON.
        """
        self.locale = locale
        self.catalog_dir = catalog_dir
        self._translations: dict[str, Any] = self._load_translations(locale, catalog_dir)

    @staticmethod
    def _load_translations(locale: str, catalog_dir: Path) -> dict[str, Any]:
        """Read and parse `catalog_dir/locale/messages.json`.

        Args:
            locale: Locale directory name.
            catalog_dir: Directory containing one subdirectory per locale.

        Returns:
            dict[str, Any]: The parsed catalog (key -> `{"message": "..."}`).

        Raises:
            CatalogNotFoundError: If the file does not exist.
            CatalogInvalidError: If the file is not valid JSON.
        """
        catalog_path = catalog_dir / locale / "messages.json"
        if not catalog_path.is_file():
            raise CatalogNotFoundError(f"No message catalog for locale {locale!r} at {catalog_path}")

        try:
            with catalog_path.open("r", encoding="utf-8") as catalog_file:
                loaded: dict[str, Any] = json.load(catalog_file)
        except json.JSONDecodeError as decode_error:
            raise CatalogInvalidError(
                f"Invalid JSON in message catalog {catalog_path}: {decode_error}"
            ) from decode_error
        return loaded

    def text(self, key: str, **params: object) -> str:
        """Look up `key` in this locale's catalog and interpolate `params`.

        Args:
            key: The catalog key to look up (e.g. `"rule.DESC-004.error"`).
            **params: Named placeholders substituted into the message template.

        Returns:
            str: The translated, interpolated string, or a fallback marker string when `key` is
                missing or the entry has an invalid structure — the same fallback format as
                `LanguageManager.text`: `"<Message for '{key}' missing in '{locale}'>"` when the
                key is absent, `"<'{key}' missing or invalid structure in '{locale}'>"` when the
                entry is present but not a `{"message": "..."}` mapping. A placeholder missing
                from `params` leaves the template unformatted rather than raising.
        """
        translation_entry = self._translations.get(key)
        template: str
        if isinstance(translation_entry, dict):
            template = translation_entry.get("message", f"<Message for '{key}' missing in '{self.locale}'>")
        else:
            template = f"<'{key}' missing or invalid structure in '{self.locale}'>"

        if not params:
            return template
        try:
            return template.format(**params)
        except (KeyError, IndexError):
            return template

    def render(self, issue: Issue) -> str:
        """Render an `Issue` using its `message_key` and `params`.

        Args:
            issue: The issue to render.

        Returns:
            str: `self.text(issue.message_key, **issue.params)`.
        """
        return self.text(issue.message_key, **issue.params)
