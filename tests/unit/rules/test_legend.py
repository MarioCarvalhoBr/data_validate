#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.legend` (Phase 3 Port 6, LEG-012…015).

Table-driven coverage per rule (happy path, each failure mode, the shared missing-column abort,
the `legend_sanity_ok`/`legend_read_success` option gates, and the engine-level empty-sheet skip)
built directly against the pure `check_*` functions and a hand-built `RuleContext` — no engine
beyond `TestLegendRegistryShape`, no mocks (`.claude/rules/testing.md`). Sheet data comes from
`tests/factories.py` where convenient, otherwise a minimal ad hoc `pd.DataFrame` (matching the
BUG-014 regression tests this module migrates).

Rewrites the untested legacy `legend_validator.py::SpLegendValidator` (deleted, see
`.specs/business-rules/legend.md`'s LEG-012…015 entries and ARC-017 Phase 3 Port 6), migrating
`tests/unit/validators/spreadsheets/legend/test_legend_validator.py`'s BUG-014 regressions
(string-vs-numeric `nivel` comparisons) onto the new rule functions. `LEG-001`…`LEG-011` (the
per-legend-group structural/cleaning checks) are out of this port's scope and stay covered by
`tests/unit/helpers/common/validation/test_legend_processing.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.legend import (
    LEGEND_REGISTRY,
    check_level_one_must_not_reference_legend,
    check_other_levels_must_reference_legend,
    check_relation_missing_and_unreferenced_codes,
    check_value_range_within_legend,
)
from data_validate.specs.issues import Severity
from tests.factories import DATA_UNAVAILABLE, LABEL_DATA_UNAVAILABLE, di_at, make_legend_frame, make_values_frame

_DESCRICAO = "descricao.xlsx"
_LEGENDA = "legenda.xlsx"
_VALORES = "valores.xlsx"


def _make_context(
    *,
    descricao: pd.DataFrame | None = None,
    legenda: pd.DataFrame | None = None,
    valores: pd.DataFrame | None = None,
    legend_sanity_ok: bool = True,
    legend_read_success: bool = True,
    scenarios: list[str] | None = None,
    min_lower_legend_default: object = 0,
    max_upper_legend_default: object = 1,
) -> RuleContext:
    """Build a `RuleContext` over a legend-relevant bundle, with every LEG option set."""
    sheets: dict[str, pd.DataFrame] = {}
    if descricao is not None:
        sheets["descricao"] = descricao
    if legenda is not None:
        sheets["legenda"] = legenda
    if valores is not None:
        sheets["valores"] = valores

    return RuleContext(
        sheets=sheets,
        cleaned={},
        options={
            "filenames": {"descricao": _DESCRICAO, "legenda": _LEGENDA, "valores": _VALORES},
            "legend_sanity_ok": legend_sanity_ok,
            "legend_read_success": legend_read_success,
            "scenarios": scenarios or [],
            "min_lower_legend_default": min_lower_legend_default,
            "max_upper_legend_default": max_upper_legend_default,
            "label_data_unavailable": LABEL_DATA_UNAVAILABLE,
            "value_data_unavailable": DATA_UNAVAILABLE,
        },
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestLegendRegistryShape:
    """The registry declares exactly the LEG ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_leg_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in LEGEND_REGISTRY] == ["LEG-012", "LEG-013", "LEG-014", "LEG-015"]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in LEGEND_REGISTRY}
        assert categories == {
            "LEG-012": NamesEnum.LEG_REL.value,
            "LEG-013": NamesEnum.LEG_REL.value,
            "LEG-014": NamesEnum.LEG_REL.value,
            "LEG-015": NamesEnum.LEG_RANGE.value,
        }

    def test_empty_description_skips_every_rule_silently(self) -> None:
        ctx = _make_context(descricao=pd.DataFrame(), valores=make_values_frame())
        result = Engine(LEGEND_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()

    def test_empty_values_skips_only_leg_015(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "legenda": [pd.NA]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=pd.DataFrame())
        result = Engine(LEGEND_REGISTRY).run(ctx)
        statuses = {outcome.rule_id: outcome.status for outcome in result.outcomes}
        assert statuses["LEG-015"] is RuleStatus.SKIPPED
        assert statuses["LEG-012"] is not RuleStatus.SKIPPED


class TestRelationLegendSanityGate:
    """LEG-012/013/014 report nothing at all when `legend_sanity_ok` is falsy."""

    @pytest.mark.parametrize(
        "check",
        [
            check_relation_missing_and_unreferenced_codes,
            check_level_one_must_not_reference_legend,
            check_other_levels_must_reference_legend,
        ],
    )
    def test_legend_sanity_not_ok_reports_nothing(self, check) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "legenda": ["9"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": ["1"]}), legend_sanity_ok=False)
        assert check(ctx) == []


class TestCheckRelationMissingAndUnreferencedCodes:
    """LEG-012: every `descricao.legenda` code must exist in `legenda`; the reverse is a warning."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "3"], "legenda": [pd.NA, "5"]})
        legenda = pd.DataFrame({"codigo": ["5"]})
        ctx = _make_context(descricao=descricao, legenda=legenda)
        assert check_relation_missing_and_unreferenced_codes(ctx) == []

    def test_a_legend_code_missing_from_legenda_is_an_error(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "3"], "legenda": [pd.NA, "7"]})
        legenda = pd.DataFrame({"codigo": []})
        ctx = _make_context(descricao=descricao, legenda=legenda)

        issues = check_relation_missing_and_unreferenced_codes(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "LEG-012"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.LEG_REL.value
        assert issue.message_key == "rule.LEG-012.error"
        assert issue.params == {"filename": _DESCRICAO, "legend_filename": _LEGENDA, "missing_codes": "[7]"}

    def test_an_unreferenced_legend_code_is_a_warning(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "3"], "legenda": [pd.NA, "5"]})
        legenda = pd.DataFrame({"codigo": ["5", "9"]})
        ctx = _make_context(descricao=descricao, legenda=legenda)

        issues = check_relation_missing_and_unreferenced_codes(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity is Severity.WARNING
        assert issue.message_key == "rule.LEG-012.warning"
        assert issue.params == {"filename": _LEGENDA, "description_filename": _DESCRICAO, "missing_codes": "[9]"}

    @pytest.mark.parametrize("missing_column", ["codigo", "nivel", "legenda"])
    def test_missing_column_reports_only_the_shared_abort(self, missing_column: str) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "legenda": [pd.NA]}).drop(columns=[missing_column])
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}))

        issues = check_relation_missing_and_unreferenced_codes(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.legend.missing_required_column"
        assert issues[0].params == {"filename": _DESCRICAO, "column": missing_column}

    def test_missing_column_silences_leg_013_and_leg_014(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}))

        assert check_level_one_must_not_reference_legend(ctx) == []
        assert check_other_levels_must_reference_legend(ctx) == []


class TestCheckLevelOneMustNotReferenceLegend:
    """LEG-013: no level-1 `descricao` row may carry a `legenda` reference (BUG-014)."""

    def test_a_level_one_indicator_without_a_legend_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "legenda": [pd.NA]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}))
        assert check_level_one_must_not_reference_legend(ctx) == []

    def test_a_float_formatted_level_one_with_a_legend_reference_is_still_caught(self) -> None:
        """BUG-014: `nivel = "1.0"` must still match the level-1 comparison."""
        descricao = pd.DataFrame({"codigo": ["10"], "nivel": ["1.0"], "legenda": ["5"]})
        legenda = pd.DataFrame({"codigo": ["5"]})
        ctx = _make_context(descricao=descricao, legenda=legenda)

        issues = check_level_one_must_not_reference_legend(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "LEG-013"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.LEG-013.error"
        assert issue.params == {"filename": _DESCRICAO, "legend_filename": _LEGENDA, "codes": "['10']"}


class TestCheckOtherLevelsMustReferenceLegend:
    """LEG-014: every non-1/2-level `descricao` row must carry a `legenda` reference (BUG-014)."""

    def test_a_level_two_indicator_without_a_legend_reports_nothing(self) -> None:
        """BUG-014: `nivel = "2.0"` must still be excluded from the "other levels" mask."""
        descricao = pd.DataFrame({"codigo": ["20"], "nivel": ["2.0"], "legenda": [pd.NA]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}))
        assert check_other_levels_must_reference_legend(ctx) == []

    def test_a_level_three_indicator_without_a_legend_is_an_error(self) -> None:
        descricao = pd.DataFrame({"codigo": ["30"], "nivel": ["3"], "legenda": [pd.NA]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}))

        issues = check_other_levels_must_reference_legend(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "LEG-014"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.LEG-014.error"
        assert issue.params == {"filename": _DESCRICAO, "legend_filename": _LEGENDA, "codes": "['30']"}

    def test_a_level_three_indicator_with_a_legend_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["30"], "nivel": ["3"], "legenda": ["5"]})
        legenda = pd.DataFrame({"codigo": ["5"]})
        ctx = _make_context(descricao=descricao, legenda=legenda)
        assert check_other_levels_must_reference_legend(ctx) == []


class TestCheckValueRangeWithinLegend:
    """LEG-015: every pattern-matching `valores` cell must fall inside its legend's range."""

    def test_a_value_within_the_default_range_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": [pd.NA]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["0.50"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)
        assert check_value_range_within_legend(ctx) == []

    def test_a_value_above_the_default_range_is_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": [pd.NA]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["1.50"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "LEG-015"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.LEG_RANGE.value
        assert issue.row == 0
        assert issue.column == "2-2020"
        assert issue.message_key == "rule.LEG-015.error_default"
        assert issue.params == {
            "filename": _VALORES,
            "row": 2,
            "value": "1.50",
            "min_value": 0,
            "max_value": 1,
            "column": "2-2020",
        }

    def test_a_value_outside_a_coded_legend_range_names_the_legend(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": ["7"]})
        legenda = make_legend_frame(codes=(7,))
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["150.00"]})
        ctx = _make_context(descricao=descricao, legenda=legenda, valores=valores)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.LEG-015.error_coded"
        assert issue.params == {
            "filename": _VALORES,
            "row": 2,
            "value": "150.00",
            "legend_id": "7",
            "min_value": 0.0,
            "max_value": 100.0,
            "column": "2-2020",
        }

    def test_a_di_marker_is_never_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": [pd.NA]})
        valores = di_at(pd.DataFrame({"id": ["1"], "2-2020": ["1.50"]}), row=0, column="2-2020")
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)
        assert check_value_range_within_legend(ctx) == []

    def test_a_level_one_indicator_is_excluded_even_with_a_float_formatted_level(self) -> None:
        """BUG-014: `nivel = "1.0"` must still exclude the column from range validation."""
        descricao = pd.DataFrame({"codigo": ["10"], "nivel": ["1.0"], "legenda": [pd.NA]})
        valores = pd.DataFrame({"10-2020": ["5.00"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)
        assert check_value_range_within_legend(ctx) == []

    def test_a_value_column_with_no_matching_description_row_uses_the_default_range(self) -> None:
        """`valores` may carry a column for an indicator absent from `descricao` (VAL-002's own
        concern, not LEG-015's) — the range check must still fall back to the default range
        rather than raise."""
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": [pd.NA]})
        valores = pd.DataFrame({"id": ["1"], "99-2020": ["1.50"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.LEG-015.error_default"

    def test_a_legend_group_with_only_the_unavailable_label_falls_back_to_the_default_range(self) -> None:
        """A legend group made only of the `Dado indisponível` row still names the legend code
        (`ModelMappingLegend.legend_id` is set to `descricao.legenda`'s own value as soon as
        *any* group matches, before its non-DI-row emptiness is even checked — it is only
        overwritten by the legend's own `codigo` when a usable range is actually found) but
        keeps the default `min`/`max`, since no parseable `minimo`/`maximo` was found."""
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": ["7"]})
        legenda = pd.DataFrame({"codigo": ["7"], "label": [LABEL_DATA_UNAVAILABLE], "minimo": [""], "maximo": [""]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["1.50"]})
        ctx = _make_context(descricao=descricao, legenda=legenda, valores=valores)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.LEG-015.error_coded"
        assert issues[0].params["legend_id"] == 7
        assert issues[0].params["min_value"] == 0
        assert issues[0].params["max_value"] == 1

    @pytest.mark.parametrize("missing_column", ["codigo", "nivel", "legenda"])
    def test_missing_column_reports_the_shared_abort(self, missing_column: str) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": [pd.NA]}).drop(columns=[missing_column])
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["0.50"]})
        ctx = _make_context(descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.legend.missing_required_column"
        assert issues[0].params == {"filename": _DESCRICAO, "column": missing_column}

    def test_legenda_column_not_required_when_legend_file_was_not_read_successfully(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["0.50"]})
        ctx = _make_context(
            descricao=descricao, legenda=pd.DataFrame({"codigo": []}), valores=valores, legend_read_success=False
        )
        assert check_value_range_within_legend(ctx) == []

    def test_legend_sanity_not_ok_falls_back_to_the_default_range(self) -> None:
        descricao = pd.DataFrame({"codigo": ["2"], "nivel": ["2"], "legenda": ["7"]})
        legenda = make_legend_frame(codes=(7,))
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["1.50"]})
        ctx = _make_context(descricao=descricao, legenda=legenda, valores=valores, legend_sanity_ok=False)

        issues = check_value_range_within_legend(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.LEG-015.error_default"
        assert issues[0].params["min_value"] == 0
        assert issues[0].params["max_value"] == 1


class TestIdempotency:
    """BUG-001: no rule here holds shared mutable state — calling one twice must be stable."""

    def test_every_check_is_idempotent_on_the_same_context(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "3"], "legenda": [pd.NA, "7"]})
        legenda = pd.DataFrame({"codigo": ["5"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["1.50"]})
        ctx = _make_context(descricao=descricao, legenda=legenda, valores=valores)

        assert check_relation_missing_and_unreferenced_codes(ctx) == check_relation_missing_and_unreferenced_codes(ctx)
        assert check_level_one_must_not_reference_legend(ctx) == check_level_one_must_not_reference_legend(ctx)
        assert check_other_levels_must_reference_legend(ctx) == check_other_levels_must_reference_legend(ctx)
        assert check_value_range_within_legend(ctx) == check_value_range_within_legend(ctx)
