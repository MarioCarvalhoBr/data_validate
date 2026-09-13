#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""`RuleSpec` and `RuleRegistry`: declared rules and their topological execution order (ADR-0006).

Replaces `controllers/spreadsheet_processor.py`'s hand-ordered validator construction (ARC-017)
and `validators/spreadsheets/base/base_validator.py`'s ad hoc, per-validator prerequisite checks
(ARC-008) with one declarative structure: a `RuleSpec` names the sheets/columns it `requires` and
the rule IDs it `depends_on`; `RuleRegistry.topological_order()` turns the whole set of registered
specs into one deterministic execution order, so a future `--list-rules` needs no separate
bookkeeping (ADR-0006's "positive consequences").

Depends only on `data_validate.specs` and the standard library, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from data_validate.rules.context import RuleContext
from data_validate.specs.issues import Issue, Severity

RULE_ID_PATTERN = re.compile(r"^(STRUCT|DESC|COMP|VAL|TEMP|SCEN|LEG|PROP|SPELL|CLEAN|TERR)-\d{3}$")
"""Stable rule-ID shape a `RuleSpec.rule_id` must match.

Kept as its own compiled pattern (rather than importing `Issue`'s private
`_RULE_ID_PATTERN`) because `rules` depends only on `specs`'s public surface
(`.claude/rules/architecture-boundaries.md`); the two patterns must be kept identical, and both
are exercised by `tests/unit/specs/test_issues.py` and `tests/unit/rules/test_registry.py`
respectively — a divergence would show up as one accepting an ID the other rejects.
"""


class RegistryCycleError(ValueError):
    """Raised by `RuleRegistry.topological_order` when `depends_on` edges form a cycle.

    Attributes:
        unresolved: Rule IDs that could not be ordered because they (transitively) depend on one
            another. This is the *set* left over once every rule with no remaining unmet
            dependency has been placed — it names every rule involved in or blocked by the cycle,
            not necessarily the minimal cycle itself (a superset is exact enough to debug a
            misdeclared `depends_on`, and finding the minimal cycle is not needed for that).
    """

    def __init__(self, unresolved: Sequence[str]) -> None:
        self.unresolved: tuple[str, ...] = tuple(unresolved)
        joined = ", ".join(self.unresolved)
        super().__init__(f"rule dependency cycle detected among: {joined}")


@dataclass(frozen=True)
class RuleSpec:
    """One registered rule: identity, prerequisites, and the check function itself.

    Attributes:
        rule_id: Stable rule identifier (`"DESC-004"`); must match `RULE_ID_PATTERN` (the same
            shape `Issue.rule_id` enforces).
        category: The report bucket this rule belongs to (a `NamesEnum`-compatible key, e.g.
            `"sequential_codes"`), used to group issues in the eventual report model.
        severity_default: The severity this rule's findings use by default; surfaced for
            documentation and a future `--list-rules`, not applied to issues by the engine in
            this slice — a rule's own `Issue.severity` is authoritative (see `Rule.check`).
        requires: Sheet name -> required column names. An empty tuple means "the sheet must be
            present and non-empty, no specific column required"; a sheet name absent from this
            mapping is not checked at all before `check()` runs.
        depends_on: Rule IDs that must not have been `SKIPPED` or `FAILED` before this rule runs
            (see `Engine`'s skip semantics) — an issue-producing dependency does *not* block.
        check: Pure function computing this rule's findings from a `RuleContext`.
        requires_options: `ctx.options` keys that must all be truthy for this rule to run; a
            falsy/absent key skips the rule with `SkipReason.DISABLED_BY_OPTION`
            (`.specs/architecture/error-model.md`'s `engine.skipped.disabled_by_option`).
            PROTO-013's first consumer: `TERR-001`/`TERR-002` declare
            `requires_options=("territory_registry_present",)` so an absent/malformed
            `spd_data.json` registry engine-skips both rules instead of running them against an
            empty id set. Defaults to no option gate.

    Raises:
        ValueError: If `rule_id` does not match `RULE_ID_PATTERN`.
    """

    rule_id: str
    category: str
    severity_default: Severity
    requires: Mapping[str, tuple[str, ...]]
    depends_on: tuple[str, ...]
    check: Callable[[RuleContext], list[Issue]]
    requires_options: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate `rule_id` and freeze `requires` into a read-only mapping."""
        if not RULE_ID_PATTERN.match(self.rule_id):
            raise ValueError(f"RuleSpec.rule_id {self.rule_id!r} does not match {RULE_ID_PATTERN.pattern!r}")
        object.__setattr__(self, "requires", MappingProxyType(dict(self.requires)))
        object.__setattr__(self, "depends_on", tuple(self.depends_on))
        object.__setattr__(self, "requires_options", tuple(self.requires_options))


class RuleRegistry:
    """Registers `RuleSpec`s and resolves their topological execution order.

    Rules are kept in registration order internally (a plain `dict` on Python 3.12+ preserves
    insertion order); `topological_order()` uses that order to break ties between rules that are
    simultaneously ready to run, matching today's hand-ordered pipeline sequence (ADR-0006).
    """

    def __init__(self) -> None:
        self._specs: dict[str, RuleSpec] = {}

    def register(self, spec: RuleSpec) -> None:
        """Add `spec` to the registry.

        Args:
            spec: The rule to register.

        Raises:
            ValueError: If `spec.rule_id` is already registered.
        """
        if spec.rule_id in self._specs:
            raise ValueError(f"rule {spec.rule_id!r} is already registered")
        self._specs[spec.rule_id] = spec

    def get(self, rule_id: str) -> RuleSpec:
        """Return the registered `RuleSpec` for `rule_id`.

        Args:
            rule_id: The rule ID to look up.

        Returns:
            RuleSpec: The registered spec.

        Raises:
            KeyError: If no rule with `rule_id` is registered.
        """
        try:
            return self._specs[rule_id]
        except KeyError as missing_rule:
            raise KeyError(f"no rule registered with id {rule_id!r}") from missing_rule

    def __iter__(self) -> Iterator[RuleSpec]:
        """Iterate registered specs in registration order."""
        return iter(self._specs.values())

    def __len__(self) -> int:
        """Return the number of registered specs."""
        return len(self._specs)

    def topological_order(self) -> tuple[str, ...]:
        """Resolve a topological order over `depends_on`, ties broken by registration order.

        Uses a stable variant of Kahn's algorithm: repeated left-to-right passes over rules in
        registration order, appending every rule whose remaining dependency count is currently
        zero. Rules that become ready mid-pass (because an earlier rule in the same pass was
        just placed) are still only appended in a later pass, so two rules that are ready
        *at the same time* keep their original registration order.

        Returns:
            tuple[str, ...]: Every registered rule ID, ordered so a rule always comes after every
                rule listed in its `depends_on`.

        Raises:
            ValueError: If a rule's `depends_on` names a `rule_id` that is not registered.
            RegistryCycleError: If `depends_on` edges form a cycle, so no valid order exists.
        """
        for spec in self._specs.values():
            for dependency_id in spec.depends_on:
                if dependency_id not in self._specs:
                    raise ValueError(f"rule {spec.rule_id!r} depends on unregistered rule {dependency_id!r}")

        remaining_dependencies: dict[str, int] = {
            rule_id: len(spec.depends_on) for rule_id, spec in self._specs.items()
        }
        dependents: dict[str, list[str]] = {rule_id: [] for rule_id in self._specs}
        for rule_id, spec in self._specs.items():
            for dependency_id in spec.depends_on:
                dependents[dependency_id].append(rule_id)

        registration_order = tuple(self._specs)
        resolved: set[str] = set()
        order: list[str] = []
        while len(order) < len(registration_order):
            newly_resolved: list[str] = []
            for rule_id in registration_order:
                if rule_id in resolved:
                    continue
                if remaining_dependencies[rule_id] == 0:
                    newly_resolved.append(rule_id)
            if not newly_resolved:
                unresolved = tuple(rule_id for rule_id in registration_order if rule_id not in resolved)
                raise RegistryCycleError(unresolved)
            for rule_id in newly_resolved:
                resolved.add(rule_id)
                order.append(rule_id)
                for dependent_id in dependents[rule_id]:
                    remaining_dependencies[dependent_id] -= 1
        return tuple(order)

    def rule(
        self,
        *,
        rule_id: str,
        category: str,
        requires: Mapping[str, tuple[str, ...]] | None = None,
        depends_on: tuple[str, ...] = (),
        severity_default: Severity = Severity.ERROR,
        requires_options: tuple[str, ...] = (),
    ) -> Callable[[Callable[[RuleContext], list[Issue]]], Callable[[RuleContext], list[Issue]]]:
        """Decorator form of `register`: wraps and registers a `check` function in one step.

        Args:
            rule_id: Stable rule identifier, see `RuleSpec.rule_id`.
            category: Report bucket, see `RuleSpec.category`.
            requires: Sheet -> required columns, see `RuleSpec.requires`. Defaults to no
                requirements.
            depends_on: Rule IDs this rule depends on, see `RuleSpec.depends_on`. Defaults to no
                dependencies.
            severity_default: See `RuleSpec.severity_default`. Defaults to `Severity.ERROR`.
            requires_options: `ctx.options` keys that must all be truthy, see
                `RuleSpec.requires_options`. Defaults to no option gate.

        Returns:
            Callable: A decorator that registers the wrapped function unchanged (so it stays
                directly callable/testable on its own) and returns it as-is.
        """

        def decorator(check: Callable[[RuleContext], list[Issue]]) -> Callable[[RuleContext], list[Issue]]:
            self.register(
                RuleSpec(
                    rule_id=rule_id,
                    category=category,
                    severity_default=severity_default,
                    requires=requires if requires is not None else {},
                    depends_on=depends_on,
                    check=check,
                    requires_options=requires_options,
                )
            )
            return check

        return decorator
