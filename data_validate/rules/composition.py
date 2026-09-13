#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""COMP-001…009: the `composicao` (indicator hierarchy) rules (ARC-017 Phase 3 Port 3, ADR-0006).

Ports BOTH legacy composition validators onto the `rules` engine, one `RuleSpec` per `COMP-*` id
documented in `.specs/business-rules/composition.md`:

- `validators/spreadsheets/composition/compostion_graph_validator.py::SpCompositionGraphValidator`
  (networkx `DiGraph`) → COMP-001 (indicator relations), COMP-002 (cycle), COMP-003 (disconnected
  components), COMP-004 (unique titles per subtree), COMP-005/COMP-006 (leaf indicators without
  associated `valores`/`proporcionalidades` data).
- `validators/spreadsheets/composition/composition_tree_validator.py::SpCompositionTreeValidator`
  (adjacency dict) → COMP-007 (tree cycle, a deliberate duplicate of COMP-002 under a different
  message shape — see the spec's "Gaps" section), COMP-008 (parent/child level hierarchy),
  COMP-009 (siblings share one level; codes resolve in `descricao`).

Both legacy filenames (including the `compostion_` typo) are retired by this port — BUG-024.

BUG-019 ("compute once"): both legacy validators independently built the same `networkx.DiGraph`
from the same cleaned `composicao` edges, and `SpCompositionGraphValidator.
validate_unique_titles_with_graph` (COMP-004) re-ran cycle detection, disconnected-component
detection, and the `descricao`<->`composicao` code comparison a second time on top of that.
`compute_composition_facts` computes every one of those values exactly once per run;
`SpreadsheetProcessor` calls it once and injects the result via
`ctx.options["composition_facts"]` (see `_build_rule_context`), and every rule below reads
`ctx.options["composition_facts"]` — never `data_validate.rules.composition.
compute_composition_facts` itself directly, and never re-runs another `COMP-*` rule's check
function. A rule-level test that builds its own `RuleContext` without pre-computing facts still
gets correct behaviour (see `_facts`'s fallback), just without the cross-rule sharing a full
pipeline run gets.

Root node (G-12): the legacy graph validator hard-coded node `"1"` as the composition root.
`ctx.options.get("composition_root", "1")` replaces the hardcoded literal, defaulting to the
same value — see `.specs/business-rules/composition.md`'s COMP-004 entry.

PERF-001: `GraphProcessing.create_graph_structure` and `TreeProcessing.create_tree_structure` were
rewritten to vectorised `nx.from_pandas_edgelist`/`groupby` (no more `iterrows()`); COMP-008's
parent/child level-hierarchy check is vectorised here via `.map()` over the cleaned edges,
replacing the deleted `TreeProcessing.validate_level_hierarchy`'s `iterrows()` loop. COMP-009's
raw-string sibling-level check is vectorised via `groupby`/`isin`/`.map()`, replacing
`SpCompositionTreeValidator.validate_tree_levels_children`'s two nested `iterrows()` loops (see
`.claude/skills/pandas-vectorization/SKILL.md` patterns 3/4).

Depends only on `data_validate.rules`/`data_validate.specs`, `pandas`, `networkx`, and the pure
`GraphProcessing`/`TreeProcessing`/`DataCleaningProcessing` helpers (no message-text-building
helper, no `models` import), per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import networkx as nx
import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.graph_processing import GraphProcessing
from data_validate.helpers.common.validation.tree_processing import TreeProcessing
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

COMPOSITION_REGISTRY = RuleRegistry()
"""Every `COMP-*` rule ported from both legacy composition validators, in their legacy order."""

_COMPOSITION_SHEET = "composicao"
_DESCRIPTION_SHEET = "descricao"
_VALUES_SHEET = "valores"
_PROPORTIONALITY_SHEET = "proporcionalidades"

_PARENT = "codigo_pai"
_CHILD = "codigo_filho"
_CODE = "codigo"
_LEVEL = "nivel"
_RELATION = "relacao"
_SIMPLE_NAME = "nome_simples"
_COMPLETE_NAME = "nome_completo"
_ID = "id"

_DEFAULT_ROOT = "1"

_MISSING_COLUMN_KEY = "rule.composition.missing_required_column"
_MISSING_COLUMN_LEVEL2_KEY = "rule.composition.missing_required_column_level2"
_LEAF_WITHOUT_DATA_KEY = "rule.composition.leaf_without_data"


@dataclass(frozen=True)
class CompositionFacts:
    """Composition graph/tree/relation facts computed once per run (BUG-019).

    Attributes:
        available: Whether the `composicao` graph could be built at all (`codigo_pai`/
            `codigo_filho` both present). Every graph-derived field below is an empty/no-op
            default when this is `False`.
        edges: The cleaned `composicao` edges (`codigo_pai` >= 0, `codigo_filho` >= 1, matching
            both legacy validators' local re-clean), indexed by the original `composicao` row
            position.
        graph: The directed graph built from `edges` (string node ids).
        has_cycle: Whether `graph` contains a cycle (COMP-002).
        cycle: The first cycle found, as `(source, target)` edge pairs, or `()`.
        disconnected_components: Every weakly-connected component of `graph` except the
            largest, sorted by size descending (COMP-003).
        root: The root node id (`ctx.options["composition_root"]`, defaulting to `"1"`).
        root_present: Whether `root` is a node of `graph`.
        leafs: Every node of `graph` with no outgoing edge (COMP-005/COMP-006).
        tree_has_cycle: Whether the adjacency-dict view of `edges` contains a cycle, detected
            by DFS (COMP-007 — a deliberate duplicate of `has_cycle` under a different message
            shape, see `.specs/business-rules/composition.md`'s COMP-007 entry).
        tree_cycle_path: The node path of `tree_has_cycle`'s cycle (e.g. `("1", "2", "1")`).
        description_levels: `codigo -> nivel` (both `int`), from `descricao` cleaned locally
            (min 1) with a synthetic `0 -> 0` entry (COMP-008's virtual root, matching the
            legacy validator always inserting one because the min-1 clean can never keep a
            `codigo == 0` row).
        description_levels_available: Whether `description_levels` could be computed
            (`descricao` has both `codigo` and `nivel`).
        relation_checked: Whether `relation_missing_in_*` were computed (`descricao` is
            non-empty and `descricao.codigo`/`composicao`'s columns are all present).
        relation_missing_in_composition: `descricao.codigo` values absent from the union of
            `composicao`'s `codigo_pai` and `codigo_filho` (COMP-001).
        relation_missing_in_description: values from the union of `composicao`'s `codigo_pai`
            and `codigo_filho` absent from `descricao.codigo` (COMP-001).
    """

    available: bool
    edges: pd.DataFrame
    graph: nx.DiGraph
    has_cycle: bool
    cycle: tuple[tuple[str, str], ...]
    disconnected_components: tuple[nx.DiGraph, ...]
    root: str
    root_present: bool
    leafs: tuple[str, ...]
    tree_has_cycle: bool
    tree_cycle_path: tuple[str, ...]
    description_levels: Mapping[int, int]
    description_levels_available: bool
    relation_checked: bool
    relation_missing_in_composition: tuple[int, ...]
    relation_missing_in_description: tuple[int, ...]


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"composicao.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _missing_composition_columns(frame: pd.DataFrame) -> list[str]:
    """Return every one of `codigo_pai`/`codigo_filho` missing from `frame`, in that order."""
    return [column for column in (_PARENT, _CHILD) if column not in frame.columns]


def _missing_column_issue(
    rule_id: str, severity: Severity, category: str, filename: str, column: str, *, level2: bool = False
) -> Issue:
    """Build the shared "required column is missing" abort `Issue`.

    Args:
        rule_id: The rule reporting the missing column.
        severity: The severity the legacy validator used for this rule's abort case.
        category: The legacy `NamesEnum` report bucket this rule belongs to.
        filename: The sheet's file name, as delivered.
        column: The missing column's name.
        level2: Whether `column` is a `proporcionalidades` level-2 column (renders
            `rule.composition.missing_required_column_level2`, matching
            `DataFrameProcessing.column_exists`'s `MultiIndex` branch text).
    """
    return Issue(
        rule_id=rule_id,
        severity=severity,
        sheet=filename,
        row=None,
        column=column,
        message_key=_MISSING_COLUMN_LEVEL2_KEY if level2 else _MISSING_COLUMN_KEY,
        params={"filename": filename, "column": column},
        category=category,
    )


def _cleaned_ids(ctx: RuleContext, sheet: str, column: str) -> set[int]:
    """Return `ctx.cleaned[sheet][column]` as a `set[int]`, or an empty set when absent."""
    series = ctx.cleaned.get(sheet, {}).get(column)
    if series is None:
        return set()
    return {int(value) for value in series.dropna().tolist()}


def _compute_relation_facts(ctx: RuleContext, graph_available: bool) -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    """COMP-001's code comparison, computed once for both COMP-001 and COMP-004 (BUG-019)."""
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    if description_frame.empty or _CODE not in description_frame.columns or not graph_available:
        return False, (), ()

    description_codes = _cleaned_ids(ctx, _DESCRIPTION_SHEET, _CODE)
    composition_codes = _cleaned_ids(ctx, _COMPOSITION_SHEET, _PARENT) | _cleaned_ids(ctx, _COMPOSITION_SHEET, _CHILD)

    missing_in_composition = tuple(sorted(description_codes - composition_codes))
    missing_in_description = tuple(sorted(composition_codes - description_codes))
    return True, missing_in_composition, missing_in_description


def _compute_description_levels(ctx: RuleContext) -> tuple[dict[int, int], bool]:
    """`codigo -> nivel` from `descricao`, cleaned locally (min 1) with a synthetic root."""
    frame = ctx.sheet(_DESCRIPTION_SHEET)
    filename = _filename(ctx, _DESCRIPTION_SHEET)
    if _CODE not in frame.columns or _LEVEL not in frame.columns:
        return {}, False

    cleaned, _errors = DataCleaningProcessing.clean_dataframe_integers(frame, filename, [_CODE, _LEVEL], min_value=1)
    levels: dict[int, int] = dict(zip(cleaned[_CODE], cleaned[_LEVEL]))
    levels.setdefault(0, 0)
    return levels, True


def compute_composition_facts(ctx: RuleContext) -> CompositionFacts:
    """Compute every `COMP-*` rule's shared graph/tree/relation facts, once (BUG-019).

    Args:
        ctx: The context every rule in `COMPOSITION_REGISTRY` will read from; only
            `ctx.sheet`/`ctx.cleaned`/`ctx.options["composition_root"]` are read here — this
            function never mutates `ctx` and never emits an `Issue` itself (a missing required
            column is reported by whichever rule needs it, see each rule's docstring).

    Returns:
        CompositionFacts: See its attributes; `available=False` when `composicao` lacks
            `codigo_pai`/`codigo_filho` (every graph-derived field then holds an empty/no-op
            default) — `relation_*`/`description_levels*` are computed independently and may
            still be populated in that case.
    """
    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    available = not _missing_composition_columns(composition_frame)

    if available:
        edges, _errors = DataCleaningProcessing.clean_dataframe_integers(
            composition_frame, composition_filename, [_PARENT], min_value=0
        )
        edges, _errors = DataCleaningProcessing.clean_dataframe_integers(
            edges, composition_filename, [_CHILD], min_value=1
        )
    else:
        edges = pd.DataFrame(columns=[_PARENT, _CHILD])

    graph_processing = GraphProcessing()
    graph = graph_processing.create_graph_structure(edges, _PARENT, _CHILD) if not edges.empty else nx.DiGraph()

    has_cycle, cycle = graph_processing.detect_cycles(graph)
    disconnected_components = tuple(graph_processing.detect_disconnected_components(graph))
    leafs = tuple(graph_processing.get_leaf_nodes(graph))

    root = str(ctx.options.get("composition_root", _DEFAULT_ROOT))
    root_present = graph.has_node(root)

    tree_adjacency = TreeProcessing.create_tree_structure(edges, _PARENT, _CHILD) if not edges.empty else {}
    tree_has_cycle, tree_cycle_path = TreeProcessing.detect_tree_cycles(tree_adjacency)

    description_levels, description_levels_available = _compute_description_levels(ctx)
    relation_checked, missing_in_composition, missing_in_description = _compute_relation_facts(ctx, available)

    return CompositionFacts(
        available=available,
        edges=edges,
        graph=graph,
        has_cycle=has_cycle,
        cycle=tuple(cycle) if cycle else (),
        disconnected_components=disconnected_components,
        root=root,
        root_present=root_present,
        leafs=leafs,
        tree_has_cycle=tree_has_cycle,
        tree_cycle_path=tuple(tree_cycle_path),
        description_levels=description_levels,
        description_levels_available=description_levels_available,
        relation_checked=relation_checked,
        relation_missing_in_composition=missing_in_composition,
        relation_missing_in_description=missing_in_description,
    )


def _facts(ctx: RuleContext) -> CompositionFacts:
    """Read `ctx.options["composition_facts"]`, computing it on the fly if a caller forgot to.

    The real pipeline (`SpreadsheetProcessor._build_rule_context`) always injects a pre-computed
    `CompositionFacts` so every rule reads it, never recomputes it (BUG-019); this fallback only
    matters for a rule-level test/caller that builds a bare `RuleContext` directly — it keeps
    that call correct (never `None`/a crash), just without the cross-rule sharing a full run
    gets.
    """
    facts = ctx.options.get("composition_facts")
    if isinstance(facts, CompositionFacts):
        return facts
    return compute_composition_facts(ctx)


def _format_cycle_edges(cycle: tuple[tuple[str, str], ...]) -> str:
    """Render a cycle's edges as `"a -> b, b -> c"`, matching the legacy COMP-002 text."""
    return ", ".join(f"{source} -> {target}" for source, target in cycle)


def _relation_issue(rule_id: str, label_from: str, label_to: str, missing_codes: tuple[int, ...]) -> Issue:
    """Build one COMP-001 "codes missing" `Issue` (one direction of the comparison)."""
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=label_from,
        row=None,
        column=None,
        message_key="rule.COMP-001.missing_codes",
        params={"label_from": label_from, "label_to": label_to, "missing_codes": str(list(missing_codes))},
        category=NamesEnum.IR.value,
    )


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-001",
    category=NamesEnum.IR.value,
    requires={_COMPOSITION_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_relation_indicators_in_composition(ctx: RuleContext) -> list[Issue]:
    """COMP-001: every code in `descricao` and every code in `composicao` must match.

    Skipped entirely when `composicao` or `descricao` is empty (`requires`/this rule's own
    gate, matching `validate_relation_indicators_in_composition`'s own top-level skip). The
    abort case is reported as one issue per missing column (`codigo_pai`, `codigo_filho`,
    `codigo` order) rather than the legacy single combined string — the report text is
    unaffected, since both land in the same category bucket.
    """
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    if description_frame.empty:
        return []

    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)

    issues: list[Issue] = [
        _missing_column_issue("COMP-001", Severity.ERROR, NamesEnum.IR.value, composition_filename, column)
        for column in _missing_composition_columns(composition_frame)
    ]
    if _CODE not in description_frame.columns:
        issues.append(
            _missing_column_issue("COMP-001", Severity.ERROR, NamesEnum.IR.value, description_filename, _CODE)
        )
    if issues:
        return issues

    facts = _facts(ctx)
    if not facts.relation_checked:
        return []

    if facts.relation_missing_in_composition:
        issues.append(
            _relation_issue(
                "COMP-001", description_filename, composition_filename, facts.relation_missing_in_composition
            )
        )
    if facts.relation_missing_in_description:
        issues.append(
            _relation_issue(
                "COMP-001", composition_filename, description_filename, facts.relation_missing_in_description
            )
        )
    return issues


