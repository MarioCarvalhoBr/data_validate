#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `RuleSpec`/`RuleRegistry` (ARC-017, ARC-008, ADR-0006).

Table-driven coverage of rule-ID validation, duplicate registration, the decorator form, and
`topological_order`'s tie-breaking and cycle detection (`.claude/rules/testing.md`).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RegistryCycleError, RuleRegistry, RuleSpec
from data_validate.specs.issues import Issue, Severity


def _no_issues(ctx: RuleContext) -> list[Issue]:
    """A trivial `check` function used where the body itself is irrelevant to the test."""
    return []


def _make_spec(
    rule_id: str = "DESC-001",
    *,
    category: str = "html_codes_in_descriptions",
    severity_default: Severity = Severity.ERROR,
    requires: dict[str, tuple[str, ...]] | None = None,
    depends_on: tuple[str, ...] = (),
    check: Callable[[RuleContext], list[Issue]] = _no_issues,
) -> RuleSpec:
    """Build a `RuleSpec` with sensible defaults, overridable per test."""
    return RuleSpec(
        rule_id=rule_id,
        category=category,
        severity_default=severity_default,
        requires=requires if requires is not None else {},
        depends_on=depends_on,
        check=check,
    )


class TestRuleSpecValidation:
    """`RuleSpec.rule_id` must match the same stable rule-ID pattern as `Issue.rule_id`."""

    @pytest.mark.parametrize(
        "rule_id",
        [
            "STRUCT-001",
            "DESC-004",
            "COMP-009",
            "VAL-003",
            "TEMP-001",
            "SCEN-004",
            "LEG-015",
            "PROP-007",
            "SPELL-001",
            "CLEAN-002",
        ],
    )
    def test_accepts_every_known_prefix(self, rule_id: str) -> None:
        spec = _make_spec(rule_id)
        assert spec.rule_id == rule_id

    @pytest.mark.parametrize(
        "rule_id",
        ["desc-004", "DESC-4", "DESC_004", "DESC-0044", "UNKNOWN-001", "", "DESC-004 "],
    )
    def test_rejects_a_malformed_rule_id(self, rule_id: str) -> None:
        with pytest.raises(ValueError, match="does not match"):
            _make_spec(rule_id)

    def test_freezes_requires_into_a_read_only_mapping(self) -> None:
        spec = _make_spec(requires={"descricao": ("codigo", "nivel")})
        assert spec.requires == {"descricao": ("codigo", "nivel")}
        with pytest.raises(TypeError):
            spec.requires["descricao"] = ()  # type: ignore[index]


class TestRuleRegistryRegistration:
    """`register`/`get`/`__iter__`/`__len__` basics."""

    def test_register_then_get_returns_the_same_spec(self) -> None:
        registry = RuleRegistry()
        spec = _make_spec("DESC-001")
        registry.register(spec)
        assert registry.get("DESC-001") is spec

    def test_register_duplicate_id_raises_value_error(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(_make_spec("DESC-001"))

    def test_get_missing_rule_raises_key_error(self) -> None:
        registry = RuleRegistry()
        with pytest.raises(KeyError, match="no rule registered"):
            registry.get("DESC-999")

    def test_iter_yields_specs_in_registration_order(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-002"))
        registry.register(_make_spec("DESC-001"))
        assert [spec.rule_id for spec in registry] == ["DESC-002", "DESC-001"]

    def test_len_counts_registered_specs(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-002"))
        assert len(registry) == 2


class TestRuleRegistryDecorator:
    """`@registry.rule(...)` registers the wrapped function and returns it unchanged."""

    def test_decorator_registers_a_rule_spec(self) -> None:
        registry = RuleRegistry()

        @registry.rule(rule_id="DESC-002", category="sequential_codes")
        def check(ctx: RuleContext) -> list[Issue]:
            return []

        spec = registry.get("DESC-002")
        assert spec.category == "sequential_codes"
        assert spec.severity_default is Severity.ERROR
        assert spec.requires == {}
        assert spec.depends_on == ()
        assert spec.check is check

    def test_decorator_returns_the_original_function_unchanged(self) -> None:
        registry = RuleRegistry()

        @registry.rule(rule_id="DESC-002", category="sequential_codes")
        def check(ctx: RuleContext) -> list[Issue]:
            return []

        assert callable(check)

    def test_decorator_accepts_requires_depends_on_and_severity(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001"))

        @registry.rule(
            rule_id="DESC-002",
            category="sequential_codes",
            requires={"descricao": ("codigo",)},
            depends_on=("DESC-001",),
            severity_default=Severity.WARNING,
        )
        def check(ctx: RuleContext) -> list[Issue]:
            return []

        spec = registry.get("DESC-002")
        assert spec.requires == {"descricao": ("codigo",)}
        assert spec.depends_on == ("DESC-001",)
        assert spec.severity_default is Severity.WARNING


class TestRuleRegistryTopologicalOrder:
    """`topological_order` ordering, tie-breaking, and error cases."""

    def test_empty_registry_returns_empty_order(self) -> None:
        registry = RuleRegistry()
        assert registry.topological_order() == ()

    def test_no_dependencies_keeps_registration_order(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-002"))
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-003"))
        assert registry.topological_order() == ("DESC-002", "DESC-001", "DESC-003")

    def test_a_dependency_is_ordered_before_its_dependent(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-002", depends_on=("DESC-001",)))
        registry.register(_make_spec("DESC-001"))
        order = registry.topological_order()
        assert order.index("DESC-001") < order.index("DESC-002")

    def test_a_chain_of_dependencies_is_fully_ordered(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-003", depends_on=("DESC-002",)))
        registry.register(_make_spec("DESC-002", depends_on=("DESC-001",)))
        registry.register(_make_spec("DESC-001"))
        assert registry.topological_order() == ("DESC-001", "DESC-002", "DESC-003")

    def test_ties_keep_registration_order(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-003"))
        registry.register(_make_spec("DESC-001"))
        registry.register(_make_spec("DESC-002", depends_on=("DESC-001",)))
        # DESC-003 and DESC-001 are both ready first; DESC-003 was registered first.
        assert registry.topological_order() == ("DESC-003", "DESC-001", "DESC-002")

    def test_depends_on_unregistered_rule_raises_value_error(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-002", depends_on=("DESC-999",)))
        with pytest.raises(ValueError, match="unregistered rule"):
            registry.topological_order()

    def test_a_two_rule_cycle_raises_registry_cycle_error(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", depends_on=("DESC-002",)))
        registry.register(_make_spec("DESC-002", depends_on=("DESC-001",)))
        with pytest.raises(RegistryCycleError) as excinfo:
            registry.topological_order()
        assert set(excinfo.value.unresolved) == {"DESC-001", "DESC-002"}

    def test_a_self_dependency_raises_registry_cycle_error(self) -> None:
        registry = RuleRegistry()
        registry.register(_make_spec("DESC-001", depends_on=("DESC-001",)))
        with pytest.raises(RegistryCycleError):
            registry.topological_order()
