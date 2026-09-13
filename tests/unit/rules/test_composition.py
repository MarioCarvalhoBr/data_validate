#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.composition` (Phase 3 Port 3, COMP-001…009).

Table-driven coverage per rule (happy path, each failure mode, missing-column abort, and the
engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no mocks (`.claude/rules/testing.md`). `_make_context` mirrors
`SpreadsheetProcessor._build_rule_context`'s two-pass build: it computes `CompositionFacts` once
via `compute_composition_facts` and injects it into `ctx.options["composition_facts"]`, so every
rule under test reads facts the same way the real pipeline does.

Rewrites the untested legacy `compostion_graph_validator.py::SpCompositionGraphValidator` and
`composition_tree_validator.py::SpCompositionTreeValidator` (both deleted, see
`.specs/business-rules/composition.md` and ARC-017 Phase 3 Port 3/BUG-024): every scenario either
legacy class could reach through its `run()` validations list is reproduced here against the
corresponding pure rule function.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.rules.composition import (
    COMPOSITION_REGISTRY,
    check_children_share_parent_level,
    check_composition_graph_acyclic,
    check_composition_no_disconnected_groups,
    check_composition_tree_acyclic,
    check_leaf_indicators_have_proportionality,
    check_leaf_indicators_have_values,
    check_parent_level_below_child_level,
    check_relation_indicators_in_composition,
    check_unique_titles_per_subtree,
    compute_composition_facts,
)
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.specs.issues import Severity
from tests.factories import (
    make_composition_frame,
    make_description_frame,
    make_proportionality_frame,
    make_values_frame,
)

_COMPOSICAO = "composicao.xlsx"
_DESCRICAO = "descricao.xlsx"
_VALORES = "valores.xlsx"
_PROPORCIONALIDADES = "proporcionalidades.xlsx"


def _cleaned_ints(frame: pd.DataFrame, column: str, *, min_value: int = 1) -> pd.Series:
    """A minimal stand-in for the model's own `min_value`-gated integer cleaning."""
    numeric = pd.to_numeric(frame[column], errors="coerce")
    valid = numeric.notna() & (numeric >= min_value) & (numeric % 1 == 0)
    return numeric[valid].astype("int64")


def _make_context(
    *,
    composicao: pd.DataFrame | None = None,
    descricao: pd.DataFrame | None = None,
    valores: pd.DataFrame | None = None,
    proporcionalidades: pd.DataFrame | None = None,
    proportionality_read_successful: bool = True,
    composition_root: str = "1",
    composicao_cleaned: dict[str, pd.Series] | None = None,
    descricao_cleaned: dict[str, pd.Series] | None = None,
) -> RuleContext:
    """Build a `RuleContext` over a composition-relevant bundle, facts pre-computed (BUG-019).

    Mirrors `SpreadsheetProcessor._build_rule_context`: a preliminary context (no
    `composition_facts` yet) is used to call `compute_composition_facts` once, then the facts
    are injected into the final, returned context — exactly like the real pipeline, so every
    rule under test reads facts the same way it does in production.
    """
    sheets: dict[str, pd.DataFrame] = {}
    cleaned: dict[str, dict[str, pd.Series]] = {}
    filenames: dict[str, str] = {}

    if composicao is not None:
        sheets["composicao"] = composicao
        filenames["composicao"] = _COMPOSICAO
        resolved = dict(composicao_cleaned) if composicao_cleaned is not None else {}
        if composicao_cleaned is None:
            if "codigo_pai" in composicao.columns:
                resolved["codigo_pai"] = _cleaned_ints(composicao, "codigo_pai")
            if "codigo_filho" in composicao.columns:
                resolved["codigo_filho"] = _cleaned_ints(composicao, "codigo_filho")
        cleaned["composicao"] = resolved

    if descricao is not None:
        sheets["descricao"] = descricao
        filenames["descricao"] = _DESCRICAO
        resolved = dict(descricao_cleaned) if descricao_cleaned is not None else {}
        if descricao_cleaned is None and "codigo" in descricao.columns:
            resolved["codigo"] = _cleaned_ints(descricao, "codigo")
        cleaned["descricao"] = resolved

    if valores is not None:
        sheets["valores"] = valores
        filenames["valores"] = _VALORES

    if proporcionalidades is not None:
        sheets["proporcionalidades"] = proporcionalidades
        filenames["proporcionalidades"] = _PROPORCIONALIDADES

    base_options = {
        "filenames": filenames,
        "proportionality_read_successful": proportionality_read_successful,
        "composition_root": composition_root,
    }

    def _build(options: dict[str, object]) -> RuleContext:
        return RuleContext(
            sheets=sheets,
            cleaned=cleaned,
            options=options,
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

    facts = compute_composition_facts(_build(base_options))
    return _build({**base_options, "composition_facts": facts})


class TestCompositionRegistryShape:
    """The registry declares exactly the COMP ids from both legacy validators, in order."""

    def test_registry_contains_every_ported_comp_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in COMPOSITION_REGISTRY] == [
            "COMP-001",
            "COMP-002",
            "COMP-003",
            "COMP-004",
            "COMP-005",
            "COMP-006",
            "COMP-007",
            "COMP-008",
            "COMP-009",
        ]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in COMPOSITION_REGISTRY}
        assert categories == {
            "COMP-001": NamesEnum.IR.value,
            "COMP-002": NamesEnum.IR.value,
            "COMP-003": NamesEnum.IR.value,
            "COMP-004": NamesEnum.UT.value,
            "COMP-005": NamesEnum.LEAF_NO_DATA.value,
            "COMP-006": NamesEnum.LEAF_NO_DATA.value,
            "COMP-007": NamesEnum.TH.value,
            "COMP-008": NamesEnum.TH.value,
            "COMP-009": NamesEnum.CHILD_LVL.value,
        }

    def test_empty_composicao_skips_every_rule_silently(self) -> None:
        ctx = _make_context(composicao=pd.DataFrame(), descricao=make_description_frame(3))
        result = Engine(COMPOSITION_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()

    def test_composicao_present_but_descricao_empty_skips_descricao_dependent_rules(self) -> None:
        # `valores` is populated too, so COMP-005/COMP-006 are NOT skipped here — isolating
        # exactly the rules that depend on `descricao` being non-empty.
        ctx = _make_context(
            composicao=make_composition_frame(),
            descricao=pd.DataFrame(),
            valores=make_values_frame(codes=(2, 3)),
        )
        result = Engine(COMPOSITION_REGISTRY).run(ctx)
        skipped = {outcome.rule_id for outcome in result.outcomes if outcome.status is RuleStatus.SKIPPED}
        assert skipped == {"COMP-001", "COMP-004", "COMP-007", "COMP-008", "COMP-009"}


class TestComputeCompositionFacts:
    """`compute_composition_facts`: the shared graph/tree/relation facts (BUG-019)."""

    def test_valid_tree_has_no_cycle_and_a_single_component(self) -> None:
        ctx = _make_context(
            composicao=make_composition_frame(edges=[(1, 2), (1, 3)]), descricao=make_description_frame(3)
        )
        facts = compute_composition_facts(ctx)

        assert facts.available is True
        assert facts.has_cycle is False
        assert facts.disconnected_components == ()
        assert facts.root_present is True
        assert set(facts.leafs) == {"2", "3"}

    def test_missing_composicao_columns_marks_facts_unavailable(self) -> None:
        ctx = _make_context(composicao=pd.DataFrame({"other": ["x"]}), descricao=make_description_frame(3))
        facts = compute_composition_facts(ctx)

        assert facts.available is False
        assert facts.graph.number_of_nodes() == 0
        assert facts.has_cycle is False

    def test_default_root_is_1_and_composition_root_option_overrides_it(self) -> None:
        ctx = _make_context(composicao=make_composition_frame(edges=[(1, 2)]), descricao=make_description_frame(2))
        assert compute_composition_facts(ctx).root == "1"

        ctx_custom_root = _make_context(
            composicao=make_composition_frame(edges=[(9, 2)]),
            descricao=make_description_frame(2),
            composition_root="9",
        )
        facts = compute_composition_facts(ctx_custom_root)
        assert facts.root == "9"
        assert facts.root_present is True


class TestCheckRelationIndicatorsInComposition:
    """COMP-001: `descricao.codigo` and `composicao`'s codes must match."""

    def test_matching_codes_report_nothing(self) -> None:
        ctx = _make_context(
            composicao=make_composition_frame(edges=[(1, 2), (1, 3)]), descricao=make_description_frame(3)
        )
        assert check_relation_indicators_in_composition(ctx) == []

    def test_codes_mismatch_both_directions_are_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 4)])
        descricao = make_description_frame(3)  # codes 1, 2, 3 — 4 is composicao-only, 3 is descricao-only
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_relation_indicators_in_composition(ctx)

        assert len(issues) == 2
        assert {issue.message_key for issue in issues} == {"rule.COMP-001.missing_codes"}
        by_label = {issue.params["label_from"]: issue.params for issue in issues}
        assert by_label[_DESCRICAO]["missing_codes"] == "[3]"
        assert by_label[_DESCRICAO]["label_to"] == _COMPOSICAO
        assert by_label[_COMPOSICAO]["missing_codes"] == "[4]"
        assert by_label[_COMPOSICAO]["label_to"] == _DESCRICAO
        assert all(issue.severity is Severity.ERROR and issue.category == NamesEnum.IR.value for issue in issues)

    def test_missing_columns_are_reported_in_order(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_filho"])
        descricao = make_description_frame(2).drop(columns=["codigo"])
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_relation_indicators_in_composition(ctx)

        assert [issue.params["column"] for issue in issues] == ["codigo_filho", "codigo"]
        assert all(issue.message_key == "rule.composition.missing_required_column" for issue in issues)


class TestCheckCompositionGraphAcyclic:
    """COMP-002: the composition graph must be acyclic."""

    def test_an_acyclic_graph_reports_nothing(self) -> None:
        ctx = _make_context(composicao=make_composition_frame(edges=[(1, 2), (1, 3)]))
        assert check_composition_graph_acyclic(ctx) == []

    def test_a_cycle_is_reported(self) -> None:
        ctx = _make_context(composicao=make_composition_frame(edges=[(1, 2), (2, 1)]))

        issues = check_composition_graph_acyclic(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-002"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.COMP-002.error"
        assert issue.params["filename"] == _COMPOSICAO
        assert issue.params["cycle"] in ("1 -> 2, 2 -> 1", "2 -> 1, 1 -> 2")

    def test_missing_column_is_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_pai"])
        ctx = _make_context(composicao=composicao)

        issues = check_composition_graph_acyclic(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.composition.missing_required_column"
        assert issues[0].params["column"] == "codigo_pai"


class TestCheckCompositionNoDisconnectedGroups:
    """COMP-003: the composition graph must be a single weakly connected component."""

    def test_a_single_component_reports_nothing(self) -> None:
        ctx = _make_context(composicao=make_composition_frame(edges=[(1, 2), (1, 3)]))
        assert check_composition_no_disconnected_groups(ctx) == []

    def test_a_disconnected_group_is_reported(self) -> None:
        ctx = _make_context(composicao=make_composition_frame(edges=[(1, 2), (1, 3), (10, 11)]))

        issues = check_composition_no_disconnected_groups(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-003"
        assert issue.message_key == "rule.COMP-003.error"
        assert issue.params["disconnected"] == "[10 -> 11]"

    def test_missing_column_reports_nothing_comp_002_already_did(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_pai"])
        ctx = _make_context(composicao=composicao)

        assert check_composition_no_disconnected_groups(ctx) == []


class TestCheckUniqueTitlesPerSubtree:
    """COMP-004: `nome_simples`/`nome_completo` must be unique inside each root-child's subtree."""

    def test_a_tree_with_unique_titles_reports_nothing(self) -> None:
        ctx = _make_context(
            composicao=make_composition_frame(edges=[(1, 2), (1, 3)]), descricao=make_description_frame(3)
        )
        assert check_unique_titles_per_subtree(ctx) == []

    def test_duplicate_titles_within_one_subtree_are_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 5), (2, 3), (2, 4), (5, 6), (5, 7)])
        descricao = make_description_frame(
            7,
            levels=[1, 2, 2, 3, 3, 2, 2],
            nome_simples=["Raiz", "A", "Same", "Same", "B", "Same", "C"],
        )
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_unique_titles_per_subtree(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-004"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.UT.value
        assert issue.message_key == "rule.COMP-004.warning.simple_name"
        assert issue.params["duplicated_values"] == "['Same']"

    def test_the_same_title_in_two_different_subtrees_is_allowed(self) -> None:
        # "Same" appears once under 2's subtree (code 3) and once under 5's subtree (code 6):
        # no duplicate is reported because each subtree is checked independently.
        composicao = make_composition_frame(edges=[(1, 2), (1, 5), (2, 3), (5, 6)])
        descricao = make_description_frame(
            5,
            levels=[1, 2, 3, 2, 3],
            nome_simples=["Raiz", "A", "Same", "B", "Same"],
        )
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_unique_titles_per_subtree(ctx) == []

    def test_missing_root_is_reported_as_an_error(self) -> None:
        # Codes 2/3/4 match on both sides (COMP-001 passes) and the graph is a single acyclic
        # component — but indicator "1" (the default root) simply does not exist.
        composicao = make_composition_frame(edges=[(2, 3), (2, 4)])
        descricao = pd.DataFrame(
            {
                "codigo": ["2", "3", "4"],
                "nivel": ["1", "2", "2"],
                "nome_simples": ["A", "B", "C"],
                "nome_completo": ["AA", "BB", "CC"],
            }
        )
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_unique_titles_per_subtree(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.COMP-004.root_missing.error"
        assert issues[0].params == {"filename": _COMPOSICAO, "root": "1"}

    def test_a_cycle_produces_no_issue_at_all(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 1)])
        descricao = make_description_frame(2)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_unique_titles_per_subtree(ctx) == []

    def test_a_relation_mismatch_produces_no_issue_at_all(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 4)])
        descricao = make_description_frame(3)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_unique_titles_per_subtree(ctx) == []

    def test_missing_columns_are_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_pai"])
        descricao = make_description_frame(2).drop(columns=["nome_completo"])
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_unique_titles_per_subtree(ctx)

        assert [issue.params["column"] for issue in issues] == ["codigo_pai", "nome_completo"]
        assert all(issue.severity is Severity.WARNING for issue in issues)


