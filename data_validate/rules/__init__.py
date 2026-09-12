#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Rule registry and execution engine (ARC-017, ARC-001, ARC-008; ADR-0006).

This package is the core described by ADR-0006: a declarative `RuleSpec` registered in a
`RuleRegistry`, executed in topological order by `Engine`, with unmet prerequisites surfaced as a
distinct, reasoned `SKIPPED` outcome instead of silently not running (closing the `set_not_executed`
placeholder gap tracked as ARC-008) and a crashing rule isolated into a `FAILED` outcome instead of
being mistaken for a clean run (SEC-004 at the engine level).

Nothing here is wired into the legacy pipeline yet (Phase 3a): no validator was ported to a `Rule`
module, no CLI/report call site changed. See `.specs/architecture/target-architecture.md` (`Rule`,
`RuleContext`, `RuleOutcome` sketches) and `docs/adrs/0006-rule-registry-with-prerequisites.md`.
"""

from __future__ import annotations

from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, EngineResult, RuleOutcome, RuleStatus, SkipReason
from data_validate.rules.registry import RegistryCycleError, RuleRegistry, RuleSpec

__all__ = [
    "Engine",
    "EngineResult",
    "RegistryCycleError",
    "RuleContext",
    "RuleOutcome",
    "RuleRegistry",
    "RuleSpec",
    "RuleStatus",
    "SkipReason",
]
