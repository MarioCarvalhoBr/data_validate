#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.territories` (PROTO-013, TERR-001…002).

Table-driven coverage per rule (present-and-valid, unknown ids, engine-level skip when the
registry is absent/malformed) built directly against the pure `check_*` functions and a
hand-built `RuleContext`, plus a small `Engine`-level slice proving the
`requires_options=("territory_registry_present",)` gate actually skips both rules
(`.claude/rules/testing.md`).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus, SkipReason
from data_validate.rules.territories import (
    TERRITORY_REGISTRY_RULES,
    check_proportionality_ids_in_registry,
    check_values_ids_in_registry,
)
from data_validate.specs.issues import Severity
from tests.factories import make_proportionality_frame, make_values_frame

_VALORES = "valores.xlsx"
_PROPORCIONALIDADES = "proporcionalidades.xlsx"


def _make_context(
    *,
    valores: pd.DataFrame | None = None,
    proporcionalidades: pd.DataFrame | None = None,
    registry_ids: frozenset[int] | None = None,
    registry_present: bool = True,
) -> RuleContext:
    """Build a `RuleContext` wrapping whichever territory-domain sheets a test needs."""
    sheets: dict[str, pd.DataFrame] = {}
    filenames: dict[str, str] = {}
    for name, frame, filename in (
        ("valores", valores, _VALORES),
        ("proporcionalidades", proporcionalidades, _PROPORCIONALIDADES),
    ):
        if frame is not None:
            sheets[name] = frame
            filenames[name] = filename

    return RuleContext(
        sheets=sheets,
        cleaned={},
        options={
            "filenames": filenames,
            "territory_registry_present": registry_present,
            "territory_registry_ids": registry_ids if registry_ids is not None else frozenset(),
        },
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestTerritoryRegistryRulesShape:
    """The registry declares exactly TERR-001/TERR-002, in that order, under the TERR category."""

    def test_registry_contains_both_terr_ids_in_order(self) -> None:
        assert [spec.rule_id for spec in TERRITORY_REGISTRY_RULES] == ["TERR-001", "TERR-002"]

    def test_both_rules_are_under_the_terr_category(self) -> None:
        for spec in TERRITORY_REGISTRY_RULES:
            assert spec.category == NamesEnum.TERR.value

    def test_both_rules_are_gated_on_territory_registry_present(self) -> None:
        for spec in TERRITORY_REGISTRY_RULES:
            assert spec.requires_options == ("territory_registry_present",)

    def test_severity_default_is_error(self) -> None:
        for spec in TERRITORY_REGISTRY_RULES:
            assert spec.severity_default is Severity.ERROR


class TestCheckValuesIdsInRegistry:
    """TERR-001: every `valores.id` must exist in the territory registry."""

    def test_every_id_present_in_the_registry_reports_nothing(self) -> None:
        valores = make_values_frame(n_rows=2)
        ctx = _make_context(valores=valores, registry_ids=frozenset({1, 2}))

        assert check_values_ids_in_registry(ctx) == []

    def test_an_unknown_id_is_reported_with_its_row(self) -> None:
        valores = make_values_frame(n_rows=2)  # ids "1", "2"
        ctx = _make_context(valores=valores, registry_ids=frozenset({1}))

        issues = check_values_ids_in_registry(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TERR-001"
        assert issue.severity is Severity.ERROR
        assert issue.sheet == _VALORES
        assert issue.row == 1
        assert issue.column == "id"
        assert issue.message_key == "rule.TERR-001.error"
        assert issue.params == {"filename": _VALORES, "row": 3, "value": "2"}
        assert issue.category == NamesEnum.TERR.value

    def test_every_id_unknown_reports_one_issue_per_row(self) -> None:
        valores = make_values_frame(n_rows=3)
        ctx = _make_context(valores=valores, registry_ids=frozenset())

        issues = check_values_ids_in_registry(ctx)

        assert [issue.params["value"] for issue in issues] == ["1", "2", "3"]
        assert [issue.params["row"] for issue in issues] == [2, 3, 4]

    def test_a_non_numeric_id_is_reported_as_unknown(self) -> None:
        valores = make_values_frame(n_rows=1)
        valores = valores.copy()
        valores.loc[0, "id"] = "abc"
        ctx = _make_context(valores=valores, registry_ids=frozenset({1}))

        issues = check_values_ids_in_registry(ctx)

        assert len(issues) == 1
        assert issues[0].params["value"] == "abc"


class TestCheckProportionalityIdsInRegistry:
    """TERR-002: every `proporcionalidades.id` (level-2 header) must exist in the registry."""

    def test_every_id_present_in_the_registry_reports_nothing(self) -> None:
        proporcionalidades = make_proportionality_frame(n_rows=2)  # ids "1", "2"
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1, 2}))

        assert check_proportionality_ids_in_registry(ctx) == []

    def test_an_unknown_id_is_reported_with_its_double_header_row(self) -> None:
        proporcionalidades = make_proportionality_frame(n_rows=2)
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1}))

        issues = check_proportionality_ids_in_registry(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TERR-002"
        assert issue.severity is Severity.ERROR
        assert issue.sheet == _PROPORCIONALIDADES
        assert issue.row == 1
        assert issue.column == "id"
        assert issue.message_key == "rule.TERR-002.error"
        # Double-header row numbering: idx + 3, not the single-header idx + 2 (TERR-001).
        assert issue.params == {"filename": _PROPORCIONALIDADES, "row": 4, "value": "2"}
        assert issue.category == NamesEnum.TERR.value

    def test_every_id_unknown_reports_one_issue_per_row(self) -> None:
        proporcionalidades = make_proportionality_frame(n_rows=3)
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset())

        issues = check_proportionality_ids_in_registry(ctx)

        assert [issue.params["value"] for issue in issues] == ["1", "2", "3"]
        assert [issue.params["row"] for issue in issues] == [3, 4, 5]

    def test_a_real_bundle_s_blank_top_header_id_column_is_still_found(self) -> None:
        """Regression: `pandas.read_excel(header=[0, 1])` renders a blank top header cell as
        `"Unnamed: 0_level_0"`, not `"id"` -- a real `proporcionalidades.xlsx`'s `id` column is
        `("Unnamed: 0_level_0", "id")`, never `("id", "id")` (that shape is only
        `tests/factories.py::make_proportionality_frame`'s own convenience choice). Found first
        via a golden-fixture run (data_ground_truth_02_registry) where this rule silently found
        nothing against real data before this test/fix.
        """
        columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "id"), ("2-2020", "4-2020")])
        proporcionalidades = pd.DataFrame([["1", "0.500"], ["9", "0.500"]], columns=columns)
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1}))

        issues = check_proportionality_ids_in_registry(ctx)

        assert len(issues) == 1
        assert issues[0].params["value"] == "9"

    def test_a_sheet_with_no_locatable_id_column_reports_nothing(self) -> None:
        """A structurally broken `proporcionalidades` (no `id` column at all) is PROP-001/PROP-002's
        concern, not TERR-002's -- this rule silently finds nothing rather than inventing its own
        missing-column error."""
        columns = pd.MultiIndex.from_tuples([("2-2020", "4-2020"), ("2-2020", "5-2020")])
        proporcionalidades = pd.DataFrame([["0.500", "0.500"]], columns=columns)
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1}))

        assert check_proportionality_ids_in_registry(ctx) == []


