#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Tests for `data_validate.helpers.common.default_translate`."""

from __future__ import annotations

from data_validate.helpers.common.default_translate import get_default_translate


class TestGetDefaultTranslate:
    def test_returns_callable_bound_to_pt_br_catalog(self):
        translate = get_default_translate()

        rendered = translate("invalid_language", default_lang="pt_BR")

        assert "Idioma inválido" in rendered

    def test_result_is_cached_across_calls(self):
        first = get_default_translate()
        second = get_default_translate()

        assert first is second

    def test_missing_key_falls_back_like_language_manager(self):
        translate = get_default_translate()

        rendered = translate("this_key_does_not_exist_anywhere")

        assert "this_key_does_not_exist_anywhere" in rendered