@COMPOSITION_REGISTRY.rule(rule_id="COMP-002", category=NamesEnum.IR.value, requires={_COMPOSITION_SHEET: ()})
def check_composition_graph_acyclic(ctx: RuleContext) -> list[Issue]:
    """COMP-002: the composition graph (all `composicao` edges) must be acyclic.

    Owns the missing-`codigo_pai`/`codigo_filho` abort for both COMP-002 and COMP-003 — the
    legacy `validate_relations_hierarchy_with_graph` covered both checks behind one column
    check, so COMP-003 stays silent on a missing column (see its docstring) to avoid the same
    text appearing twice.
    """
    frame = ctx.sheet(_COMPOSITION_SHEET)
    filename = _filename(ctx, _COMPOSITION_SHEET)
    missing = _missing_composition_columns(frame)
    if missing:
        return [
            _missing_column_issue("COMP-002", Severity.ERROR, NamesEnum.IR.value, filename, column)
            for column in missing
        ]

    facts = _facts(ctx)
    if not facts.has_cycle:
        return []
    return [
        Issue(
            rule_id="COMP-002",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=None,
            message_key="rule.COMP-002.error",
            params={"filename": filename, "cycle": _format_cycle_edges(facts.cycle)},
            category=NamesEnum.IR.value,
        )
    ]


