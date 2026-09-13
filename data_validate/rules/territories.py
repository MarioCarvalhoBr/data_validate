#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""TERR-001…002: the optional territory registry (`spd_data.json`) checks (PROTO-013, ADR-0006).

Source: maintainer decisions 2026-09-12 (`.specs/business-rules/territories.md`). Unlike every
other `rules/*.py` module, this one does not port a legacy validator -- it is new. Three decisions
fix its shape:

1. **Own verification category**: `NamesEnum.TERR` (`verification_name_territory_registry`),
   never folded into an existing category.
2. **Triggered only when `spd_data.json` is present**: both rules declare
   `requires_options=("territory_registry_present",)` (`RuleSpec.requires_options`, `rules/
   registry.py`), so an absent or malformed registry engine-skips both rules with
   `SkipReason.DISABLED_BY_OPTION` instead of running them against an empty id set --
   `SpreadsheetProcessor` sets `ctx.options["territory_registry_present"]` from the loader's own
   `TerritoryRegistry.loaded` (`helpers/tools/data_loader/api/facade.py`).
3. **Findings are always errors** (`Severity.ERROR`), never warnings -- a `valores`/
   `proporcionalidades` id absent from the registry is always rejected.

`ctx.options["territory_registry_ids"]` carries the registry's own `frozenset[int]` (empty when
absent/malformed, in which case the rules never run anyway per point 2 above).

Row numbering (`.claude/rules/dataframe-conventions.md`): `valores` is single-header (`idx + 2`);
`proporcionalidades` is double-header (`idx + 3`); `Issue.row` itself stays the raw, 0-based `idx`
either way (matching every other rule module's convention), only the rendered message's `row`
param uses the sheet-specific offset.

`proporcionalidades.id` quirk (matches `rules/proportionality.py`'s own `_proportionality_missing_id`
precedent): a real bundle's `id` column is `(<blank>, "id")` under `pandas`' `header=[0, 1]` read
(pandas renders the blank top header cell as `"Unnamed: 0_level_0"`), never `("id", "id")` --
`RuleSpec.requires` cannot name `"id"` for this sheet (a bare `"id" not in frame.columns` check on
a `MultiIndex` only matches *level 0*, which is never `"id"` here), so TERR-002 only requires the
sheet's presence and locates its `id` column itself, by level 1, before comparing any value.

Depends only on `data_validate.rules`/`data_validate.specs` and `pandas`, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

TERRITORY_REGISTRY_RULES = RuleRegistry()
"""TERR-001/TERR-002, always run last in the pipeline (`SpreadsheetProcessor._build_pipeline`)."""

_VALUES_SHEET = "valores"
_PROPORTIONALITY_SHEET = "proporcionalidades"
_ID = "id"

_CATEGORY = NamesEnum.TERR.value
_REGISTRY_PRESENT_OPTION = "territory_registry_present"
_REGISTRY_IDS_OPTION = "territory_registry_ids"


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"valores.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _registry_ids(ctx: RuleContext) -> frozenset[int]:
    """Return `ctx.options["territory_registry_ids"]` as a `frozenset[int]`, defaulting to empty."""
    value = ctx.options.get(_REGISTRY_IDS_OPTION, frozenset())
    if isinstance(value, frozenset):
        return value
    if isinstance(value, (set, list, tuple)):
        return frozenset(value)
    return frozenset()


def _proportionality_id_column(frame: pd.DataFrame) -> object | None:
    """Locate `proporcionalidades`' `id` column by level 1, or `None` when it is absent.

    See the module docstring's "quirk" note: a real bundle's `id` column is `(<blank>, "id")`,
    not `("id", "id")`, so this cannot be a simple `"id" in frame.columns` check.
    """
    if isinstance(frame.columns, pd.MultiIndex):
        for column in frame.columns:
            if column[1] == _ID:
                return cast(object, column)
        return None
    return _ID if _ID in frame.columns else None


def _unknown_id_issue(rule_id: str, filename: str, idx: int, excel_row: int, raw_value: object) -> Issue:
    """Build one "id not found in the territory registry" `Issue`, shared by TERR-001/TERR-002."""
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=filename,
        row=int(idx),
        column=_ID,
        message_key=f"rule.{rule_id}.error",
        params={"filename": filename, "row": excel_row, "value": raw_value},
        category=_CATEGORY,
    )


@TERRITORY_REGISTRY_RULES.rule(
    rule_id="TERR-001",
    category=_CATEGORY,
    requires={_VALUES_SHEET: (_ID,)},
    requires_options=(_REGISTRY_PRESENT_OPTION,),
)
def check_values_ids_in_registry(ctx: RuleContext) -> list[Issue]:
    """TERR-001: every `valores.id` must exist in the territory registry.

    Engine-skipped (never run) when `spd_data.json` is absent/malformed
    (`requires_options=("territory_registry_present",)`) or `valores`/its `id` column is missing
    (`requires`) -- matches `.specs/business-rules/territories.md`'s "skipped, not an error"
    contract for an absent file.
    """
    frame = ctx.sheet(_VALUES_SHEET)
    filename = _filename(ctx, _VALUES_SHEET)
    registry_ids = _registry_ids(ctx)

    numeric_ids = pd.to_numeric(frame[_ID], errors="coerce")
    unknown_mask = ~numeric_ids.isin(registry_ids)
    return [
        _unknown_id_issue("TERR-001", filename, idx, int(idx) + 2, frame.loc[idx, _ID])
        for idx in frame.index[unknown_mask]
    ]


@TERRITORY_REGISTRY_RULES.rule(
    rule_id="TERR-002",
    category=_CATEGORY,
    requires={_PROPORTIONALITY_SHEET: ()},
    requires_options=(_REGISTRY_PRESENT_OPTION,),
)
def check_proportionality_ids_in_registry(ctx: RuleContext) -> list[Issue]:
    """TERR-002: every `proporcionalidades.id` (level-2 header) must exist in the territory registry.

    Same engine-skip gating as TERR-001; additionally skipped when `proporcionalidades` itself is
    absent/empty (an optional sheet -- `requires`), per `.specs/business-rules/territories.md`.
    Silently reports nothing (rather than a missing-column abort) when the sheet is present but
    its own `id` column cannot be located -- an already-structurally-broken `proporcionalidades`
    sheet is PROP-001/PROP-002's concern (`models/sp_proportionality.py`), not this rule's.
    """
    frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    filename = _filename(ctx, _PROPORTIONALITY_SHEET)
    registry_ids = _registry_ids(ctx)

    id_column = _proportionality_id_column(frame)
    if id_column is None:
        return []

    id_series = frame[id_column]
    numeric_ids = pd.to_numeric(id_series, errors="coerce")
    unknown_mask = ~numeric_ids.isin(registry_ids)
    return [
        _unknown_id_issue("TERR-002", filename, idx, int(idx) + 3, id_series.loc[idx])
        for idx in id_series.index[unknown_mask]
    ]
