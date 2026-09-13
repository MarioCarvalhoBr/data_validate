#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.scenario` (Phase 3 Port 4, SCEN-003…004).

Table-driven coverage per rule (happy path, each failure mode, missing-column abort, and the
engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no engine, no mocks (`.claude/rules/testing.md`). Sheet data comes
from `tests/factories.py` (`make_scenario_frame`), mutated per-case as the factory's own
docstring recommends.

Rewrites the untested legacy `scenario_validator.py::SpScenarioValidator` (deleted, see
`.specs/business-rules/scenarios.md`'s SCEN-003…004 entries and ARC-017 Phase 3 Port 4);
`SCEN-001`/`SCEN-002` (the model-level structural checks) are out of this port's scope and stay
covered by the `SpScenario` model tests.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.scenario import (
    SCENARIO_REGISTRY,
    check_name_and_symbol_are_unique,
    check_punctuation,
)
from data_validate.specs.issues import Severity
from tests.factories import make_scenario_frame

_FILENAME = "cenarios.xlsx"


def _make_context(frame: pd.DataFrame) -> RuleContext:
    """Build a `RuleContext` wrapping a single `cenarios` frame."""
    return RuleContext(
        sheets={"cenarios": frame},
        cleaned={},
        options={"filenames": {"cenarios": _FILENAME}},
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestScenarioRegistryShape:
    """The registry declares exactly the SCEN ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_scen_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in SCENARIO_REGISTRY] == ["SCEN-003", "SCEN-004"]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in SCENARIO_REGISTRY}
        assert categories == {
            "SCEN-003": NamesEnum.MAND_PUNC_SCEN.value,
            "SCEN-004": NamesEnum.UVR_SCEN.value,
        }

    def test_empty_sheet_skips_every_rule_silently(self) -> None:
        ctx = _make_context(pd.DataFrame())
        result = Engine(SCENARIO_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()


class TestCheckPunctuation:
    """SCEN-003: `nome` never ends with punctuation; `descricao` must end with a period."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_scenario_frame(symbols=("O", "P")))
        assert check_punctuation(ctx) == []

    def test_a_name_ending_with_punctuation_is_reported(self) -> None:
        frame = make_scenario_frame(symbols=("O",))
        frame.loc[0, "nome"] = "Otimista."
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "SCEN-003"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.MAND_PUNC_SCEN.value
        assert issue.message_key == "rule.SCEN-003.no_punctuation"
        assert issue.params == {"filename": _FILENAME, "row": 2, "column": "nome"}

    def test_a_missing_period_in_description_is_reported(self) -> None:
        frame = make_scenario_frame(symbols=("O",))
        frame.loc[0, "descricao"] = "Cenário otimista"
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.SCEN-003.must_end_with_dot"
        assert issues[0].params == {"filename": _FILENAME, "row": 2, "column": "descricao"}

    def test_an_empty_cell_is_not_reported(self) -> None:
        frame = make_scenario_frame(symbols=("O",))
        frame.loc[0, "nome"] = ""
        frame.loc[0, "descricao"] = ""
        ctx = _make_context(frame)
        assert check_punctuation(ctx) == []

    @pytest.mark.parametrize("missing_column", ["nome", "descricao"])
    def test_missing_column_reports_a_warning(self, missing_column: str) -> None:
        frame = make_scenario_frame(symbols=("O",)).drop(columns=[missing_column])
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert issues[0].severity is Severity.WARNING
        assert issues[0].message_key == "rule.scenario.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": missing_column}

    def test_both_missing_columns_are_reported_in_order(self) -> None:
        frame = make_scenario_frame(symbols=("O",)).drop(columns=["nome", "descricao"])
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert [issue.params["column"] for issue in issues] == ["nome", "descricao"]


class TestCheckNameAndSymbolAreUnique:
    """SCEN-004: `nome` and `simbolo` must each contain no duplicated value."""

    def test_unique_values_report_nothing(self) -> None:
        ctx = _make_context(make_scenario_frame(symbols=("O", "P")))
        assert check_name_and_symbol_are_unique(ctx) == []

    def test_a_duplicated_symbol_is_reported(self) -> None:
        frame = pd.DataFrame({"nome": ["a", "b"], "descricao": ["A.", "B."], "simbolo": ["O", "O"]})
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "SCEN-004"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.UVR_SCEN.value
        assert issue.message_key == "rule.SCEN-004.error"
        assert issue.params == {"filename": _FILENAME, "column": "simbolo"}

    def test_a_duplicated_name_is_reported(self) -> None:
        frame = pd.DataFrame({"nome": ["a", "a"], "descricao": ["A.", "B."], "simbolo": ["O", "P"]})
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert [issue.column for issue in issues] == ["nome"]

    @pytest.mark.parametrize("missing_column", ["nome", "simbolo"])
    def test_missing_column_reports_an_error(self, missing_column: str) -> None:
        frame = make_scenario_frame(symbols=("O",)).drop(columns=[missing_column])
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert issues[0].message_key == "rule.scenario.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": missing_column}

    def test_both_missing_columns_are_reported_in_order(self) -> None:
        frame = make_scenario_frame(symbols=("O",)).drop(columns=["nome", "simbolo"])
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert [issue.params["column"] for issue in issues] == ["nome", "simbolo"]