@COMPOSITION_REGISTRY.rule(rule_id="COMP-003", category=NamesEnum.IR.value, requires={_COMPOSITION_SHEET: ()})
def check_composition_no_disconnected_groups(ctx: RuleContext) -> list[Issue]:
    """COMP-003: the composition graph must be a single weakly connected component.

    Silent when `codigo_pai`/`codigo_filho` is missing — COMP-002 already reports that abort
    (see its docstring); this mirrors the legacy code's single combined column check.
    """
    frame = ctx.sheet(_COMPOSITION_SHEET)
    if _missing_composition_columns(frame):
        return []

    facts = _facts(ctx)
    if not facts.disconnected_components:
        return []

    filename = _filename(ctx, _COMPOSITION_SHEET)
    reporter = GraphProcessing()
    formatted = ", ".join(
        f"[{reporter.generate_graph_report(component)}]" for component in facts.disconnected_components
    )
    return [
        Issue(
            rule_id="COMP-003",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=None,
            message_key="rule.COMP-003.error",
            params={"filename": filename, "disconnected": formatted},
            category=NamesEnum.IR.value,
        )
    ]


def _duplicated_values(frame: pd.DataFrame, column: str) -> list[str]:
    """Every value of `column` that appears more than once, in `value_counts()` order."""
    if column not in frame.columns or frame.empty:
        return []
    normalized = frame[column].astype(str).str.strip()
    if not normalized.duplicated().any():
        return []
    counts = normalized.value_counts()
    return counts[counts > 1].index.tolist()


