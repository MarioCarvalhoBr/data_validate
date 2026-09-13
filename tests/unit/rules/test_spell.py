#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.spell` (Phase 3 Port 8, SPELL-001…005).

Table-driven coverage per rule (happy path, missing-column abort, `--no-spellchecker` skip,
processing failure, the legacy sort-by-rendered-text order, and the engine-level empty-sheet
skip) built directly against the pure `check_*` functions and a hand-built `RuleContext` — no
engine except where the engine-level `SKIPPED`/empty-sheet behaviour itself is under test
(`.claude/rules/testing.md`). The `SpellChecker` backend is never constructed for real (no
`enchant`/hunspell dependency in these tests): `FakeSpellBackend` is a plain test double
implementing `check_spelling_text_structured`'s contract, matching
`tests/unit/helpers/tools/spellchecker/test_spellchecker_controller.py::CountingFakeDict`'s
precedent (`pytest`/`pytest-mock` only, never `unittest.mock`).

Migrates the BUG-027 regression tests from
`tests/unit/validators/spell/test_spellchecker_validator.py` (deleted): a broken dictionary
backend must still surface as `SPELL-001`, entirely independent of `--no-spellchecker`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.tools.spellchecker.spellchecker import SpellingFinding
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.spell import (
    SPELL_REGISTRY,
    SpellBackend,
    check_dictionary_backend,
    check_spelling_description,
    check_spelling_scenario,
    check_spelling_temporal_reference,
)
from data_validate.specs.issues import Severity
from tests.factories import make_description_frame, make_scenario_frame, make_temporal_frame

_DESCRIPTION_FILENAME = "descricao.xlsx"
_TEMPORAL_FILENAME = "referencia_temporal.xlsx"
_SCENARIO_FILENAME = "cenarios.xlsx"


class FakeSpellBackend:
    """Test double for `SpellChecker`'s structured surface, no `enchant` dependency.

    Args:
        findings: `(row_index, column, kind, words)` tuples returned by
            `check_spelling_text_structured`, translated into `SpellingFinding`s.
        error: When set, `check_spelling_text_structured` returns this as its error instead of
            any findings (mirrors `SpellChecker.check_spelling_text_structured`'s own contract).
        errors_dictionary: Pre-collected dictionary/backend initialisation error strings
            (`SPELL-001`).
    """

    def __init__(
        self,
        findings: list[tuple[int, str, str, list[str] | None]] | None = None,
        error: str | None = None,
        errors_dictionary: list[str] | None = None,
    ) -> None:
        self._findings = findings or []
        self._error = error
        self.errors_dictionary = errors_dictionary or []
        self.calls: list[tuple[str, ...]] = []

    def check_spelling_text_structured(
        self, df: pd.DataFrame, columns_sheets: list[str]
    ) -> tuple[tuple[SpellingFinding, ...], str | None]:
        self.calls.append(tuple(columns_sheets))
        if self._error is not None:
            return (), self._error
        return (
            tuple(
                SpellingFinding(row_index=row, column=column, kind=kind, words=tuple(words or ()))
                for row, column, kind, words in self._findings
            ),
            None,
        )

    def clean_files_generated(self) -> None:
        """No-op: this fake holds no temporary resources (ARC-015's `SpellBackend` Protocol)."""


