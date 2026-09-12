#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `MessageCatalog` (ARC-004, ADR-0004).

Exercises the real `pt_BR`/`en_US` catalogs under `default_catalog_dir()`, the missing-key/
invalid-structure fallbacks copied verbatim from `LanguageManager.text` (`.claude/rules/testing.md`
table-driven convention), and the two catalog-loading error types.
"""

from __future__ import annotations

import json

import pytest

from data_validate.i18n.catalog import (
    CatalogInvalidError,
    CatalogNotFoundError,
    MessageCatalog,
    default_catalog_dir,
)
from data_validate.specs.issues import Issue, Severity


class TestDefaultCatalogDir:
    """`default_catalog_dir` points at the real package locale directory."""

    def test_points_at_static_locales(self) -> None:
        catalog_dir = default_catalog_dir()

        assert catalog_dir.name == "locales"
        assert catalog_dir.parent.name == "static"
        assert (catalog_dir / "pt_BR" / "messages.json").is_file()
        assert (catalog_dir / "en_US" / "messages.json").is_file()


class TestMessageCatalogAgainstRealCatalogs:
    """Loading and rendering against the real, shipped locale catalogs."""

    @pytest.mark.parametrize("locale", ["pt_BR", "en_US"])
    def test_renders_a_known_key_identically_to_the_literal_json(self, locale: str) -> None:
        catalog_path = default_catalog_dir() / locale / "messages.json"
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        expected = raw_catalog["invalid_language"]["message"].format(default_lang="pt_BR")

        catalog = MessageCatalog(locale=locale, catalog_dir=default_catalog_dir())

        assert catalog.text("invalid_language", default_lang="pt_BR") == expected

    def test_text_without_params_returns_the_raw_unformatted_template(self) -> None:
        catalog_path = default_catalog_dir() / "pt_BR" / "messages.json"
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        expected = raw_catalog["lang_load_error"]["message"]

        catalog = MessageCatalog(locale="pt_BR", catalog_dir=default_catalog_dir())

        assert catalog.text("lang_load_error") == expected

    def test_text_with_params_interpolates_the_real_template(self) -> None:
        catalog_path = default_catalog_dir() / "pt_BR" / "messages.json"
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        expected = raw_catalog["lang_load_error"]["message"].format(lang="en_US", default_lang="pt_BR")

        catalog = MessageCatalog(locale="pt_BR", catalog_dir=default_catalog_dir())

        assert catalog.text("lang_load_error", lang="en_US", default_lang="pt_BR") == expected


class TestMessageCatalogFallbacks:
    """Fallback text for a missing key or malformed entry, byte-for-byte with `LanguageManager`."""

    def test_missing_key_returns_the_invalid_structure_marker(self, tmp_path) -> None:
        # A key entirely absent from the catalog is, like a non-dict entry, "not a dict" from
        # `self._translations.get(key)`'s point of view — it hits the same branch as a malformed
        # entry, not the "message field missing from a present dict" branch (see
        # `test_missing_message_field_falls_back_to_the_missing_marker` below for that one).
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text("{}", encoding="utf-8")
        catalog = MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)

        assert catalog.text("no_such_key") == "<'no_such_key' missing or invalid structure in 'pt_BR'>"

    def test_entry_with_invalid_structure_returns_the_invalid_structure_marker(self, tmp_path) -> None:
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text(json.dumps({"bad_key": "not-a-dict"}), encoding="utf-8")
        catalog = MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)

        assert catalog.text("bad_key") == "<'bad_key' missing or invalid structure in 'pt_BR'>"

    def test_missing_placeholder_leaves_the_template_unformatted(self, tmp_path) -> None:
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text(
            json.dumps({"greeting": {"message": "Hello {name}"}}), encoding="utf-8"
        )
        catalog = MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)

        assert catalog.text("greeting") == "Hello {name}"
        assert catalog.text("greeting", wrong_param="x") == "Hello {name}"

    def test_missing_message_field_falls_back_to_the_missing_marker(self, tmp_path) -> None:
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text(json.dumps({"no_message": {}}), encoding="utf-8")
        catalog = MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)

        assert catalog.text("no_message") == "<Message for 'no_message' missing in 'pt_BR'>"


class TestMessageCatalogRenderIssue:
    """`render(issue)` delegates to `text(issue.message_key, **issue.params)`."""

    def test_render_interpolates_issue_params(self, tmp_path) -> None:
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text(
            json.dumps({"rule.DESC-004.error": {"message": "Valor {value} invalido, esperado {expected}"}}),
            encoding="utf-8",
        )
        catalog = MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)
        issue = Issue(
            rule_id="DESC-004",
            severity=Severity.ERROR,
            sheet="descricao.xlsx",
            row=3,
            column="codigo",
            message_key="rule.DESC-004.error",
            params={"value": "Abc.", "expected": "Abc"},
        )

        assert catalog.render(issue) == "Valor Abc. invalido, esperado Abc"


class TestMessageCatalogErrors:
    """Loading errors are raised, never printed (`.claude/rules/security.md`, "No prints")."""

    def test_missing_locale_directory_raises_catalog_not_found(self, tmp_path) -> None:
        with pytest.raises(CatalogNotFoundError):
            MessageCatalog(locale="xx_XX", catalog_dir=tmp_path)

    def test_missing_messages_file_raises_catalog_not_found(self, tmp_path) -> None:
        (tmp_path / "pt_BR").mkdir()

        with pytest.raises(CatalogNotFoundError):
            MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)

    def test_malformed_json_raises_catalog_invalid(self, tmp_path) -> None:
        locale_dir = tmp_path / "pt_BR"
        locale_dir.mkdir()
        (locale_dir / "messages.json").write_text("{not valid json", encoding="utf-8")

        with pytest.raises(CatalogInvalidError):
            MessageCatalog(locale="pt_BR", catalog_dir=tmp_path)