def _duplicate_title_issues(
    ctx: RuleContext, facts: CompositionFacts, description_frame: pd.DataFrame, description_filename: str
) -> list[Issue]:
    """COMP-004's per-subtree duplicate-title warnings, one root-child subtree at a time."""
    graph_processing = GraphProcessing()
    tree = graph_processing.convert_to_tree(facts.root, facts.graph)
    root_children = list(tree.neighbors(facts.root))

    cleaned_codes = ctx.cleaned.get(_DESCRIPTION_SHEET, {}).get(_CODE)
    if cleaned_codes is None:
        return []
    code_as_str = cleaned_codes.astype(str)

    issues: list[Issue] = []
    for child in root_children:
        subtree = graph_processing.breadth_first_search_from_node(child, facts.graph)
        nodes = list(subtree.nodes())
        mask = code_as_str.isin(nodes)
        description_slice = description_frame.loc[code_as_str.index[mask]]

        for column, message_key in (
            (_SIMPLE_NAME, "rule.COMP-004.warning.simple_name"),
            (_COMPLETE_NAME, "rule.COMP-004.warning.complete_name"),
        ):
            duplicated = _duplicated_values(description_slice, column)
            if not duplicated:
                continue
            issues.append(
                Issue(
                    rule_id="COMP-004",
                    severity=Severity.WARNING,
                    sheet=description_filename,
                    row=None,
                    column=column,
                    message_key=message_key,
                    params={
                        "filename": description_filename,
                        "duplicated_values": str(duplicated),
                    },
                    category=NamesEnum.UT.value,
                )
            )
    return issues


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-004",
    category=NamesEnum.UT.value,
    requires={_COMPOSITION_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_unique_titles_per_subtree(ctx: RuleContext) -> list[Issue]:
    """COMP-004: `nome_simples`/`nome_completo` must be unique inside each root-child's subtree.

    Produces nothing at all (matching `validate_unique_titles_with_graph`'s own gating,
    BUG-019) when: `composicao`/`descricao` is empty (`requires`); a required column is
    missing (reported here — this rule's own required-column set, matching the legacy
    method's own independent check); COMP-001's code comparison would itself report a
    mismatch; the graph has a cycle or is disconnected. Only the missing-root case
    (`root_present` is `False`) is reported as an error; every other case above is silent.
    """
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    if description_frame.empty:
        return []

    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)

    issues: list[Issue] = [
        _missing_column_issue("COMP-004", Severity.WARNING, NamesEnum.UT.value, composition_filename, column)
        for column in _missing_composition_columns(composition_frame)
    ]
    for column in (_CODE, _SIMPLE_NAME, _COMPLETE_NAME):
        if column not in description_frame.columns:
            issues.append(
                _missing_column_issue("COMP-004", Severity.WARNING, NamesEnum.UT.value, description_filename, column)
            )
    if issues:
        return issues

    # `facts.available` is always `True` here: it is derived from the same
    # `_missing_composition_columns` check already run above (an early `return` on any miss),
    # so it is never re-checked (there would be nothing left for it to catch).
    facts = _facts(ctx)
    if facts.relation_checked and (facts.relation_missing_in_composition or facts.relation_missing_in_description):
        return []
    if facts.has_cycle or facts.disconnected_components:
        return []
    if not facts.root_present:
        return [
            Issue(
                rule_id="COMP-004",
                severity=Severity.ERROR,
                sheet=composition_filename,
                row=None,
                column=None,
                message_key="rule.COMP-004.root_missing.error",
                params={"filename": composition_filename, "root": facts.root},
                category=NamesEnum.UT.value,
            )
        ]

    return _duplicate_title_issues(ctx, facts, description_frame, description_filename)