class TestTerritoryRegistryEngineGating:
    """Absent/malformed registry (`territory_registry_present=False`) skips both rules."""

    def test_registry_absent_skips_every_registered_rule(self) -> None:
        """Both sheets present, but the registry itself is absent/malformed."""
        ctx = _make_context(
            valores=make_values_frame(n_rows=1),
            proporcionalidades=make_proportionality_frame(n_rows=1),
            registry_present=False,
        )
        result = Engine(TERRITORY_REGISTRY_RULES).run(ctx)

        assert [outcome.status for outcome in result.outcomes] == [RuleStatus.SKIPPED, RuleStatus.SKIPPED]
        assert all(outcome.skip_reason == SkipReason.DISABLED_BY_OPTION for outcome in result.outcomes)
        assert result.validation_result.issues == ()

    def test_registry_present_and_valid_runs_both_rules(self) -> None:
        ctx = _make_context(
            valores=make_values_frame(n_rows=1),
            proporcionalidades=make_proportionality_frame(n_rows=1),
            registry_ids=frozenset({1}),
            registry_present=True,
        )
        result = Engine(TERRITORY_REGISTRY_RULES).run(ctx)

        assert [outcome.status for outcome in result.outcomes] == [RuleStatus.PASSED, RuleStatus.PASSED]

    def test_proporcionalidades_absent_skips_only_terr_002(self) -> None:
        """An optional, genuinely-missing sheet skips TERR-002 with MISSING_SHEET, not the option gate."""
        ctx = _make_context(valores=make_values_frame(n_rows=1), registry_ids=frozenset({1}), registry_present=True)
        result = Engine(TERRITORY_REGISTRY_RULES).run(ctx)

        outcomes = {outcome.rule_id: outcome for outcome in result.outcomes}
        assert outcomes["TERR-001"].status is RuleStatus.PASSED
        assert outcomes["TERR-002"].status is RuleStatus.SKIPPED
        assert outcomes["TERR-002"].skip_reason == SkipReason.MISSING_SHEET


