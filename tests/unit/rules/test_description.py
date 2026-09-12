#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.description` (Phase 3 Port 2, DESC-001…010).

Table-driven coverage per rule (happy path, each failure mode, missing-column abort, and the
engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no engine, no mocks (`.claude/rules/testing.md`). Sheet data comes
from `tests/factories.py` (`make_description_frame`), mutated per-case as the factory's own
docstring recommends, never through `iterrows`/`unittest.mock`.

Rewrites the untested legacy `description_validator.py::SpDescriptionValidator` (deleted, see
`.specs/business-rules/description.md`'s TST-001 entries and ARC-017 Phase 3 Port 2): every
scenario the legacy class could reach through its `run()` validations list is reproduced here
against the corresponding pure rule function.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.description import (
    DESCRIPTION_REGISTRY,
    check_empty_strings,
    check_html_in_simple_description,
    check_indicator_levels,
    check_name_capitalization,
    check_no_cr_lf_characters,
    check_punctuation,
    check_sequential_codes,
    check_simple_description_length,
    check_title_length,
    check_unique_codes,
)
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.specs.issues import Severity
from tests.factories import make_description_frame

_FILENAME = "descricao.xlsx"


def _make_context(
    frame: pd.DataFrame,
    *,
    cleaned: dict[str, pd.Series] | None = None,
    expected_columns: tuple[str, ...] | None = None,
    no_warning_titles_length: bool = False,
    title_max_length: int = 40,
    simple_desc_max_length: int = 150,
) -> RuleContext:
    """Build a `RuleContext` wrapping a single `descricao` frame.

    Args:
        frame: The `descricao` sheet under test.
        cleaned: Cleaned columns to expose via `ctx.cleaned["descricao"]`; defaults to cleaning
            `codigo` losslessly from the frame itself (every cell parses as int).
        expected_columns: `EXPECTED_COLUMNS` as `SpDescription.pre_processing` would compute it;
            defaults to every column present in `frame`.
        no_warning_titles_length: Mirrors the `--no-warning-titles-length` CLI flag.
        title_max_length: Mirrors `ApplicationConfig.TITLE_OVER_N_CHARS`.
        simple_desc_max_length: Mirrors `ApplicationConfig.SIMPLE_DESCRIPTIONS_OVER_N_CHARS`.
    """
    if cleaned is None:
        cleaned = {}
        if "codigo" in frame.columns:
            cleaned["codigo"] = pd.to_numeric(frame["codigo"], errors="coerce").astype("Int64")
    resolved_expected_columns = expected_columns if expected_columns is not None else tuple(frame.columns)
    return RuleContext(
        sheets={"descricao": frame},
        cleaned={"descricao": cleaned},
        options={
            "filenames": {"descricao": _FILENAME},
            "expected_columns": resolved_expected_columns,
            "no_warning_titles_length": no_warning_titles_length,
            "title_max_length": title_max_length,
            "simple_desc_max_length": simple_desc_max_length,
        },
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestDescriptionRegistryShape:
    """The registry declares exactly the DESC ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_desc_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in DESCRIPTION_REGISTRY] == [
            "DESC-001",
            "DESC-002",
            "DESC-003",
            "DESC-004",
            "DESC-005",
            "DESC-006",
            "DESC-007",
            "DESC-008",
            "DESC-009",
            "DESC-010",
        ]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in DESCRIPTION_REGISTRY}
        assert categories == {
            "DESC-001": NamesEnum.HTML_DESC.value,
            "DESC-002": NamesEnum.SC.value,
            "DESC-003": NamesEnum.CO_UN.value,
            "DESC-004": NamesEnum.INP.value,
            "DESC-005": NamesEnum.IL.value,
            "DESC-006": NamesEnum.MAND_PUNC_DESC.value,
            "DESC-007": NamesEnum.EF.value,
            "DESC-008": NamesEnum.LB_DESC.value,
            "DESC-009": NamesEnum.SIMP_DESC_N.value,
            "DESC-010": NamesEnum.TITLES_N.value,
        }

    def test_empty_sheet_skips_every_rule_silently(self) -> None:
        ctx = _make_context(pd.DataFrame())
        result = Engine(DESCRIPTION_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()


class TestCheckHtmlInSimpleDescription:
    """DESC-001: `desc_simples` must not contain HTML tags."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame())
        assert check_html_in_simple_description(ctx) == []

    def test_an_html_tag_is_reported_as_a_warning(self) -> None:
        frame = make_description_frame(2)
        frame.loc[1, "desc_simples"] = "Descrição com <b>html</b>."
        ctx = _make_context(frame)

        issues = check_html_in_simple_description(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "DESC-001"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.HTML_DESC.value
        assert issue.message_key == "rule.DESC-001.warning"
        assert issue.params == {"filename": _FILENAME, "row": 3, "column": "desc_simples"}

    def test_missing_column_reports_an_error(self) -> None:
        frame = make_description_frame().drop(columns=["desc_simples"])
        ctx = _make_context(frame)

        issues = check_html_in_simple_description(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "desc_simples"}


class TestCheckSequentialCodes:
    """DESC-002: `codigo` must be 1, 2, ..., n after cleaning."""

    def test_sequential_codes_report_nothing(self) -> None:
        ctx = _make_context(make_description_frame(3))
        assert check_sequential_codes(ctx) == []

    def test_a_non_numeric_code_aborts_with_one_error(self) -> None:
        frame = make_description_frame(3)
        cleaned = pd.to_numeric(frame["codigo"], errors="coerce").astype("Int64")
        # Simulate the model's own cleaning step having dropped the invalid row.
        cleaned = cleaned.dropna().astype("int64")
        frame.loc[1, "codigo"] = "abc"
        ctx = _make_context(frame, cleaned={"codigo": cleaned.drop(index=1)})

        issues = check_sequential_codes(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-002.non_numeric"
        assert issues[0].params == {"filename": _FILENAME, "column": "codigo"}

    def test_first_code_not_one_is_reported(self) -> None:
        frame = make_description_frame(3, codigo=["2", "3", "4"])
        cleaned = pd.Series([2, 3, 4], dtype="int64")
        ctx = _make_context(frame, cleaned={"codigo": cleaned})

        issues = check_sequential_codes(ctx)

        assert [issue.message_key for issue in issues] == [
            "rule.DESC-002.must_start_at_one",
            "rule.DESC-002.must_be_sequential",
        ]

    def test_non_sequential_codes_are_reported(self) -> None:
        frame = make_description_frame(3, codigo=["1", "2", "5"])
        cleaned = pd.Series([1, 2, 5], dtype="int64")
        ctx = _make_context(frame, cleaned={"codigo": cleaned})

        issues = check_sequential_codes(ctx)

        assert [issue.message_key for issue in issues] == ["rule.DESC-002.must_be_sequential"]

    def test_missing_column_reports_an_error(self) -> None:
        frame = make_description_frame().drop(columns=["codigo"])
        ctx = _make_context(frame)

        issues = check_sequential_codes(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "codigo"}


class TestCheckUniqueCodes:
    """DESC-003: `codigo` must contain no duplicates."""

    def test_unique_codes_report_nothing(self) -> None:
        ctx = _make_context(make_description_frame(3))
        assert check_unique_codes(ctx) == []

    def test_a_duplicate_code_is_reported(self) -> None:
        frame = make_description_frame(3, codigo=["1", "2", "2"])
        cleaned = pd.Series([1, 2, 2], dtype="int64")
        ctx = _make_context(frame, cleaned={"codigo": cleaned})

        issues = check_unique_codes(ctx)

        assert len(issues) == 1
        assert issues[0].rule_id == "DESC-003"
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.DESC-003.error"
        assert issues[0].params == {"filename": _FILENAME, "column": "codigo", "duplicated_codes": "[2]"}

    def test_missing_column_reports_an_error(self) -> None:
        frame = make_description_frame().drop(columns=["codigo"])
        ctx = _make_context(frame)

        issues = check_unique_codes(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"


class TestCheckNameCapitalization:
    """DESC-004: `nome_simples`/`nome_completo` follow ABNT capitalisation."""

    def test_correctly_capitalized_names_report_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_name_capitalization(ctx) == []

    def test_a_miscapitalized_name_is_reported_with_expected_and_found(self) -> None:
        frame = make_description_frame(1, nome_simples=["Segurança Alimentar"])
        ctx = _make_context(frame)

        issues = check_name_capitalization(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "DESC-004"
        assert issue.severity is Severity.WARNING
        assert issue.category == NamesEnum.INP.value
        assert issue.message_key == "rule.DESC-004.warning"
        assert issue.params == {
            "filename": _FILENAME,
            "row": 2,
            "column": "nome_simples",
            "expected_text": "Segurança alimentar",
            "original_text": "Segurança Alimentar",
        }

    def test_an_acronym_is_preserved(self) -> None:
        frame = make_description_frame(1, nome_simples=["Índice ABNT"])
        ctx = _make_context(frame)
        assert check_name_capitalization(ctx) == []

    def test_missing_column_reports_a_warning_and_still_checks_the_other_column(self) -> None:
        frame = make_description_frame(1, nome_completo=["Nome Completo Errado"]).drop(columns=["nome_simples"])
        ctx = _make_context(frame)

        issues = check_name_capitalization(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].params == {"filename": _FILENAME, "column": "nome_simples"}
        assert issues[1].message_key == "rule.DESC-004.warning"
        assert issues[1].params["column"] == "nome_completo"


class TestCheckIndicatorLevels:
    """DESC-005: `nivel` must be an integer >= 1 (comma decimals tolerated)."""

    def test_valid_levels_report_nothing(self) -> None:
        ctx = _make_context(make_description_frame(3))
        assert check_indicator_levels(ctx) == []

    def test_a_comma_decimal_integer_is_accepted(self) -> None:
        frame = make_description_frame(1, nivel=["1,0"])
        ctx = _make_context(frame)
        assert check_indicator_levels(ctx) == []

    @pytest.mark.parametrize("bad_value", ["0", "-1", "1.5", "abc", ""])
    def test_an_invalid_level_is_reported(self, bad_value: str) -> None:
        frame = make_description_frame(1)
        frame.loc[0, "nivel"] = bad_value
        ctx = _make_context(frame)

        issues = check_indicator_levels(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "DESC-005"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.DESC-005.error"
        assert issue.params == {"filename": _FILENAME, "row": 2, "column": "nivel"}

    def test_missing_column_reports_an_error(self) -> None:
        frame = make_description_frame().drop(columns=["nivel"])
        ctx = _make_context(frame)

        issues = check_indicator_levels(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"


class TestCheckPunctuation:
    """DESC-006: names must not end with punctuation, descriptions must end with a period."""

    def test_a_valid_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_punctuation(ctx) == []

    def test_a_name_ending_with_punctuation_is_reported(self) -> None:
        frame = make_description_frame(1, nome_simples=["Segurança alimentar."])
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-006.no_punctuation"
        assert issues[0].params == {"filename": _FILENAME, "row": 2, "column": "nome_simples"}

    def test_a_description_not_ending_with_a_period_is_reported(self) -> None:
        frame = make_description_frame(1, desc_simples=["Descrição sem ponto final"])
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-006.must_end_with_dot"
        assert issues[0].params == {"filename": _FILENAME, "row": 2, "column": "desc_simples"}

    def test_missing_columns_are_reported_before_any_violation(self) -> None:
        frame = make_description_frame(1, desc_simples=["Sem ponto"]).drop(columns=["nome_simples"])
        ctx = _make_context(frame)

        issues = check_punctuation(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].params["column"] == "nome_simples"
        assert issues[-1].message_key == "rule.DESC-006.must_end_with_dot"


class TestCheckEmptyStrings:
    """DESC-007: name/description columns must never be empty."""

    def test_a_fully_populated_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_empty_strings(ctx) == []

    def test_an_empty_cell_is_reported(self) -> None:
        frame = make_description_frame(2)
        frame.loc[1, "nome_completo"] = ""
        ctx = _make_context(frame)

        issues = check_empty_strings(ctx)

        assert len(issues) == 1
        assert issues[0].rule_id == "DESC-007"
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.DESC-007.error"
        assert issues[0].params == {"filename": _FILENAME, "row": 3, "column": "nome_completo"}

    def test_a_null_cell_is_reported(self) -> None:
        frame = make_description_frame(2)
        frame.loc[1, "desc_completa"] = None
        ctx = _make_context(frame)

        issues = check_empty_strings(ctx)

        assert len(issues) == 1
        assert issues[0].params["column"] == "desc_completa"

    def test_missing_column_reports_an_error_and_continues(self) -> None:
        frame = make_description_frame(1).drop(columns=["nome_simples"])
        ctx = _make_context(frame)

        issues = check_empty_strings(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].params["column"] == "nome_simples"


class TestCheckNoCrLfCharacters:
    """DESC-008: no CR/LF at the start/end of any expected column, nor anywhere in names."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_no_cr_lf_characters(ctx) == []

    def test_a_trailing_lf_is_reported(self) -> None:
        frame = make_description_frame(1)
        frame.loc[0, "desc_simples"] = "Descrição simples.\n"
        ctx = _make_context(frame)

        issues = check_no_cr_lf_characters(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-008.end"
        assert issues[0].params == {"filename": _FILENAME, "row": 2, "column": "desc_simples", "char_type": "LF"}

    def test_a_leading_cr_is_reported(self) -> None:
        frame = make_description_frame(1)
        frame.loc[0, "desc_simples"] = "\rDescrição simples."
        ctx = _make_context(frame)

        issues = check_no_cr_lf_characters(ctx)

        assert issues[0].message_key == "rule.DESC-008.start"
        assert issues[0].params["char_type"] == "CR"

    def test_a_line_break_inside_a_name_column_reports_its_position(self) -> None:
        frame = make_description_frame(1, nome_simples=["Segurança\nalimentar"])
        ctx = _make_context(frame)

        issues = check_no_cr_lf_characters(ctx)

        assert issues[0].message_key == "rule.DESC-008.anywhere"
        assert issues[0].params == {
            "filename": _FILENAME,
            "row": 2,
            "column": "nome_simples",
            "char_type": "LF",
            "position": 10,
        }

    def test_missing_expected_column_is_reported_as_a_warning(self) -> None:
        frame = make_description_frame(1)
        ctx = _make_context(frame, expected_columns=(*frame.columns, "cenario"))

        issues = check_no_cr_lf_characters(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].severity is Severity.WARNING
        assert issues[0].params["column"] == "cenario"


class TestCheckSimpleDescriptionLength:
    """DESC-009: `desc_simples` must be <= 150 characters."""

    def test_a_short_description_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_simple_description_length(ctx) == []

    def test_a_too_long_description_is_reported(self) -> None:
        long_text = "a" * 151
        frame = make_description_frame(1, desc_simples=[long_text])
        ctx = _make_context(frame)

        issues = check_simple_description_length(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-009.warning"
        assert issues[0].params == {
            "filename": _FILENAME,
            "row": 2,
            "column": "desc_simples",
            "max_length": 150,
            "actual_length": 151,
        }

    def test_exactly_the_limit_reports_nothing(self) -> None:
        frame = make_description_frame(1, desc_simples=["a" * 150])
        ctx = _make_context(frame)
        assert check_simple_description_length(ctx) == []

    def test_missing_column_reports_a_warning(self) -> None:
        frame = make_description_frame().drop(columns=["desc_simples"])
        ctx = _make_context(frame)

        issues = check_simple_description_length(ctx)

        assert issues[0].message_key == "rule.description.missing_required_column"
        assert issues[0].severity is Severity.WARNING


class TestCheckTitleLength:
    """DESC-010: `nome_simples` must be <= 40 characters, unless the CLI flag disables it."""

    def test_a_short_title_reports_nothing(self) -> None:
        ctx = _make_context(make_description_frame(1))
        assert check_title_length(ctx) == []

    def test_a_too_long_title_is_reported(self) -> None:
        long_title = "a" * 41
        frame = make_description_frame(1, nome_simples=[long_title])
        ctx = _make_context(frame)

        issues = check_title_length(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.DESC-010.warning"
        assert issues[0].params == {
            "filename": _FILENAME,
            "row": 2,
            "column": "nome_simples",
            "max_length": 40,
            "actual_length": 41,
        }

    def test_the_flag_suppresses_every_finding(self) -> None:
        long_title = "a" * 41
        frame = make_description_frame(1, nome_simples=[long_title])
        ctx = _make_context(frame, no_warning_titles_length=True)

        assert check_title_length(ctx) == []