def _leaf_data_missing_column_issues(ctx: RuleContext, rule_id: str) -> list[Issue]:
    """The combined COMP-005/COMP-006 missing-column abort (one legacy method, one check)."""
    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    values_frame = ctx.sheet(_VALUES_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)

    issues: list[Issue] = [
        _missing_column_issue(rule_id, Severity.ERROR, NamesEnum.LEAF_NO_DATA.value, composition_filename, column)
        for column in _missing_composition_columns(composition_frame)
    ]
    if _ID not in values_frame.columns:
        issues.append(
            _missing_column_issue(rule_id, Severity.ERROR, NamesEnum.LEAF_NO_DATA.value, values_filename, _ID)
        )

    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    if ctx.options.get("proportionality_read_successful") and not proportionality_frame.empty:
        proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)
        is_multiindex = isinstance(proportionality_frame.columns, pd.MultiIndex)
        id_values = (
            proportionality_frame.columns.get_level_values(1) if is_multiindex else proportionality_frame.columns
        )
        if _ID not in id_values:
            issues.append(
                _missing_column_issue(
                    rule_id,
                    Severity.ERROR,
                    NamesEnum.LEAF_NO_DATA.value,
                    proportionality_filename,
                    _ID,
                    level2=is_multiindex,
                )
            )
    return issues


