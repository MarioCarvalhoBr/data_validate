#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""`Engine`: runs a `RuleRegistry` over a `RuleContext`, producing one `RuleOutcome` per rule.

Replaces `validators/spreadsheets/base/base_validator.py::build_reports`'s plain `for` loop and
its `except Exception as e:` that turns any crash into a normal-looking error string
(ADR-0006, SEC-004): here, an unmet prerequisite is a distinct, reasoned `SKIPPED` outcome, and a
crashing rule is a distinct `FAILED` outcome that a future CLI can map to a dedicated exit code
(`.specs/architecture/error-model.md`), never silently absorbed as "the bundle is valid".

Execution is sequential in this slice (no `ProcessPoolExecutor` yet — PERF-007), but each rule is
run through one per-rule method (`_run_one`) that only reads its own prerequisites and the
already-computed outcomes of earlier rules, so a future pool only needs to parallelise the loop
in `Engine.run`, not restructure this module.

Depends only on `data_validate.rules.context`/`data_validate.rules.registry` and
`data_validate.specs`, per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry, RuleSpec
from data_validate.specs.issues import Issue, ValidationResult


class RuleStatus(StrEnum):
    """Outcome status of one rule's execution attempt."""

    PASSED = "passed"
    """`check()` ran and returned no issues."""

    ISSUES = "issues"
    """`check()` ran and returned at least one issue (error and/or warning severity)."""

    SKIPPED = "skipped"
    """`check()` did not run: an unmet `requires`/`depends_on` prerequisite (see `SkipReason`)."""

    FAILED = "failed"
    """`check()` raised; the exception is captured, never allowed to crash the engine."""


class SkipReason(StrEnum):
    """Catalog-style keys naming why a rule was `SKIPPED` (`.specs/architecture/error-model.md`).

    These are the same key shapes `error-model.md` documents for `RuleOutcome.reason`
    (`engine.skipped.missing_sheet`, `engine.skipped.missing_column`,
    `engine.skipped.dependency_failed`, `engine.skipped.disabled_by_option`);
    `DEPENDENCY_SKIPPED` is this slice's addition, needed because `depends_on` blocks on either a
    `SKIPPED` or a `FAILED` upstream rule and the two deserve a distinguishable reason.
    """

    MISSING_SHEET = "engine.skipped.missing_sheet"
    MISSING_COLUMN = "engine.skipped.missing_column"
    DEPENDENCY_SKIPPED = "engine.skipped.dependency_skipped"
    DEPENDENCY_FAILED = "engine.skipped.dependency_failed"
    DISABLED_BY_OPTION = "engine.skipped.disabled_by_option"
    """PROTO-013's first consumer: a `RuleSpec.requires_options` key that is falsy/absent in
    `ctx.options` (e.g. `territory_registry_present` when `spd_data.json` was not provided)."""


@dataclass(frozen=True)
class RuleOutcome:
    """The result of attempting to run one rule.

    Attributes:
        rule_id: The rule this outcome belongs to.
        status: What happened (see `RuleStatus`).
        issues: Findings produced by `check()`; always empty unless `status is RuleStatus.ISSUES`.
        skip_reason: For `SKIPPED`, one of `SkipReason`'s values; for `FAILED`, `repr(exception)`
            (this slice has no separate error field — see the module docstring); `None` for
            `PASSED`/`ISSUES`.
        duration_ms: Wall-clock time spent on this rule, including prerequisite checks, in
            milliseconds.
    """

    rule_id: str
    status: RuleStatus
    issues: tuple[Issue, ...]
    skip_reason: str | None
    duration_ms: float


@dataclass(frozen=True)
class EngineResult:
    """Every `RuleOutcome` from one `Engine.run` call, in execution order.

    Attributes:
        outcomes: One `RuleOutcome` per rule that was executed (see `Engine.run`'s `only`
            parameter for which rules that is).
    """

    outcomes: tuple[RuleOutcome, ...]

    @property
    def validation_result(self) -> ValidationResult:
        """Flatten every outcome's issues into one `ValidationResult`, in execution order.

        Returns:
            ValidationResult: All issues from all outcomes, concatenated in the order their
                rules ran.
        """
        issues: list[Issue] = []
        for outcome in self.outcomes:
            issues.extend(outcome.issues)
        return ValidationResult(issues=tuple(issues))