class TestCheckLeafIndicatorsHaveValues:
    """COMP-005: every leaf indicator must have a `valores` column."""

    def test_every_leaf_has_a_value_column_reports_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 3)])
        valores = make_values_frame(codes=(2, 3))
        ctx = _make_context(composicao=composicao, valores=valores)

        assert check_leaf_indicators_have_values(ctx) == []

    def test_a_leaf_without_a_value_column_is_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 3)])
        valores = make_values_frame(codes=(2,))
        ctx = _make_context(composicao=composicao, valores=valores)

        issues = check_leaf_indicators_have_values(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-005"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.LEAF_NO_DATA.value
        assert issue.message_key == "rule.composition.leaf_without_data"
        assert issue.params == {"filename": _VALORES, "leaf": "3"}

    def test_missing_columns_are_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_filho"])
        valores = make_values_frame(codes=(2,)).drop(columns=["id"])
        ctx = _make_context(composicao=composicao, valores=valores)

        issues = check_leaf_indicators_have_values(ctx)

        assert {issue.params["column"] for issue in issues} == {"codigo_filho", "id"}


class TestCheckLeafIndicatorsHaveProportionality:
    """COMP-006: every leaf indicator must appear in `proporcionalidades` (when delivered)."""

    def test_every_leaf_present_reports_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 3), (2, 4)])
        valores = make_values_frame(codes=(3, 4))
        proporcionalidades = make_proportionality_frame(parent_children={"2-2020": ["3-2020", "4-2020"]})
        ctx = _make_context(composicao=composicao, valores=valores, proporcionalidades=proporcionalidades)

        assert check_leaf_indicators_have_proportionality(ctx) == []

    def test_a_leaf_missing_from_proportionality_is_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 3), (2, 4)])
        valores = make_values_frame(codes=(3, 4))
        proporcionalidades = make_proportionality_frame(parent_children={"2-2020": ["3-2020"]})
        ctx = _make_context(composicao=composicao, valores=valores, proporcionalidades=proporcionalidades)

        issues = check_leaf_indicators_have_proportionality(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.composition.leaf_without_data"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "leaf": "4"}

    def test_proportionality_unavailable_skips_this_rule_only(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 3), (2, 4)])
        valores = make_values_frame(codes=(3,))  # leaf 4 missing too, but COMP-006 must stay silent
        ctx = _make_context(
            composicao=composicao,
            valores=valores,
            proporcionalidades=None,
            proportionality_read_successful=False,
        )

        assert check_leaf_indicators_have_proportionality(ctx) == []
        # COMP-005 still reports the valores-side gap independently.
        assert len(check_leaf_indicators_have_values(ctx)) == 1

    def test_empty_valores_skips_comp_006_even_when_proportionality_has_data(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 3)])
        proporcionalidades = make_proportionality_frame(parent_children={"2-2020": ["3-2020"]})
        ctx = _make_context(composicao=composicao, valores=pd.DataFrame(), proporcionalidades=proporcionalidades)

        assert check_leaf_indicators_have_proportionality(ctx) == []


