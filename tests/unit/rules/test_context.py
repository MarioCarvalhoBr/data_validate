#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `RuleContext` (ARC-017, ADR-0006).

Covers the `sheet`/`has_sheet` helpers, immutability of the top-level mappings, and that a
missing sheet reads as empty rather than raising (`.claude/rules/testing.md`).
"""

from __future__ import annotations

from datetime import datetime, UTC
from types import MappingProxyType

import pandas as pd
import pytest
from tests.factories import make_description_frame

from data_validate.rules.context import RuleContext


def _make_context(**overrides: object) -> RuleContext:
    """Build a `RuleContext` with sensible defaults, overridable per test."""
    defaults: dict[str, object] = {
        "sheets": {"descricao": make_description_frame()},
        "cleaned": {},
        "options": {},
        "translate": lambda key, **params: key,
        "clock": lambda: datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return RuleContext(**defaults)  # type: ignore[arg-type]


class TestRuleContextSheetAccess:
    """`has_sheet`/`sheet` behavior for present and absent sheets."""

    def test_has_sheet_true_when_present(self) -> None:
        ctx = _make_context()
        assert ctx.has_sheet("descricao") is True

    def test_has_sheet_false_when_absent(self) -> None:
        ctx = _make_context()
        assert ctx.has_sheet("legenda") is False

    def test_sheet_returns_the_stored_frame(self) -> None:
        frame = make_description_frame()
        ctx = _make_context(sheets={"descricao": frame})
        pd.testing.assert_frame_equal(ctx.sheet("descricao"), frame)

    def test_sheet_returns_empty_frame_when_absent(self) -> None:
        ctx = _make_context()
        result = ctx.sheet("legenda")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_sheet_returns_a_fresh_empty_frame_each_call(self) -> None:
        ctx = _make_context()
        first = ctx.sheet("legenda")
        second = ctx.sheet("legenda")
        assert first is not second


class TestRuleContextImmutability:
    """Top-level mappings are frozen into read-only proxies."""

    def test_sheets_is_a_mapping_proxy(self) -> None:
        ctx = _make_context()
        assert isinstance(ctx.sheets, MappingProxyType)

    def test_options_is_a_mapping_proxy(self) -> None:
        ctx = _make_context(options={"no_spellchecker": True})
        assert isinstance(ctx.options, MappingProxyType)
        assert ctx.options["no_spellchecker"] is True

    def test_cleaned_and_its_per_sheet_columns_are_mapping_proxies(self) -> None:
        column = pd.Series([1, 2, 3], name="codigo")
        ctx = _make_context(cleaned={"descricao": {"codigo": column}})
        assert isinstance(ctx.cleaned, MappingProxyType)
        assert isinstance(ctx.cleaned["descricao"], MappingProxyType)
        pd.testing.assert_series_equal(ctx.cleaned["descricao"]["codigo"], column)

    def test_context_is_frozen(self) -> None:
        ctx = _make_context()
        with pytest.raises(AttributeError):
            ctx.options = {}  # type: ignore[misc]


class TestRuleContextCallables:
    """`translate`/`clock` are stored and callable as given."""

    def test_translate_is_called_with_named_params(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def translate(key: str, **params: object) -> str:
            calls.append((key, params))
            return "rendered"

        ctx = _make_context(translate=translate)
        result = ctx.translate("rule.DESC-004.error", value="Abc.")
        assert result == "rendered"
        assert calls == [("rule.DESC-004.error", {"value": "Abc."})]

    def test_clock_returns_the_injected_time(self) -> None:
        fixed = datetime(2030, 5, 17, tzinfo=UTC)
        ctx = _make_context(clock=lambda: fixed)
        assert ctx.clock() == fixed
