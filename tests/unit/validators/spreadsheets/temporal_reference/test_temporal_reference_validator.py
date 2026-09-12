#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for SpTemporalReferenceValidator (BUG-007)."""

from __future__ import annotations

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.models import SpTemporalReference
from data_validate.validators.spreadsheets.temporal_reference.temporal_reference_validator import (
    SpTemporalReferenceValidator,
)


def _build_data_models_context(mocker, *, symbols: list, current_year: int = 2026):
    """Build a mocked DataModelContext wired with a minimal temporal reference model.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    symbols : list
        Raw values for the `simbolo` column, first entry is the current-year
        row excluded by `validate_reference_years`.
    current_year : int
        Value returned by `context.config.CURRENT_YEAR`.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` whose `get_instance_of` resolves
        `SpTemporalReference` to a minimal mock carrying the raw dataframe
        `SpTemporalReferenceValidator` needs.
    """
    temporal_reference_model = mocker.MagicMock()
    temporal_reference_model.filename = "referencia_temporal.csv"
    temporal_reference_raw_data = pd.DataFrame(
        {
            "nome": [f"ano_{i}" for i in range(len(symbols))],
            "descricao": [f"Descrição {i}." for i in range(len(symbols))],
            "simbolo": symbols,
        }
    )
    temporal_reference_model.data_loader_model.raw_data = temporal_reference_raw_data
    # `BaseValidator` reads the model's own working frame (`.frame`), not
    # `data_loader_model.raw_data`, since BUG-003 (see `SpModelABC.frame`).
    temporal_reference_model.frame = temporal_reference_raw_data

    models_by_class = {SpTemporalReference: temporal_reference_model}

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.side_effect = lambda model_class: models_by_class[model_class]
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }
    data_models_context.context.config.CURRENT_YEAR = current_year

    return data_models_context


def _build_validator(mocker, *, symbols: list, current_year: int = 2026) -> SpTemporalReferenceValidator:
    """Instantiate a `SpTemporalReferenceValidator` wired with a minimal mocked context.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    symbols : list
        Raw values for the `simbolo` column.
    current_year : int
        Value returned by `context.config.CURRENT_YEAR`.

    Returns
    -------
    SpTemporalReferenceValidator
        A validator instance that already ran its validation pipeline once
        (construction triggers `run()`, per ARC-001).
    """
    data_models_context = _build_data_models_context(mocker, symbols=symbols, current_year=current_year)
    return SpTemporalReferenceValidator(data_models_context=data_models_context, validation_reports=ValidationReport())


class TestSpTemporalReferenceValidator:
    """Regression tests for BUG-007: `int(year)` crashing on a non-numeric symbol."""

    def test_validate_reference_years_skips_non_numeric_symbol_without_raising(self, mocker):
        """A symbol column containing a non-numeric value (e.g. `"2030a"`) must not
        raise; the rule must silently skip it while still flagging genuinely past
        numeric years."""
        validator = _build_validator(mocker, symbols=["2000", "2030a", "2020", "2030"], current_year=2026)

        errors, warnings = validator.validate_reference_years()

        assert warnings == []
        assert not any("Exception validation" in error for error in errors)
        assert not any("2030a" in error for error in errors)
        assert any("2020" in error for error in errors)
        assert not any("2030 " in error or error.endswith("2030") for error in errors)

    def test_validate_reference_years_two_validators_are_independent(self, mocker):
        """Two validators built from different frames in the same process must
        produce independent results (guards against reading shared class state)."""
        past_year_validator = _build_validator(mocker, symbols=["2000", "2020"], current_year=2026)
        future_year_validator = _build_validator(mocker, symbols=["2000", "2030"], current_year=2026)

        past_year_errors, __ = past_year_validator.validate_reference_years()
        future_year_errors, __ = future_year_validator.validate_reference_years()

        assert past_year_errors != []
        assert future_year_errors == []