def _make_context(
    sheets: dict[str, pd.DataFrame],
    *,
    backend: FakeSpellBackend | None = None,
    no_spellchecker: bool = False,
    scenarios: list[str] | None = None,
) -> RuleContext:
    """Build a `RuleContext` for one or more spell-checked sheets."""
    filenames = {
        "descricao": _DESCRIPTION_FILENAME,
        "referencia_temporal": _TEMPORAL_FILENAME,
        "cenarios": _SCENARIO_FILENAME,
    }
    return RuleContext(
        sheets=sheets,
        cleaned={},
        options={
            "filenames": filenames,
            "spell_backend": backend,
            "no_spellchecker": no_spellchecker,
            "scenarios": scenarios or [],
        },
        translate=lambda key, **params: _render(key, params),
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


def _render(key: str, params: dict[str, object]) -> str:
    """A tiny stand-in catalog: renders enough of the real templates to prove sort order.

    Only the two keys whose rendered text order actually matters for these tests
    (`rule.SPELL-003.warning`/`rule.SPELL-004.warning`) get a realistic template; every other
    key renders as itself (sufficient for equality assertions on `message_key`/`params`).
    """
    templates = {
        "rule.SPELL-003.warning": "{filename}, linha {row}: Há dois ou mais espaços seguidos na coluna {column}.",
        "rule.SPELL-004.warning": "{filename}, linha {row}: Palavras com possíveis erros ortográficos na coluna {column}: {words}.",
    }
    template = templates.get(key, key)
    return template.format(**params)


class TestSpellRegistryShape:
    """The registry declares exactly the SPELL ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_spell_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in SPELL_REGISTRY] == ["SPELL-001", "SPELL-002", "SPELL-003", "SPELL-004"]

    def test_every_spec_declares_the_spell_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in SPELL_REGISTRY}
        assert categories == dict.fromkeys(categories, NamesEnum.SPELL.value)

    def test_empty_sheets_skip_every_model_rule_silently(self) -> None:
        ctx = _make_context(
            {"descricao": pd.DataFrame(), "referencia_temporal": pd.DataFrame(), "cenarios": pd.DataFrame()},
            backend=FakeSpellBackend(),
            scenarios=["O"],
        )
        result = Engine(SPELL_REGISTRY).run(ctx)
        statuses = {outcome.rule_id: outcome.status for outcome in result.outcomes}
        assert statuses["SPELL-002"] is RuleStatus.SKIPPED
        assert statuses["SPELL-003"] is RuleStatus.SKIPPED
        assert statuses["SPELL-004"] is RuleStatus.SKIPPED


class TestCheckDictionaryBackend:
    """SPELL-001: the language dictionary/backend must initialise without error (BUG-027)."""

    def test_no_errors_means_no_issues(self) -> None:
        ctx = _make_context({}, backend=FakeSpellBackend())
        assert check_dictionary_backend(ctx) == []

    def test_a_missing_dictionary_is_reported_as_an_error(self) -> None:
        backend = FakeSpellBackend(errors_dictionary=["Dicionário pt_BR não encontrado"])
        ctx = _make_context({}, backend=backend)

        issues = check_dictionary_backend(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "SPELL-001"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.SPELL.value
        assert issue.message_key == "rule.SPELL-001.backend_error"
        assert issue.params == {"message": "Dicionário pt_BR não encontrado"}

    def test_every_error_string_becomes_its_own_issue_in_order(self) -> None:
        backend = FakeSpellBackend(errors_dictionary=["primeiro erro", "segundo erro"])
        ctx = _make_context({}, backend=backend)

        issues = check_dictionary_backend(ctx)

        assert [issue.params["message"] for issue in issues] == ["primeiro erro", "segundo erro"]

    def test_runs_even_when_no_spellchecker_is_set(self) -> None:
        """BUG-027: dictionary errors surface regardless of `--no-spellchecker`."""
        backend = FakeSpellBackend(errors_dictionary=["erro de dicionário"])
        ctx = _make_context({}, backend=backend, no_spellchecker=True)

        issues = check_dictionary_backend(ctx)

        assert len(issues) == 1

    def test_no_backend_configured_reports_nothing(self) -> None:
        ctx = _make_context({}, backend=None)
        assert check_dictionary_backend(ctx) == []


class TestCheckSpellingDescription:
    """SPELL-002…005 (description): missing column / no-spellchecker / quality findings."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        frame = make_description_frame(n_indicators=2)
        ctx = _make_context({"descricao": frame}, backend=FakeSpellBackend())

        assert check_spelling_description(ctx) == []

    def test_missing_columns_are_reported_as_warnings_in_order(self) -> None:
        frame = make_description_frame(n_indicators=1).drop(columns=["nome_simples", "desc_completa"])
        ctx = _make_context({"descricao": frame}, backend=FakeSpellBackend())

        issues = check_spelling_description(ctx)

        assert [issue.params["column"] for issue in issues] == ["nome_simples", "desc_completa"]
        for issue in issues:
            assert issue.rule_id == "SPELL-002"
            assert issue.severity is Severity.WARNING
            assert issue.message_key == "rule.spelling.missing_required_column"
            assert issue.params["filename"] == _DESCRIPTION_FILENAME

    def test_no_spellchecker_skips_everything_including_missing_columns(self) -> None:
        frame = make_description_frame(n_indicators=1).drop(columns=["nome_simples"])
        ctx = _make_context({"descricao": frame}, backend=FakeSpellBackend(), no_spellchecker=True)

        assert check_spelling_description(ctx) == []

    def test_quality_findings_are_rendered_as_spell_003_and_spell_004(self) -> None:
        frame = make_description_frame(n_indicators=1)
        backend = FakeSpellBackend(
            findings=[
                (0, "nome_simples", "multiple_spaces", None),
                (0, "desc_simples", "misspelled_words", ["Wrld"]),
            ]
        )
        ctx = _make_context({"descricao": frame}, backend=backend)

        issues = check_spelling_description(ctx)

        assert {issue.rule_id for issue in issues} == {"SPELL-003", "SPELL-004"}
        space_issue = next(issue for issue in issues if issue.rule_id == "SPELL-003")
        assert space_issue.severity is Severity.WARNING
        assert space_issue.message_key == "rule.SPELL-003.warning"
        assert space_issue.params == {"filename": _DESCRIPTION_FILENAME, "row": 2, "column": "nome_simples"}

        word_issue = next(issue for issue in issues if issue.rule_id == "SPELL-004")
        assert word_issue.message_key == "rule.SPELL-004.warning"
        assert word_issue.params == {
            "filename": _DESCRIPTION_FILENAME,
            "row": 2,
            "column": "desc_simples",
            "words": "['Wrld']",
        }

    def test_findings_are_sorted_by_rendered_text_not_insertion_order(self) -> None:
        """Reproduces the legacy `sorted(warnings_spellchecker)` lexicographic reordering."""
        frame = make_description_frame(n_indicators=1)
        backend = FakeSpellBackend(
            findings=[
                (10, "nome_simples", "multiple_spaces", None),
                (2, "nome_simples", "multiple_spaces", None),
            ]
        )
        ctx = _make_context({"descricao": frame}, backend=backend)

        issues = check_spelling_description(ctx)

        # "linha 10" < "linha 12" lexicographically (row 10 -> excel row 12, row 2 -> excel row 4).
        assert [issue.row for issue in issues] == [10, 2]

    def test_a_processing_failure_is_reported_as_spell_005_with_no_other_issues(self) -> None:
        frame = make_description_frame(n_indicators=1)
        backend = FakeSpellBackend(error="AttributeError: 'NoneType' object has no attribute 'check'")
        ctx = _make_context({"descricao": frame}, backend=backend)

        issues = check_spelling_description(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "SPELL-005"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.SPELL-005.error"
        assert issue.params == {
            "filename": _DESCRIPTION_FILENAME,
            "message": "AttributeError: 'NoneType' object has no attribute 'check'",
        }

    def test_missing_column_issues_still_precede_a_processing_failure(self) -> None:
        frame = make_description_frame(n_indicators=1).drop(columns=["nome_simples"])
        backend = FakeSpellBackend(error="boom")
        ctx = _make_context({"descricao": frame}, backend=backend)

        issues = check_spelling_description(ctx)

        assert [issue.rule_id for issue in issues] == ["SPELL-002", "SPELL-005"]

    def test_no_backend_configured_still_reports_missing_columns(self) -> None:
        frame = make_description_frame(n_indicators=1).drop(columns=["nome_simples"])
        ctx = _make_context({"descricao": frame}, backend=None)

        issues = check_spelling_description(ctx)

        assert [issue.rule_id for issue in issues] == ["SPELL-002"]


class TestCheckSpellingTemporalReference:
    """SPELL-002…005 (referencia_temporal): spell-checks `descricao` only."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        frame = make_temporal_frame(years=[2020])
        ctx = _make_context({"referencia_temporal": frame}, backend=FakeSpellBackend())

        assert check_spelling_temporal_reference(ctx) == []

    def test_missing_column_is_reported(self) -> None:
        frame = make_temporal_frame().drop(columns=["descricao"])
        ctx = _make_context({"referencia_temporal": frame}, backend=FakeSpellBackend())

        issues = check_spelling_temporal_reference(ctx)

        assert len(issues) == 1
        assert issues[0].rule_id == "SPELL-002"
        assert issues[0].params == {"filename": _TEMPORAL_FILENAME, "column": "descricao"}

    def test_backend_is_called_with_only_the_temporal_reference_column(self) -> None:
        frame = make_temporal_frame(years=[2020])
        backend = FakeSpellBackend()
        ctx = _make_context({"referencia_temporal": frame}, backend=backend)

        check_spelling_temporal_reference(ctx)

        assert backend.calls == [("descricao",)]


class TestCheckSpellingScenario:
    """SPELL-002…005 (cenarios): only runs when scenarios exist."""

    def test_a_clean_sheet_reports_nothing(self) -> None:
        frame = make_scenario_frame(symbols=["O", "P"])
        ctx = _make_context({"cenarios": frame}, backend=FakeSpellBackend(), scenarios=["O", "P"])

        assert check_spelling_scenario(ctx) == []

    def test_no_scenarios_skips_entirely_even_with_data_present(self) -> None:
        frame = make_scenario_frame(symbols=["O"])
        ctx = _make_context({"cenarios": frame}, backend=FakeSpellBackend(), scenarios=[])

        assert check_spelling_scenario(ctx) == []

    def test_missing_columns_are_reported_when_scenarios_exist(self) -> None:
        frame = make_scenario_frame(symbols=["O"]).drop(columns=["nome", "descricao"])
        ctx = _make_context({"cenarios": frame}, backend=FakeSpellBackend(), scenarios=["O"])

        issues = check_spelling_scenario(ctx)

        assert [issue.params["column"] for issue in issues] == ["nome", "descricao"]

    def test_no_spellchecker_skips_even_with_a_missing_column_and_scenarios_present(self) -> None:
        frame = make_scenario_frame(symbols=["O"]).drop(columns=["nome"])
        ctx = _make_context({"cenarios": frame}, backend=FakeSpellBackend(), scenarios=["O"], no_spellchecker=True)

        assert check_spelling_scenario(ctx) == []

    def test_a_missing_column_is_still_reported_when_spellchecker_is_enabled(self) -> None:
        frame = make_scenario_frame(symbols=["O"]).drop(columns=["nome"])
        ctx = _make_context({"cenarios": frame}, backend=FakeSpellBackend(), scenarios=["O"], no_spellchecker=False)

        issues = check_spelling_scenario(ctx)

        assert len(issues) == 1
        assert issues[0].params["column"] == "nome"


class TestSpellBackendProtocol:
    """ARC-015: `SpellBackend` is a structural, `pyenchant`-independent Protocol."""

    def test_fake_spell_backend_satisfies_the_protocol(self) -> None:
        assert isinstance(FakeSpellBackend(), SpellBackend)

    def test_real_spell_checker_satisfies_the_protocol(self, mocker) -> None:
        """The concrete `SpellChecker` (the only production `SpellBackend` today) satisfies
        the Protocol structurally, with its heavy `pyenchant`/`DictionaryManager` collaborators
        mocked out — proving the Protocol names exactly the surface `rules/spell.py` and
        `SpreadsheetProcessor` actually use, not an implementation detail of one backend."""
        from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker

        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DictionaryManager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.SpellCheckerController",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "data_validate.helpers.tools.spellchecker.spellchecker.DataFrameProcessor",
            return_value=mocker.MagicMock(),
        )

        spell_checker = SpellChecker("pt_BR", [])

        assert isinstance(spell_checker, SpellBackend)

    def test_an_object_missing_clean_files_generated_does_not_satisfy_the_protocol(self) -> None:
        class _Incomplete:
            def __init__(self) -> None:
                self.errors_dictionary: list[str] = []

            def check_spelling_text_structured(self, df, columns_sheets):
                return (), None

        assert not isinstance(_Incomplete(), SpellBackend)