class Engine:
    """Runs every rule in a `RuleRegistry`, in topological order, over one `RuleContext`."""

    def __init__(self, registry: RuleRegistry) -> None:
        """Store the registry to run.

        Args:
            registry: The rules to execute.
        """
        self._registry = registry

    def run(self, ctx: RuleContext, only: set[str] | None = None) -> EngineResult:
        """Execute registered rules over `ctx`, in topological order.

        Args:
            ctx: The immutable context every rule's `check()` receives.
            only: When given, restricts execution to exactly these rule IDs (still in
                topological order); a rule ID outside `only` is not executed and produces no
                `RuleOutcome` at all. A `depends_on` reference to a rule that was excluded this
                way is treated as satisfied (not blocking) — the dependency simply was not part
                of this run, which is different from having run and been `SKIPPED`/`FAILED`.
                `None` (the default) runs every registered rule.

        Returns:
            EngineResult: One outcome per executed rule, in the order they ran.
        """
        order = self._registry.topological_order()
        if only is not None:
            order = tuple(rule_id for rule_id in order if rule_id in only)

        outcomes_by_id: dict[str, RuleOutcome] = {}
        outcomes: list[RuleOutcome] = []
        for rule_id in order:
            spec = self._registry.get(rule_id)
            outcome = self._run_one(spec, ctx, outcomes_by_id)
            outcomes_by_id[rule_id] = outcome
            outcomes.append(outcome)
        return EngineResult(outcomes=tuple(outcomes))

    def _run_one(
        self,
        spec: RuleSpec,
        ctx: RuleContext,
        previous_outcomes: Mapping[str, RuleOutcome],
    ) -> RuleOutcome:
        """Run one rule, honoring its prerequisites and isolating any crash.

        Args:
            spec: The rule to run.
            ctx: The context to pass to `spec.check` if prerequisites are met.
            previous_outcomes: Outcomes of every rule already run in this `Engine.run` call,
                keyed by rule ID — used to resolve `spec.depends_on`.

        Returns:
            RuleOutcome: `SKIPPED` if a prerequisite is unmet, `FAILED` if `check()` raised,
                otherwise `PASSED`/`ISSUES` depending on whether `check()` returned any issues.
        """
        started_at = time.perf_counter()

        skip_reason = self._unmet_prerequisite(spec, ctx, previous_outcomes)
        if skip_reason is not None:
            return RuleOutcome(
                rule_id=spec.rule_id,
                status=RuleStatus.SKIPPED,
                issues=(),
                skip_reason=skip_reason,
                duration_ms=self._elapsed_ms(started_at),
            )

        try:
            issues = list(spec.check(ctx))
        except Exception as crash:
            # Deliberate broad catch: the engine's entire purpose here is to isolate an
            # unexpected failure in *any* rule (a KeyError, a TypeError, a pandas exception -
            # the specific type is unknowable in advance because rules are third-party-shaped
            # plugins from the engine's point of view) into a FAILED outcome instead of letting
            # it crash the whole validation run or, worse, be silently absorbed as a clean pass.
            return RuleOutcome(
                rule_id=spec.rule_id,
                status=RuleStatus.FAILED,
                issues=(),
                skip_reason=repr(crash),
                duration_ms=self._elapsed_ms(started_at),
            )

        status = RuleStatus.ISSUES if issues else RuleStatus.PASSED
        return RuleOutcome(
            rule_id=spec.rule_id,
            status=status,
            issues=tuple(issues),
            skip_reason=None,
            duration_ms=self._elapsed_ms(started_at),
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        """Milliseconds elapsed since `started_at` (a `time.perf_counter()` reading)."""
        return (time.perf_counter() - started_at) * 1000

    @staticmethod
    def _unmet_prerequisite(
        spec: RuleSpec,
        ctx: RuleContext,
        previous_outcomes: Mapping[str, RuleOutcome],
    ) -> str | None:
        """Return the `SkipReason` for `spec`, or `None` if every prerequisite is met.

        Checks `spec.requires` before `spec.requires_options` before `spec.depends_on`, so a rule
        missing both its sheet and a healthy dependency is reported for the sheet, matching the
        order they are declared in `RuleSpec`.
        """
        for sheet_name, required_columns in spec.requires.items():
            if not ctx.has_sheet(sheet_name):
                return SkipReason.MISSING_SHEET
            frame = ctx.sheet(sheet_name)
            if frame.empty:
                return SkipReason.MISSING_SHEET
            for column_name in required_columns:
                if column_name not in frame.columns:
                    return SkipReason.MISSING_COLUMN

        for option_key in spec.requires_options:
            if not ctx.options.get(option_key, False):
                return SkipReason.DISABLED_BY_OPTION

        for dependency_id in spec.depends_on:
            dependency_outcome = previous_outcomes.get(dependency_id)
            if dependency_outcome is None:
                continue
            if dependency_outcome.status is RuleStatus.SKIPPED:
                return SkipReason.DEPENDENCY_SKIPPED
            if dependency_outcome.status is RuleStatus.FAILED:
                return SkipReason.DEPENDENCY_FAILED

        return None
