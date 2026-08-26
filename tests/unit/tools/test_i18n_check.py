#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/i18n_check.py."""

from __future__ import annotations

import json
from pathlib import Path

from tools import i18n_check


def _write_catalog(locale_dir: Path, entries: dict[str, str]) -> None:
    locale_dir.mkdir(parents=True, exist_ok=True)
    payload = {key: {"message": message} for key, message in entries.items()}
    (locale_dir / "messages.json").write_text(json.dumps(payload), encoding="utf-8")


class TestCheckCatalogs:
    """Test suite for check_catalogs()."""

    def test_check_catalogs_detects_missing_key(self, tmp_path, mocker) -> None:
        """A key present in one locale but absent from another is a parity error."""
        locales_dir = tmp_path / "locales"
        _write_catalog(locales_dir / "pt_BR", {"hello": "Ola {name}"})
        _write_catalog(locales_dir / "en_US", {})
        source_dir = tmp_path / "empty_source"
        source_dir.mkdir()

        mocker.patch.object(i18n_check, "_LOCALES_DIR", locales_dir)
        mocker.patch.object(i18n_check, "_SOURCE_DIR", source_dir)

        report = i18n_check.check_catalogs()

        assert report["ok"] is False
        assert report["missing_per_locale"]["en_US"] == ["hello"]
        assert "hello" in report["unused_keys"]

    def test_check_catalogs_detects_placeholder_mismatch(self, tmp_path, mocker) -> None:
        """Different named placeholders for the same key across locales is a parity error."""
        locales_dir = tmp_path / "locales"
        _write_catalog(locales_dir / "pt_BR", {"hello": "Ola {name}"})
        _write_catalog(locales_dir / "en_US", {"hello": "Hello {username}"})
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "mod.py").write_text('lm.text("hello", name="x")\n', encoding="utf-8")

        mocker.patch.object(i18n_check, "_LOCALES_DIR", locales_dir)
        mocker.patch.object(i18n_check, "_SOURCE_DIR", source_dir)

        report = i18n_check.check_catalogs()

        assert report["ok"] is False
        assert "hello" in report["placeholder_mismatches"]
        assert "hello" not in report["unused_keys"]

    def test_check_catalogs_all_ok(self, tmp_path, mocker) -> None:
        """Matching keys, matching placeholders, and a used key report as OK."""
        locales_dir = tmp_path / "locales"
        _write_catalog(locales_dir / "pt_BR", {"hello": "Ola {name}"})
        _write_catalog(locales_dir / "en_US", {"hello": "Hello {name}"})
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "mod.py").write_text('lm.text("hello", name="x")\n', encoding="utf-8")

        mocker.patch.object(i18n_check, "_LOCALES_DIR", locales_dir)
        mocker.patch.object(i18n_check, "_SOURCE_DIR", source_dir)

        report = i18n_check.check_catalogs()

        assert report["ok"] is True
        assert report["unused_keys"] == []

    def test_check_catalogs_handles_missing_locales_dir(self, tmp_path, mocker) -> None:
        """No locales directory yields an empty, OK report rather than crashing."""
        mocker.patch.object(i18n_check, "_LOCALES_DIR", tmp_path / "does_not_exist")
        mocker.patch.object(i18n_check, "_SOURCE_DIR", tmp_path)

        report = i18n_check.check_catalogs()

        assert report["locales"] == []
        assert report["ok"] is True


class TestMessagePlaceholders:
    """Test suite for _message_placeholders()."""

    def test_message_placeholders_extracts_named_fields(self) -> None:
        assert i18n_check._message_placeholders("Missing {count} of {total}") == {"count", "total"}

    def test_message_placeholders_empty_for_plain_text(self) -> None:
        assert i18n_check._message_placeholders("No placeholders here") == set()


class TestMain:
    """Test suite for main()."""

    def test_main_returns_1_on_parity_error(self, tmp_path, mocker) -> None:
        locales_dir = tmp_path / "locales"
        _write_catalog(locales_dir / "pt_BR", {"hello": "Ola"})
        _write_catalog(locales_dir / "en_US", {})
        mocker.patch.object(i18n_check, "_LOCALES_DIR", locales_dir)
        mocker.patch.object(i18n_check, "_SOURCE_DIR", tmp_path)

        assert i18n_check.main([]) == 1

    def test_main_json_output(self, tmp_path, mocker, capsys) -> None:
        locales_dir = tmp_path / "locales"
        _write_catalog(locales_dir / "pt_BR", {"hello": "Ola"})
        _write_catalog(locales_dir / "en_US", {"hello": "Hello"})
        mocker.patch.object(i18n_check, "_LOCALES_DIR", locales_dir)
        mocker.patch.object(i18n_check, "_SOURCE_DIR", tmp_path)

        exit_code = i18n_check.main(["--json"])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
