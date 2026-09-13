#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.temporal_reference` (Phase 3 Port 4, TEMP-001…003).

Table-driven coverage per rule (happy path, each failure mode, missing-column abort, and the
engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no engine, no mocks (`.claude/rules/testing.md`). Sheet data comes
from `tests/factories.py` (`make_temporal_frame`), mutated per-case as the factory's own
docstring recommends.

Rewrites the deleted `temporal_reference_validator.py::SpTemporalReferenceValidator` (see
`.specs/business-rules/temporal-reference.md`'s TEMP-001…003 entries and ARC-017 Phase 3 Port 4),
including the BUG-007 regression tests migrated from
`tests/unit/validators/spreadsheets/temporal_reference/test_temporal_reference_validator.py`
(deleted): a non-numeric `simbolo` must not raise and must be silently skipped while a genuinely
past numeric year is still reported, and two independent contexts must not leak state.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.temporal_reference import (
    TEMPORAL_REGISTRY,
    check_description_ends_with_period,
    check_name_and_symbol_are_unique,
    check_reference_years_are_future,
    check_single_observed_reference,
    check_symbol_is_four_digits,
)
from data_validate.specs.issues import Severity
from tests.factories import make_temporal_frame

_FILENAME = "referencia_temporal.xlsx"


def _make_context(frame: pd.DataFrame, *, current_year: int = 2026) -> RuleContext:
    """Build a `RuleContext` wrapping a single `referencia_temporal` frame.

    Args:
        frame: The `referencia_temporal` sheet under test.
        current_year: The year `ctx.clock().year` resolves to.
    """
    return RuleContext(
        sheets={"referencia_temporal": frame},
        cleaned={},
        options={"filenames": {"referencia_temporal": _FILENAME}},
        translate=lambda key, **params: key,
        clock=lambda: datetime(current_year, 1, 1, tzinfo=UTC),
    )


class TestTemporalRegistryShape:
    """The registry declares exactly the TEMP ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_temp_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in TEMPORAL_REGISTRY] == [
            "TEMP-001",
            "TEMP-002",
            "TEMP-003",
            "TEMP-004",
            "TEMP-005",
        ]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in TEMPORAL_REGISTRY}
        assert categories == {
            "TEMP-001": NamesEnum.MAND_PUNC_TEMP.value,
            "TEMP-002": NamesEnum.YEARS_TEMP.value,
            "TEMP-003": NamesEnum.UVR_TEMP.value,
            "TEMP-004": NamesEnum.YEARS_TEMP.value,
            "TEMP-005": NamesEnum.YEARS_TEMP.value,
        }

    def test_empty_sheet_skips_every_rule_silently(self) -> None:
        ctx = _make_context(pd.DataFrame())
        result = Engine(TEMPORAL_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()


class TestCheckDescriptionEndsWithPeriod:
    """TEMP-001: `descricao` must end with a period."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_temporal_frame(years=[2020, 2021]))
        assert check_description_ends_with_period(ctx) == []

    def test_a_missing_period_is_reported_as_a_warning(self) -> None:
        frame = make_temporal_frame(years=[2020])
        frame.loc[0, "descricao"] = "Ano de referência 2020"
        ctx = _make_context(frame)

        issues = check_description_ends_with_period(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TEMP-001"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.MAND_PUNC_TEMP.value
        assert issue.message_key == "rule.TEMP-001.warning"
        assert issue.params == {"filename": _FILENAME, "row": 2, "column": "descricao"}

    def test_an_empty_description_is_not_reported(self) -> None:
        frame = make_temporal_frame(years=[2020])
        frame.loc[0, "descricao"] = ""
        ctx = _make_context(frame)
        assert check_description_ends_with_period(ctx) == []

    def test_missing_column_reports_a_warning(self) -> None:
        frame = make_temporal_frame().drop(columns=["descricao"])
        ctx = _make_context(frame)

        issues = check_description_ends_with_period(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.WARNING
        assert issues[0].message_key == "rule.temporal_reference.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "descricao"}


class TestCheckReferenceYearsAreFuture:
    """TEMP-002: every distinct `simbolo` (excluding the present-time row) must be a future year."""

    def test_only_future_years_report_nothing(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "2030"], "simbolo": ["2000", "2030"]})
        ctx = _make_context(frame, current_year=2026)
        assert check_reference_years_are_future(ctx) == []

    def test_a_past_year_is_reported_as_an_error(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "2020"], "simbolo": ["2000", "2020"]})
        ctx = _make_context(frame, current_year=2026)

        issues = check_reference_years_are_future(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TEMP-002"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.YEARS_TEMP.value
        assert issue.message_key == "rule.TEMP-002.error"
        assert issue.params == {"filename": _FILENAME, "year": "2020"}

    def test_a_year_equal_to_the_current_year_passes(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "2026"], "simbolo": ["2000", "2026"]})
        ctx = _make_context(frame, current_year=2026)
        assert check_reference_years_are_future(ctx) == []

    def test_the_present_time_row_is_excluded_even_when_past(self) -> None:
        frame = pd.DataFrame({"nome": ["atual"], "simbolo": ["2000"]})
        ctx = _make_context(frame, current_year=2026)
        assert check_reference_years_are_future(ctx) == []

    def test_a_non_numeric_symbol_is_skipped_without_raising(self) -> None:
        """BUG-007 regression: a symbol such as `"2030a"` must not raise and must not be
        reported (it is already reported as a data-cleaning error by the model), while a
        genuinely past numeric year in the same sheet is still reported."""
        frame = pd.DataFrame({"nome": ["atual", "b", "c", "d"], "simbolo": ["2000", "2030a", "2020", "2030"]})
        ctx = _make_context(frame, current_year=2026)

        issues = check_reference_years_are_future(ctx)

        assert [issue.params["year"] for issue in issues] == ["2020"]

    def test_two_independent_contexts_do_not_leak_state(self) -> None:
        """Regression companion to BUG-007's original class-level-Series bug: two contexts
        built from different frames in the same process must produce independent results."""
        past_year_ctx = _make_context(
            pd.DataFrame({"nome": ["atual", "2020"], "simbolo": ["2000", "2020"]}), current_year=2026
        )
        future_year_ctx = _make_context(
            pd.DataFrame({"nome": ["atual", "2030"], "simbolo": ["2000", "2030"]}), current_year=2026
        )

        assert check_reference_years_are_future(past_year_ctx) != []
        assert check_reference_years_are_future(future_year_ctx) == []

    def test_missing_column_aborts_with_one_error(self) -> None:
        frame = make_temporal_frame().drop(columns=["simbolo"])
        ctx = _make_context(frame)

        issues = check_reference_years_are_future(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.temporal_reference.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "simbolo"}


