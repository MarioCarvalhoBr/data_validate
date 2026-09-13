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
call site outside `tests/unit/rules/` and the reusable seam every later validator port reuses.
Phase 3 Port 4 adds `temporal_reference.py` (`TEMPORAL_REGISTRY`, `TEMP-001`…`TEMP-003`) and
`scenario.py` (`SCENARIO_REGISTRY`, `SCEN-003`…`SCEN-004`). Phase 3 Port 5 adds `value.py`
(`VALUE_REGISTRY`, `VAL-002`…`VAL-005`), replacing the deleted `validators.SpValueValidator`.
Phase 3 Port 6 adds `legend.py` (`LEGEND_REGISTRY`, `LEG-012`…`LEG-015`), replacing the deleted
`validators.SpLegendValidator`. Phase 3 Port 7 adds `proportionality.py`
(`PROPORTIONALITY_REGISTRY`, `PROP-003`…`PROP-010`), replacing the deleted
`validators.SpProportionalityValidator`. Phase 3 Port 8 (the migration's last validator port)
adds `spell.py` (`SPELL_REGISTRY`, `SPELL-001`…`SPELL-005`), replacing the deleted
`validators.SpellCheckerValidator` — with it, `data_validate/validators/` is deleted entirely
(ARC-008) and every model's `run()`/`SpreadsheetProcessor.run()` is called explicitly by its
caller instead of automatically from `__init__` (ARC-001). See
`.specs/architecture/target-architecture.md` (`Rule`, `RuleContext`, `RuleOutcome` sketches) and
`docs/adrs/0006-rule-registry-with-prerequisites.md`.
"""

from __future__ import annotations

from typing import NamedTuple

from data_validate.rules.composition import COMPOSITION_REGISTRY, CompositionFacts, compute_composition_facts
from data_validate.rules.context import RuleContext
from data_validate.rules.description import DESCRIPTION_REGISTRY
from data_validate.rules.engine import Engine, EngineResult, RuleOutcome, RuleStatus, SkipReason
from data_validate.rules.legacy_adapter import extend_report_from_outcomes
from data_validate.rules.legend import LEGEND_REGISTRY
from data_validate.rules.proportionality import PROPORTIONALITY_REGISTRY
from data_validate.rules.registry import RegistryCycleError, RuleRegistry, RuleSpec
from data_validate.rules.scenario import SCENARIO_REGISTRY
from data_validate.rules.spell import SPELL_REGISTRY, SpellBackend
from data_validate.rules.structure import STRUCTURE_REGISTRY
from data_validate.rules.temporal_reference import TEMPORAL_REGISTRY
from data_validate.rules.value import VALUE_REGISTRY

#: Every rule registry the pipeline runs, in the same fixed order
#: `SpreadsheetProcessor._build_pipeline` runs them (registry-to-registry order is still
#: explicit, per ARC-017's "Done" note — only each registry's *internal* order is topological).
ALL_REGISTRIES: tuple[RuleRegistry, ...] = (
    STRUCTURE_REGISTRY,
    SPELL_REGISTRY,
    DESCRIPTION_REGISTRY,
    COMPOSITION_REGISTRY,
    TEMPORAL_REGISTRY,
    PROPORTIONALITY_REGISTRY,
    VALUE_REGISTRY,
    SCENARIO_REGISTRY,
    LEGEND_REGISTRY,
)


class RuleSummary(NamedTuple):
    """One row of `list_all_rules()` — ARC-011's `--list-rules`.

    Attributes:
        rule_id: Stable rule identifier (`"DESC-004"`).
        category: The report bucket this rule belongs to (`RuleSpec.category`).
        severity: The rule's default severity (`RuleSpec.severity_default`), as plain text.
    """

    rule_id: str
    category: str
    severity: str


def list_all_rules() -> tuple[RuleSummary, ...]:
    """List every rule registered across `ALL_REGISTRIES`, sorted by rule ID.

    ARC-011: backs the CLI's `--list-rules` flag — one `RuleSummary` per rule, independent of
    any particular run/bundle (no `RuleContext` needed), so it can print and exit before any
    input folder is even read.

    Returns:
        tuple[RuleSummary, ...]: One entry per registered rule, sorted by `rule_id`.
    """
    return tuple(
        sorted(
            (
                RuleSummary(rule_id=spec.rule_id, category=spec.category, severity=spec.severity_default.value)
                for registry in ALL_REGISTRIES
                for spec in registry
            ),
            key=lambda summary: summary.rule_id,
        )
    )


__all__ = [
    "ALL_REGISTRIES",
    "COMPOSITION_REGISTRY",
    "CompositionFacts",
    "DESCRIPTION_REGISTRY",
    "Engine",
    "EngineResult",
    "RegistryCycleError",
    "LEGEND_REGISTRY",
    "PROPORTIONALITY_REGISTRY",
    "RuleContext",
    "RuleOutcome",
    "RuleRegistry",
    "RuleSpec",
    "RuleStatus",
    "RuleSummary",
    "SCENARIO_REGISTRY",
    "SPELL_REGISTRY",
    "STRUCTURE_REGISTRY",
    "SkipReason",
    "SpellBackend",
    "TEMPORAL_REGISTRY",
    "VALUE_REGISTRY",
    "compute_composition_facts",
    "extend_report_from_outcomes",
    "list_all_rules",
]
