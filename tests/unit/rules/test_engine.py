#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `Engine`/`RuleOutcome`/`EngineResult` (ARC-017, ARC-001, ARC-008, ADR-0006).

Table-driven coverage of the engine's skip semantics (`requires`/`depends_on`), crash isolation,
duration measurement, `only=` filtering, and `EngineResult.validation_result` flattening
(`.claude/rules/testing.md`). Contexts are built with hand-rolled minimal sheets rather than the
full `tests/factories.py` bundle where a single-column frame is enough to exercise a prerequisite
check; `tests/factories.py` is used where a realistic `descricao` frame matters.
"""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd
from tests.factories import make_description_frame

from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus, SkipReason
from data_validate.rules.registry import RuleRegistry, RuleSpec
from data_validate.specs.issues import Issue, Severity


def _make_context(sheets: dict[str, pd.DataFrame] | None = None, **overrides: object) -> RuleContext:
    """Build a `RuleContext` with sensible defaults, overridable per test."""
    defaults: dict[str, object] = {
        "sheets": sheets if sheets is not None else {"descricao": make_description_frame()},
        "cleaned": {},
        "options": {},
        "translate": lambda key, **params: key,
        "clock": lambda: datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return RuleContext(**defaults)  # type: ignore[arg-type]


def _make_issue(rule_id: str = "DESC-001") -> Issue:
    """Build a minimal `Issue` for a check function to return."""
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet="descricao.xlsx",
        row=None,
        column=None,
        message_key=f"rule.{rule_id}.error",
        params={},
    )


def _make_spec(
    rule_id: str,
    *,
    requires: dict[str, tuple[str, ...]] | None = None,
    depends_on: tuple[str, ...] = (),
    requires_options: tuple[str, ...] = (),
    check: object = None,
) -> RuleSpec:
    """Build a `RuleSpec` whose `check` defaults to a no-op returning no issues."""

    def _default_check(ctx: RuleContext) -> list[Issue]:
        return []

    return RuleSpec(
        rule_id=rule_id,
        category="sequential_codes",
        severity_default=Severity.ERROR,
        requires=requires if requires is not None else {},
        depends_on=depends_on,
        check=check if check is not None else _default_check,  # type: ignore[arg-type]
        requires_options=requires_options,
    )


class TestEngineRunsAHealthyRule:
    """A rule with met prerequisites executes and reports PASSED/ISSUES."""

    def test_a_rule_with_no_requirements_passes_when_it_finds_nothing(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        result = Engine(registry).run(_make_context())
        assert len(result.outcomes) == 1
        outcome = result.outcomes[0]
        assert outcome.rule_id == "DESC-001"
        assert outcome.status is RuleStatus.PASSED
        assert outcome.issues == ()
        assert outcome.skip_reason is None

    def test_a_rule_that_returns_issues_reports_status_issues(self) -> None:
        issue = _make_issue("DESC-001")
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", check=lambda ctx: [issue]))
        result = Engine(registry).run(_make_context())
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.ISSUES
        assert outcome.issues == (issue,)
        assert outcome.skip_reason is None

    def test_duration_ms_is_measured_and_non_negative(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        result = Engine(registry).run(_make_context())
        assert result.outcomes[0].duration_ms >= 0.0


class TestEngineRequiresSkip:
    """`requires` unmet sheet/column prerequisites produce a SKIPPED outcome."""

    def test_missing_sheet_is_skipped_with_missing_sheet_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}))
        result = Engine(registry).run(_make_context(sheets={}))
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.SKIPPED
        assert outcome.skip_reason == SkipReason.MISSING_SHEET

    def test_empty_sheet_is_skipped_with_missing_sheet_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}))
        empty_frame = pd.DataFrame(columns=["codigo"])
        result = Engine(registry).run(_make_context(sheets={"legenda": empty_frame}))
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.SKIPPED
        assert outcome.skip_reason == SkipReason.MISSING_SHEET

    def test_missing_required_column_is_skipped_with_missing_column_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-005", requires={"descricao": ("nivel", "does_not_exist")}))
        result = Engine(registry).run(_make_context())
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.SKIPPED
        assert outcome.skip_reason == SkipReason.MISSING_COLUMN

    def test_present_sheet_and_columns_runs_normally(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-005", requires={"descricao": ("codigo", "nivel")}))
        result = Engine(registry).run(_make_context())
        assert result.outcomes[0].status is RuleStatus.PASSED

    def test_a_rule_that_only_requires_sheet_presence_ignores_columns(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}))
        legend_frame = pd.DataFrame({"anything": ["1"]})
        result = Engine(registry).run(_make_context(sheets={"legenda": legend_frame}))
        assert result.outcomes[0].status is RuleStatus.PASSED

    def test_check_is_never_called_when_skipped(self) -> None:
        calls: list[str] = []

        def check(ctx: RuleContext) -> list[Issue]:
            calls.append("called")
            return []

        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}, check=check))
        Engine(registry).run(_make_context(sheets={}))
        assert calls == []


class TestEngineRequiresOptionsSkip:
    """`requires_options` unmet `ctx.options` keys produce a SKIPPED outcome (PROTO-013)."""

    def test_missing_option_is_skipped_with_disabled_by_option_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("TERR-001", requires_options=("territory_registry_present",)))
        result = Engine(registry).run(_make_context(options={}))
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.SKIPPED
        assert outcome.skip_reason == SkipReason.DISABLED_BY_OPTION

    def test_falsy_option_is_skipped_with_disabled_by_option_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("TERR-001", requires_options=("territory_registry_present",)))
        result = Engine(registry).run(_make_context(options={"territory_registry_present": False}))
        assert result.outcomes[0].status is RuleStatus.SKIPPED
        assert result.outcomes[0].skip_reason == SkipReason.DISABLED_BY_OPTION

    def test_truthy_option_runs_normally(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("TERR-001", requires_options=("territory_registry_present",)))
        result = Engine(registry).run(_make_context(options={"territory_registry_present": True}))
        assert result.outcomes[0].status is RuleStatus.PASSED

    def test_check_is_never_called_when_disabled_by_option(self) -> None:
        calls: list[str] = []

        def check(ctx: RuleContext) -> list[Issue]:
            calls.append("called")
            return []

        registry = RuleRegistry()
        registry.register(_make_spec("TERR-001", requires_options=("territory_registry_present",), check=check))
        Engine(registry).run(_make_context(options={}))
        assert calls == []

    def test_requires_is_checked_before_requires_options(self) -> None:
        """A rule missing both its sheet and a truthy option is reported for the sheet."""
        registry = RuleRegistry()
        registry.register(
            _make_spec(
                "TERR-001",
                requires={"valores": ()},
                requires_options=("territory_registry_present",),
            )
        )
        result = Engine(registry).run(_make_context(sheets={}, options={}))
        assert result.outcomes[0].skip_reason == SkipReason.MISSING_SHEET


class TestEngineDependsOnSkip:
    """`depends_on` blocks only on an upstream SKIPPED/FAILED outcome, never on issues."""

    def test_depends_on_a_skipped_rule_is_skipped_with_dependency_skipped_reason(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}))
        registry.register(_make_spec("LEG-013", depends_on=("LEG-012",)))
        result = Engine(registry).run(_make_context(sheets={}))
        outcomes = {outcome.rule_id: outcome for outcome in result.outcomes}
        assert outcomes["LEG-012"].status is RuleStatus.SKIPPED
        assert outcomes["LEG-013"].status is RuleStatus.SKIPPED
        assert outcomes["LEG-013"].skip_reason == SkipReason.DEPENDENCY_SKIPPED

    def test_depends_on_a_failed_rule_is_skipped_with_dependency_failed_reason(self) -> None:
        def crashing_check(ctx: RuleContext) -> list[Issue]:
            raise KeyError("boom")

        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", check=crashing_check))
        registry.register(_make_spec("LEG-013", depends_on=("LEG-012",)))
        result = Engine(registry).run(_make_context())
        outcomes = {outcome.rule_id: outcome for outcome in result.outcomes}
        assert outcomes["LEG-012"].status is RuleStatus.FAILED
        assert outcomes["LEG-013"].status is RuleStatus.SKIPPED
        assert outcomes["LEG-013"].skip_reason == SkipReason.DEPENDENCY_FAILED

    def test_depends_on_a_rule_with_issues_does_not_block(self) -> None:
        issue = _make_issue("LEG-012")
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", check=lambda ctx: [issue]))
        registry.register(_make_spec("LEG-013", depends_on=("LEG-012",)))
        result = Engine(registry).run(_make_context())
        outcomes = {outcome.rule_id: outcome for outcome in result.outcomes}
        assert outcomes["LEG-012"].status is RuleStatus.ISSUES
        assert outcomes["LEG-013"].status is RuleStatus.PASSED

    def test_depends_on_a_passed_rule_runs_normally(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012"))
        registry.register(_make_spec("LEG-013", depends_on=("LEG-012",)))
        result = Engine(registry).run(_make_context())
        outcomes = {outcome.rule_id: outcome for outcome in result.outcomes}
        assert outcomes["LEG-013"].status is RuleStatus.PASSED


class TestEngineCrashIsolation:
    """An exception inside `check()` becomes a FAILED outcome, never propagates."""

    def test_a_raised_exception_becomes_a_failed_outcome(self) -> None:
        def crashing_check(ctx: RuleContext) -> list[Issue]:
            raise TypeError("unexpected shape")

        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", check=crashing_check))
        result = Engine(registry).run(_make_context())
        outcome = result.outcomes[0]
        assert outcome.status is RuleStatus.FAILED
        assert outcome.issues == ()
        assert outcome.skip_reason == repr(TypeError("unexpected shape"))

    def test_engine_run_does_not_raise_when_a_rule_crashes(self) -> None:
        def crashing_check(ctx: RuleContext) -> list[Issue]:
            raise ValueError("boom")

        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", check=crashing_check))
        registry.register(_make_spec("DESC-002"))
        result = Engine(registry).run(_make_context())
        assert [outcome.status for outcome in result.outcomes] == [RuleStatus.FAILED, RuleStatus.PASSED]


class TestEngineOnlyFiltering:
    """`only=` restricts execution to a subset of rule IDs."""

    def test_only_none_runs_every_registered_rule(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-002"))
        result = Engine(registry).run(_make_context(), only=None)
        assert [outcome.rule_id for outcome in result.outcomes] == ["DESC-001", "DESC-002"]

    def test_only_a_subset_runs_just_that_subset(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-002"))
        result = Engine(registry).run(_make_context(), only={"DESC-002"})
        assert [outcome.rule_id for outcome in result.outcomes] == ["DESC-002"]

    def test_only_excludes_a_dependency_without_blocking_the_dependent(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-002", depends_on=("DESC-001",)))
        result = Engine(registry).run(_make_context(), only={"DESC-002"})
        assert [outcome.rule_id for outcome in result.outcomes] == ["DESC-002"]
        assert result.outcomes[0].status is RuleStatus.PASSED

    def test_only_an_empty_set_runs_nothing(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        result = Engine(registry).run(_make_context(), only=set())
        assert result.outcomes == ()


class TestEngineResultFlattening:
    """`EngineResult.validation_result` concatenates every outcome's issues, in order."""

    def test_flattens_issues_from_every_outcome_in_execution_order(self) -> None:
        first_issue = _make_issue("DESC-001")
        second_issue = _make_issue("DESC-002")
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", check=lambda ctx: [first_issue]))
        registry.register(_make_spec("DESC-002", check=lambda ctx: [second_issue]))
        result = Engine(registry).run(_make_context())
        assert result.validation_result.issues == (first_issue, second_issue)

    def test_skipped_and_failed_outcomes_contribute_no_issues(self) -> None:
        def crashing_check(ctx: RuleContext) -> list[Issue]:
            raise ValueError("boom")

        registry = RuleRegistry()
        registry.register(_make_spec("LEG-012", requires={"legenda": ()}))
        registry.register(_make_spec("DESC-001", check=crashing_check))
        result = Engine(registry).run(_make_context(sheets={"descricao": make_description_frame()}))
        assert result.validation_result.issues == ()

    def test_empty_engine_result_has_an_empty_validation_result(self) -> None:
        registry = RuleRegistry()
        result = Engine(registry).run(_make_context())
        assert result.validation_result.issues == ()