def _leaf_no_data_issue(rule_id: str, filename: str, leaf: str) -> Issue:
    """Build one COMP-005/COMP-006 "leaf indicator without data" `Issue`."""
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=filename,
        row=None,
        column=None,
        message_key=_LEAF_WITHOUT_DATA_KEY,
        params={"filename": filename, "leaf": leaf},
        category=NamesEnum.LEAF_NO_DATA.value,
    )


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-005", category=NamesEnum.LEAF_NO_DATA.value, requires={_COMPOSITION_SHEET: (), _VALUES_SHEET: ()}
)
def check_leaf_indicators_have_values(ctx: RuleContext) -> list[Issue]:
    """COMP-005: every leaf indicator (no children) must have a `valores` column.

    Skipped entirely when `composicao` or `valores` is empty (`requires` — this ALSO gates
    COMP-006, even when `proporcionalidades` itself has data, reproducing the legacy quirk
    exactly: both checks share one top-level `if value_frame.empty` gate in
    `validate_associated_indicators_leafs`). Owns the combined missing-column abort for both
    COMP-005 and COMP-006 (one legacy method, one column check) — COMP-006 stays silent on a
    missing column.
    """
    issues = _leaf_data_missing_column_issues(ctx, "COMP-005")
    if issues:
        return issues

    # `facts.available` is always `True` here — see COMP-004's equivalent comment.
    facts = _facts(ctx)

    values_frame = ctx.sheet(_VALUES_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)
    codes_in_values = {column.split("-", 1)[0] for column in values_frame.columns}
    return [
        _leaf_no_data_issue("COMP-005", values_filename, leaf) for leaf in facts.leafs if leaf not in codes_in_values
    ]


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-006", category=NamesEnum.LEAF_NO_DATA.value, requires={_COMPOSITION_SHEET: (), _VALUES_SHEET: ()}
)
def check_leaf_indicators_have_proportionality(ctx: RuleContext) -> list[Issue]:
    """COMP-006: every leaf indicator must appear in `proporcionalidades` (when delivered).

    Skipped when `composicao`/`valores` is empty (see COMP-005's docstring — the same legacy
    top gate covers both) or when `proporcionalidades` was not read successfully / is empty.
    Silent (no issue) when a required column was missing — COMP-005 already reports that (one
    legacy method, one column check).
    """
    if _leaf_data_missing_column_issues(ctx, "COMP-006"):
        return []

    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    if not ctx.options.get("proportionality_read_successful") or proportionality_frame.empty:
        return []

    # `facts.available` is always `True` here — see COMP-004's equivalent comment.
    facts = _facts(ctx)

    proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)
    level_two_columns = [
        column for column in proportionality_frame.columns.get_level_values(1).unique().tolist() if column != _ID
    ]
    level_two_columns = [column for column in level_two_columns if not column.lower().startswith("unnamed")]
    codes_in_proportionality = {column.split("-", 1)[0] for column in level_two_columns}

    return [
        _leaf_no_data_issue("COMP-006", proportionality_filename, leaf)
        for leaf in facts.leafs
        if leaf not in codes_in_proportionality
    ]


