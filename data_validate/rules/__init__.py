#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Rule registry and execution engine (ARC-017, ARC-001, ARC-008; ADR-0006).

This package is the core described by ADR-0006: a declarative `RuleSpec` registered in a
`RuleRegistry`, executed in topological order by `Engine`, with unmet prerequisites surfaced as a
distinct, reasoned `SKIPPED` outcome instead of silently not running (closing the `set_not_executed`
placeholder gap tracked as ARC-008) and a crashing rule isolated into a `FAILED` outcome instead of
being mistaken for a clean run (SEC-004 at the engine level).

Phase 3a built the registry/engine core with nothing wired into the legacy pipeline. Phase 3b
(ARC-017) ports the first validator, `FileStructureValidator`, onto it: `structure.py` declares
`STRUCTURE_REGISTRY` (the `STRUCT-001`…`STRUCT-006` `RuleSpec`s) and `legacy_adapter.py` renders an
`Engine.run(...)`'s outcomes into the legacy `ValidationReport`
(`controllers/spreadsheet_processor.py::SpreadsheetProcessor._run_structure_rules`) — the first
call site outside `tests/unit/rules/` and the reusable seam every later validator port reuses. See
`.specs/architecture/target-architecture.md` (`Rule`, `RuleContext`, `RuleOutcome` sketches) and
`docs/adrs/0006-rule-registry-with-prerequisites.md`.
"""

from __future__ import annotations

from data_validate.rules.context import RuleContext
from data_validate.rules.description import DESCRIPTION_REGISTRY
from data_validate.rules.engine import Engine, EngineResult, RuleOutcome, RuleStatus, SkipReason
from data_validate.rules.legacy_adapter import extend_report_from_outcomes
from data_validate.rules.registry import RegistryCycleError, RuleRegistry, RuleSpec
from data_validate.rules.structure import STRUCTURE_REGISTRY

__all__ = [
    "DESCRIPTION_REGISTRY",
    "Engine",
    "EngineResult",
    "RegistryCycleError",
    "RuleContext",
    "RuleOutcome",
    "RuleRegistry",
    "RuleSpec",
    "RuleStatus",
    "STRUCTURE_REGISTRY",
    "SkipReason",
    "extend_report_from_outcomes",
]
