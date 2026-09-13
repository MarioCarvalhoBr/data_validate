#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Process-wide default translator for `helpers/common/**` message-building helpers.

ARC-005: every message-building helper under `helpers/common/**` accepts an optional
`translate: Callable[..., str]` parameter so no helper ever writes a hardcoded pt-BR
literal (`.claude/rules/i18n.md`). Models pass `self.context.language_manager.text` for
real, locale-aware rendering; a caller that does not supply one (existing direct-helper
unit tests, `rules/*.py` call sites that discard the returned message) falls back to
this module's cached pt-BR `LanguageManager`, so the rendered text is unchanged from
before this helper existed, and the fallback itself is never a Python string literal.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Callable

from data_validate.helpers.tools.locale.language_manager import LanguageManager


@lru_cache(maxsize=1)
def get_default_translate() -> Callable[..., str]:
    """Return a process-wide cached pt-BR translator.

    Built once per process (the catalog is read-only i18n data, immutable once loaded —
    the same justification `ARC-002` accepts for the `SHEET`/`METADATA` module
    singletons) and reused by every helper call that does not receive an explicit
    `translate` callable.

    Returns:
        Callable[..., str]: `LanguageManager(locale="pt_BR").text`, matching the
        `(key: str, **params) -> str` shape every helper's `translate` parameter expects.
    """
    return LanguageManager(locale="pt_BR").text