def _tree_required_column_issues(ctx: RuleContext, rule_id: str, category: str) -> list[Issue]:
    """The shared composicao+descricao required-column check for COMP-007/008/009.

    Reproduces `SpCompositionTreeValidator.global_required_columns` exactly, including
    `descricao.relacao` — vestigial (the model always injects a default `relacao` column, see
    `.specs/business-rules/composition.md`'s COMP-008 entry) but part of the legacy check.
    """
    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)

    issues: list[Issue] = [
        _missing_column_issue(rule_id, Severity.ERROR, category, composition_filename, column)
        for column in _missing_composition_columns(composition_frame)
    ]
    for column in (_CODE, _LEVEL, _RELATION):
        if column not in description_frame.columns:
            issues.append(_missing_column_issue(rule_id, Severity.ERROR, category, description_filename, column))
    return issues


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-007",
    category=NamesEnum.TH.value,
    requires={_COMPOSITION_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_composition_tree_acyclic(ctx: RuleContext) -> list[Issue]:
    """COMP-007: the composition tree (adjacency-dict view of `composicao`) must be acyclic.

    A DFS-based duplicate of COMP-002 under a different message shape (protocol gap, see
    `.specs/business-rules/composition.md`); requires `descricao`'s `codigo`/`nivel`/`relacao`
    in addition to `composicao`'s columns, matching `validate_hierarchy_with_tree`'s own
    combined required-columns check.
    """
    issues = _tree_required_column_issues(ctx, "COMP-007", NamesEnum.TH.value)
    if issues:
        return issues

    facts = _facts(ctx)
    if not facts.tree_has_cycle:
        return []
    filename = _filename(ctx, _COMPOSITION_SHEET)
    return [
        Issue(
            rule_id="COMP-007",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=None,
            message_key="rule.COMP-007.error",
            params={"filename": filename, "cycle_path": " -> ".join(facts.tree_cycle_path)},
            category=NamesEnum.TH.value,
        )
    ]


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-008",
    category=NamesEnum.TH.value,
    requires={_COMPOSITION_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_parent_level_below_child_level(ctx: RuleContext) -> list[Issue]:
    """COMP-008: a parent indicator's `nivel` must be lower than every one of its children's.

    Only reported when BOTH the parent's and the child's `nivel` are known in `descricao`
    (matches `_format_level_errors`'s `if parent is not None and child is not None`) — a code
    missing from `descricao` entirely is silently ignored here (COMP-009 reports that, in its
    own raw-string shape). Vectorised via `.map()` (PERF-001), replacing the deleted
    `TreeProcessing.validate_level_hierarchy`'s `iterrows()` loop.
    """
    issues = _tree_required_column_issues(ctx, "COMP-008", NamesEnum.TH.value)
    if issues:
        return issues

    facts = _facts(ctx)
    if not facts.description_levels_available or facts.edges.empty:
        return []

    filename = _filename(ctx, _COMPOSITION_SHEET)
    edges = facts.edges
    parent_levels = edges[_PARENT].map(facts.description_levels)
    child_levels = edges[_CHILD].map(facts.description_levels)
    violation_mask = parent_levels.notna() & child_levels.notna() & (parent_levels >= child_levels)

    return [
        Issue(
            rule_id="COMP-008",
            severity=Severity.ERROR,
            sheet=filename,
            row=int(idx),
            column=None,
            message_key="rule.COMP-008.error",
            params={
                "filename": filename,
                "row": int(idx) + 2,
                "parent": int(edges.loc[idx, _PARENT]),
                "parent_level": int(parent_levels.loc[idx]),
                "child": int(edges.loc[idx, _CHILD]),
                "child_level": int(child_levels.loc[idx]),
            },
            category=NamesEnum.TH.value,
        )
        for idx in edges.index[violation_mask]
    ]


@COMPOSITION_REGISTRY.rule(
    rule_id="COMP-009",
    category=NamesEnum.CHILD_LVL.value,
    requires={_COMPOSITION_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_children_share_parent_level(ctx: RuleContext) -> list[Issue]:
    """COMP-009: every child of the same parent must share one `nivel`; codes must resolve.

    Uses the RAW (uncleaned) `composicao`/`descricao` values, matching
    `validate_tree_levels_children` exactly (BUG-014: `"1"` vs `"1.0"` string mismatches are a
    known, preserved defect — not fixed by this port). Vectorised via `groupby`/`isin`/`.map()`
    (PERF-001), replacing the legacy method's two nested `iterrows()` loops.
    """
    issues = _tree_required_column_issues(ctx, "COMP-009", NamesEnum.CHILD_LVL.value)
    if issues:
        return issues

    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)

    levels_map = dict(zip(description_frame[_CODE], description_frame[_LEVEL]))

    issues = []
    for parent, group in composition_frame.groupby(_PARENT):
        if parent not in levels_map:
            issues.append(
                Issue(
                    rule_id="COMP-009",
                    severity=Severity.ERROR,
                    sheet=composition_filename,
                    row=None,
                    column=None,
                    message_key="rule.COMP-009.parent_missing",
                    params={"filename": composition_filename, "parent": parent},
                    category=NamesEnum.CHILD_LVL.value,
                )
            )
            continue

        children = group[_CHILD]
        known_mask = children.isin(levels_map.keys())
        for child in children[~known_mask]:
            issues.append(
                Issue(
                    rule_id="COMP-009",
                    severity=Severity.ERROR,
                    sheet=composition_filename,
                    row=None,
                    column=None,
                    message_key="rule.COMP-009.child_missing",
                    params={"filename": composition_filename, "child": child},
                    category=NamesEnum.CHILD_LVL.value,
                )
            )

        known_children = children[known_mask]
        if known_children.empty:
            continue
        child_levels = known_children.map(levels_map)
        if not (child_levels == child_levels.iloc[0]).all():
            pairs = ", ".join(
                f"indicador {child} possui nível '{level}'" for child, level in zip(known_children, child_levels)
            )
            issues.append(
                Issue(
                    rule_id="COMP-009",
                    severity=Severity.ERROR,
                    sheet=description_filename,
                    row=None,
                    column=None,
                    message_key="rule.COMP-009.level_mismatch",
                    params={"filename": description_filename, "parent": parent, "children": pairs},
                    category=NamesEnum.CHILD_LVL.value,
                )
            )
    return issues
