#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""`RuleContext`: the immutable, read-only view of a bundle a `Rule.check` receives (ADR-0006).

Mirrors the `RuleContext` sketch in `.specs/architecture/target-architecture.md`, adapted to what
this slice actually needs: sheets keyed by name rather than by a not-yet-built `SheetFrame`, plus a
`cleaned` mapping for per-column cleaned `Series` (the eventual `normalizing` layer's output), a
`translate` callable in place of the full `MessageCatalog`/`i18n` dependency, and a `clock` for any
rule that needs "now" without calling `datetime.now()` itself (`.claude/rules/coding-standards.md`
"no global state"). Depends only on the standard library and `pandas`, per
`.claude/rules/architecture-boundaries.md` (`rules` depends on `specs` and `util`, never the other
way around; nothing here reaches into `loading`/`normalizing`/`reporting`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

import pandas as pd

_EMPTY_FRAME_COLUMNS: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleContext:
    """Read-only bundle handed to every `Rule.check` call.

    A rule never mutates any value reachable from a `RuleContext` (`.claude/rules/
    dataframe-conventions.md`); the engine builds one `RuleContext` per run and reuses it,
    unchanged, across every rule.

    Attributes:
        sheets: Normalised frame per sheet name (e.g. `"descricao"`); a sheet absent from the
            bundle is simply absent from this mapping — use `has_sheet`/`sheet` rather than
            indexing directly so a missing sheet reads as "empty", not a `KeyError`.
        cleaned: Per-sheet, per-column cleaned `Series` (the eventual `normalizing` layer's
            output), keyed the same way as `sheets`.
        options: Run-time flags and settings a rule may consult (e.g. the scenario symbol list,
            `no_warning_titles_length`); kept as an untyped `Mapping[str, object]` in this slice
            rather than the target architecture's `Options` dataclass, which does not exist yet.
        translate: Renders a catalog key (plus named parameters) into localised text — the same
            shape as `MessageCatalog.text`/`context.lm.text` (`.claude/rules/i18n.md`); a rule
            never builds user-facing text itself.
        clock: Returns "now"; a rule that needs a timestamp calls `ctx.clock()` instead of
            `datetime.now()` directly, so it stays pure and testable.
    """

    sheets: Mapping[str, pd.DataFrame]
    cleaned: Mapping[str, Mapping[str, pd.Series]]
    options: Mapping[str, object]
    translate: Callable[..., str]
    clock: Callable[[], datetime]

    def __post_init__(self) -> None:
        """Freeze the top-level mappings into read-only proxies.

        Only the mappings themselves are frozen (matching `Issue.params`'s precedent in
        `data_validate/specs/issues.py`); the `pd.DataFrame`/`pd.Series` values they hold are not
        deep-copied — callers must not mutate them once a `RuleContext` is built.
        """
        object.__setattr__(self, "sheets", MappingProxyType(dict(self.sheets)))
        object.__setattr__(
            self,
            "cleaned",
            MappingProxyType({name: MappingProxyType(dict(columns)) for name, columns in self.cleaned.items()}),
        )
        object.__setattr__(self, "options", MappingProxyType(dict(self.options)))

    def has_sheet(self, name: str) -> bool:
        """Return whether `name` is present in `sheets`.

        Args:
            name: Sheet name to look up (e.g. `"descricao"`).

        Returns:
            bool: `True` if the sheet was loaded (regardless of whether it has any rows).
        """
        return name in self.sheets

    def sheet(self, name: str) -> pd.DataFrame:
        """Return the frame for `name`, or an empty frame when the sheet is absent.

        Args:
            name: Sheet name to look up (e.g. `"descricao"`).

        Returns:
            pd.DataFrame: `self.sheets[name]` if present, otherwise a fresh empty `DataFrame`
                (never a shared instance, so a caller cannot accidentally observe another
                caller's mutation of it).
        """
        if name in self.sheets:
            return self.sheets[name]
        return pd.DataFrame(columns=list(_EMPTY_FRAME_COLUMNS))
