#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for SpValueValidator (BUG-001)."""

from __future__ import annotations

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.models import SpDescription, SpScenario, SpTemporalReference, SpValue
from data_validate.validators.spreadsheets.value.value_validator import SpValueValidator


def _build_data_models_context(mocker):
    """Build a mocked DataModelContext wired with minimal per-model mocks.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` whose `get_instance_of` resolves each
        `Sp*` model class to a minimal mock carrying the raw dataframes
        `SpValueValidator` needs.
    """
    # `BaseValidator` and `SpValueValidator._prepare_statement` read each model's own
    # working frame (`.frame`), not `data_loader_model.raw_data` (BUG-003, see
    # `SpModelABC.frame`); mirror the same dataframe onto both attributes.
    value_model = mocker.MagicMock()
    value_model.filename = "valores.csv"
    value_raw_data = pd.DataFrame({"id": [1], "1-2020": [10.5]})
    value_model.data_loader_model.raw_data = value_raw_data
    value_model.frame = value_raw_data
    value_model.scenario_exists_file = True
    value_model.scenarios = ["O"]

    description_model = mocker.MagicMock()
    description_model.filename = "descricao.csv"
    description_raw_data = pd.DataFrame({"codigo": [1], "nivel": [2], "cenario": [0]})
    description_model.data_loader_model.raw_data = description_raw_data
    description_model.frame = description_raw_data

    temporal_reference_model = mocker.MagicMock()
    temporal_reference_model.filename = "referencia_temporal.csv"
    temporal_reference_raw_data = pd.DataFrame({"simbolo": [2020]})
    temporal_reference_model.data_loader_model.raw_data = temporal_reference_raw_data
    temporal_reference_model.frame = temporal_reference_raw_data

    scenario_model = mocker.MagicMock()
    scenario_model.filename = "cenarios.csv"
    scenario_raw_data = pd.DataFrame({"simbolo": ["O"]})
    scenario_model.data_loader_model.raw_data = scenario_raw_data
    scenario_model.frame = scenario_raw_data

    models_by_class = {
        SpValue: value_model,
        SpDescription: description_model,
        SpTemporalReference: temporal_reference_model,
        SpScenario: scenario_model,
    }

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.side_effect = lambda model_class: models_by_class[model_class]
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }

    return data_models_context


def _build_validator(mocker) -> SpValueValidator:
    """Instantiate a `SpValueValidator` wired with the minimal mocked context.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.

    Returns
    -------
    SpValueValidator
        A validator instance that already ran its validation pipeline once
        (construction triggers `run()`, per ARC-001).
    """
    data_models_context = _build_data_models_context(mocker)
    return SpValueValidator(data_models_context=data_models_context, validation_reports=ValidationReport())


class TestSpValueValidator:
    """Regression tests for BUG-001: shared list mutation in value combination validation."""

    def test_validate_value_combination_relation_does_not_mutate_shared_required_columns(self, mocker):
        """Repeated calls must not grow `global_required_columns[sp_name_description]`."""
        validator = _build_validator(mocker)
        description_key = validator.sp_name_description
        before = list(validator.global_required_columns[description_key])

        validator.validate_value_combination_relation()
        validator.validate_value_combination_relation()

        after = validator.global_required_columns[description_key]
        assert after == before
        assert after.count("cenario") <= 1

    def test_validate_value_combination_relation_is_idempotent(self, mocker):
        """Two consecutive calls must return the same errors/warnings."""
        validator = _build_validator(mocker)

        first_result = validator.validate_value_combination_relation()
        second_result = validator.validate_value_combination_relation()

        assert first_result == second_result