class TestCheckCompositionTreeAcyclic:
    """COMP-007: the composition tree (adjacency-dict view) must be acyclic."""

    def test_an_acyclic_tree_reports_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 3)])
        descricao = make_description_frame(3)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_composition_tree_acyclic(ctx) == []

    def test_a_cycle_is_reported_as_a_node_path(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 1)])
        descricao = make_description_frame(2)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_composition_tree_acyclic(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-007"
        assert issue.message_key == "rule.COMP-007.error"
        assert issue.params["cycle_path"] in ("1 -> 2 -> 1", "2 -> 1 -> 2")

    def test_missing_relacao_column_is_no_longer_required_proto_002(self) -> None:
        """PROTO-002: `relacao` was removed from the protocol; it must not be required here."""
        composicao = make_composition_frame(edges=[(1, 2)])
        descricao = make_description_frame(2).drop(columns=["relacao"])
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_composition_tree_acyclic(ctx)

        assert not any(issue.params.get("column") == "relacao" for issue in issues)
        assert issues == []


class TestCheckParentLevelBelowChildLevel:
    """COMP-008: a parent's `nivel` must be lower than every one of its children's."""

    def test_a_valid_hierarchy_reports_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 3)])
        descricao = make_description_frame(3)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_parent_level_below_child_level(ctx) == []

    def test_a_parent_at_the_same_or_higher_level_is_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)])
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["2", "1"], "relacao": ["1", "1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_parent_level_below_child_level(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-008"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.COMP-008.error"
        assert issue.params == {
            "filename": _COMPOSICAO,
            "row": 2,
            "parent": 1,
            "parent_level": 2,
            "child": 2,
            "child_level": 1,
        }

    def test_a_code_missing_from_descricao_is_silently_ignored(self) -> None:
        composicao = make_composition_frame(edges=[(1, 99)])
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "relacao": ["1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_parent_level_below_child_level(ctx) == []


class TestCheckChildrenSharedParentLevel:
    """COMP-009: every child of the same parent must share one `nivel`; codes must resolve."""

    def test_siblings_at_the_same_level_report_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (1, 3)])
        descricao = make_description_frame(3)
        ctx = _make_context(composicao=composicao, descricao=descricao)

        assert check_children_share_parent_level(ctx) == []

    def test_siblings_at_different_levels_are_reported(self) -> None:
        composicao = pd.DataFrame({"codigo_pai": ["1", "1"], "codigo_filho": ["2", "3"]})
        descricao = pd.DataFrame({"codigo": ["1", "2", "3"], "nivel": ["1", "2", "3"], "relacao": ["1", "1", "1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_children_share_parent_level(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "COMP-009"
        assert issue.message_key == "rule.COMP-009.level_mismatch"
        assert issue.params["parent"] == "1"
        assert "indicador 2 possui nível '2'" in issue.params["children"]
        assert "indicador 3 possui nível '3'" in issue.params["children"]

    def test_an_unresolved_parent_code_is_reported(self) -> None:
        composicao = pd.DataFrame({"codigo_pai": ["9"], "codigo_filho": ["2"]})
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["1"], "relacao": ["1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_children_share_parent_level(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.COMP-009.parent_missing"
        assert issues[0].params == {"filename": _COMPOSICAO, "parent": "9"}

    def test_an_unresolved_child_code_is_reported(self) -> None:
        composicao = pd.DataFrame({"codigo_pai": ["1"], "codigo_filho": ["99"]})
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "relacao": ["1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_children_share_parent_level(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.COMP-009.child_missing"
        assert issues[0].params == {"filename": _COMPOSICAO, "child": "99"}

    def test_raw_string_mismatch_is_a_preserved_defect_bug_014(self) -> None:
        # "1" (raw composicao) vs "1.0" (raw descricao): not equal as raw strings, so the
        # parent is reported as unresolved — matching the legacy validator exactly.
        composicao = pd.DataFrame({"codigo_pai": ["1"], "codigo_filho": ["2"]})
        descricao = pd.DataFrame({"codigo": ["1.0", "2"], "nivel": ["1", "2"], "relacao": ["1", "1"]})
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_children_share_parent_level(ctx)

        assert issues[0].message_key == "rule.COMP-009.parent_missing"

    def test_missing_columns_are_reported(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=["codigo_pai"])
        descricao = make_description_frame(2).drop(columns=["nivel"])
        ctx = _make_context(composicao=composicao, descricao=descricao)

        issues = check_children_share_parent_level(ctx)

        assert {issue.params["column"] for issue in issues} == {"codigo_pai", "nivel"}