class TestTerritoryRegistryHelperFallbacks:
    """Direct `RuleContext` construction for the private helpers' less-common branches."""

    def test_filename_falls_back_to_the_sheet_name_when_no_filenames_option_is_given(self) -> None:
        """`_filename` returns the bare sheet name when `ctx.options` carries no `"filenames"`."""
        ctx = RuleContext(
            sheets={"valores": make_values_frame(n_rows=1, codes=(1,))},
            cleaned={},
            options={"territory_registry_present": True, "territory_registry_ids": frozenset({1})},
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        assert check_values_ids_in_registry(ctx) == []

    def test_registry_ids_accepts_a_plain_set(self) -> None:
        ctx = RuleContext(
            sheets={"valores": make_values_frame(n_rows=1, codes=(1,))},
            cleaned={},
            options={
                "filenames": {"valores": _VALORES},
                "territory_registry_present": True,
                "territory_registry_ids": {1, 2, 3},
            },
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        assert check_values_ids_in_registry(ctx) == []

    def test_registry_ids_accepts_a_plain_list(self) -> None:
        ctx = RuleContext(
            sheets={"valores": make_values_frame(n_rows=1, codes=(1,))},
            cleaned={},
            options={
                "filenames": {"valores": _VALORES},
                "territory_registry_present": True,
                "territory_registry_ids": [1, 2, 3],
            },
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        assert check_values_ids_in_registry(ctx) == []

    def test_registry_ids_falls_back_to_empty_for_an_unsupported_type(self) -> None:
        """A malformed option value (neither frozenset/set/list/tuple) is treated as no ids."""
        ctx = RuleContext(
            sheets={"valores": make_values_frame(n_rows=1, codes=(1,))},
            cleaned={},
            options={
                "filenames": {"valores": _VALORES},
                "territory_registry_present": True,
                "territory_registry_ids": "not-a-container",
            },
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        issues = check_values_ids_in_registry(ctx)

        assert len(issues) == 1

    def test_proportionality_id_column_is_found_on_a_flat_single_header_frame(self) -> None:
        """`_proportionality_id_column`'s non-`MultiIndex` branch (a plain, flat `id` column)."""
        proporcionalidades = pd.DataFrame({"id": ["1", "9"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1}))

        issues = check_proportionality_ids_in_registry(ctx)

        assert len(issues) == 1
        assert issues[0].params["value"] == "9"

    def test_proportionality_id_column_is_none_on_a_flat_frame_without_id(self) -> None:
        proporcionalidades = pd.DataFrame({"2-2020": ["0.5"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, registry_ids=frozenset({1}))

        assert check_proportionality_ids_in_registry(ctx) == []
