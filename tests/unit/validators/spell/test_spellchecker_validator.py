#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for SpellCheckerValidator (BUG-027)."""

from __future__ import annotations

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.validators.spell.spellchecker_validator import SpellCheckerValidator


def _build_data_models_context(mocker):
    """Build a mocked `DataModelContext` wired for `SpellCheckerValidator`.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` resolving `SpDictionary` to a minimal
        model and configured to skip the per-column spellcheck pipeline
        (`no_spellchecker=True`), so tests focus only on `_prepare_statement`.
    """
    dictionary_model = mocker.MagicMock()
    dictionary_model.filename = "dicionario.csv"
    dictionary_raw_data = pd.DataFrame({"palavra": []})
    dictionary_model.data_loader_model.raw_data = dictionary_raw_data
    # `BaseValidator`/`validate_spellchecker` read the model's own working frame
    # (`.frame`), not `data_loader_model.raw_data` (BUG-003, see `SpModelABC.frame`).
    dictionary_model.frame = dictionary_raw_data
    dictionary_model.words_to_ignore = []
    dictionary_model.scenarios = []

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.return_value = dictionary_model
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }
    data_models_context.context.data_args.data_file.locale = "pt_BR"
    data_models_context.context.data_args.data_action.no_spellchecker = True

    return data_models_context, dictionary_model


def _patch_spellchecker(mocker, errors_dictionary: list[str]):
    """Patch `SpellChecker` in the validator's module namespace.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to patch the class.
    errors_dictionary : list[str]
        The `errors_dictionary` value the fake `SpellChecker` instance
        should carry (mirrors `DictionaryManager` collected errors).

    Returns
    -------
    unittest.mock.MagicMock
        The mocked `SpellChecker` instance returned by the constructor.
    """
    spellchecker_class = mocker.patch("data_validate.validators.spell.spellchecker_validator.SpellChecker")
    spellchecker_instance = spellchecker_class.return_value
    spellchecker_instance.errors_dictionary = errors_dictionary
    return spellchecker_instance


class TestSpellCheckerValidatorPrepareStatement:
    """Regression tests for BUG-027: `_prepare_statement` was never called."""

    def test_dictionary_errors_are_collected_into_internal_errors(self, mocker):
        """A broken dictionary backend must reach `self._errors`."""
        data_models_context, _ = _build_data_models_context(mocker)
        _patch_spellchecker(mocker, ["Dicionário pt_BR não encontrado"])

        validator = SpellCheckerValidator(
            data_models_context=data_models_context, validation_reports=ValidationReport()
        )

        assert validator._errors == ["Dicionário pt_BR não encontrado"]

    def test_dictionary_errors_reach_the_spelling_report_section(self, mocker):
        """Dictionary initialization errors must be visible under the spelling title."""
        data_models_context, _ = _build_data_models_context(mocker)
        _patch_spellchecker(mocker, ["Dicionário pt_BR não encontrado"])
        validation_reports = ValidationReport()

        validator = SpellCheckerValidator(
            data_models_context=data_models_context, validation_reports=validation_reports
        )

        spelling_title = validator.TITLES_INFO[NamesEnum.SPELL.value]
        assert spelling_title in validation_reports.reports
        assert validation_reports.reports[spelling_title].errors == ["Dicionário pt_BR não encontrado"]

    def test_no_dictionary_errors_means_nothing_is_added(self, mocker):
        """An empty `errors_dictionary` must not add anything to errors or the report."""
        data_models_context, _ = _build_data_models_context(mocker)
        _patch_spellchecker(mocker, [])
        validation_reports = ValidationReport()

        validator = SpellCheckerValidator(
            data_models_context=data_models_context, validation_reports=validation_reports
        )

        assert validator._errors == []
        assert validation_reports.reports == {}