class TestCheckNameAndSymbolAreUnique:
    """TEMP-003: `nome` and `simbolo` must each contain no duplicated value."""

    def test_unique_values_report_nothing(self) -> None:
        ctx = _make_context(make_temporal_frame(years=[2020, 2021]))
        assert check_name_and_symbol_are_unique(ctx) == []

    def test_a_duplicated_symbol_is_reported(self) -> None:
        frame = pd.DataFrame({"nome": ["a", "b"], "descricao": ["A.", "B."], "simbolo": ["0", "0"]})
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TEMP-003"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.UVR_TEMP.value
        assert issue.message_key == "rule.TEMP-003.error"
        assert issue.params == {"filename": _FILENAME, "column": "simbolo"}

    def test_a_duplicated_name_is_reported(self) -> None:
        frame = pd.DataFrame({"nome": ["a", "a"], "descricao": ["A.", "B."], "simbolo": ["0", "1"]})
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert [issue.column for issue in issues] == ["nome"]

    @pytest.mark.parametrize("missing_column", ["nome", "simbolo"])
    def test_missing_column_reports_an_error(self, missing_column: str) -> None:
        frame = make_temporal_frame().drop(columns=[missing_column])
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert issues[0].message_key == "rule.temporal_reference.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": missing_column}

    def test_both_missing_columns_are_reported_in_order(self) -> None:
        frame = make_temporal_frame().drop(columns=["nome", "simbolo"])
        ctx = _make_context(frame)

        issues = check_name_and_symbol_are_unique(ctx)

        assert [issue.params["column"] for issue in issues] == ["nome", "simbolo"]


class TestCheckSymbolIsFourDigits:
    """TEMP-004 (PROTO-014, gap G-15): `simbolo` must be exactly four numeric characters."""

    def test_four_digit_symbols_report_nothing(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "futuro"], "simbolo": ["2020", "2021"]})
        ctx = _make_context(frame)
        assert check_symbol_is_four_digits(ctx) == []

    @pytest.mark.parametrize(
        "value",
        ["1", "12345", "203a", "20.0", "-202", ""],
        ids=["one_digit", "five_digits", "trailing_letter", "decimal", "signed", "empty"],
    )
    def test_a_non_four_digit_symbol_is_reported(self, value: str) -> None:
        frame = pd.DataFrame({"nome": ["atual", "b"], "simbolo": ["2000", value]})
        ctx = _make_context(frame)

        issues = check_symbol_is_four_digits(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TEMP-004"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.YEARS_TEMP.value
        assert issue.message_key == "rule.TEMP-004.error"
        assert issue.params == {"filename": _FILENAME, "row": 3, "column": "simbolo", "value": value}

    def test_missing_column_reports_an_error(self) -> None:
        frame = make_temporal_frame().drop(columns=["simbolo"])
        ctx = _make_context(frame)

        issues = check_symbol_is_four_digits(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.temporal_reference.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "simbolo"}


class TestCheckSingleObservedReference:
    """TEMP-005 (PROTO-014, gap G-16): at most one `simbolo` <= the current year."""

    def test_a_single_observed_reference_reports_nothing(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "2030"], "simbolo": ["2000", "2030"]})
        ctx = _make_context(frame, current_year=2026)
        assert check_single_observed_reference(ctx) == []

    def test_two_observed_references_are_reported_as_a_warning(self) -> None:
        frame = pd.DataFrame({"nome": ["atual", "passado", "futuro"], "simbolo": ["2000", "2020", "2030"]})
        ctx = _make_context(frame, current_year=2026)

        issues = check_single_observed_reference(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "TEMP-005"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.YEARS_TEMP.value
        assert issue.message_key == "rule.TEMP-005.warning"
        assert issue.params == {
            "filename": _FILENAME,
            "column": "simbolo",
            "observed_symbols": "['2000', '2020']",
        }

    def test_missing_column_reports_nothing(self) -> None:
        frame = make_temporal_frame().drop(columns=["simbolo"])
        ctx = _make_context(frame)
        assert check_single_observed_reference(ctx) == []
