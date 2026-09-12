#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for BaseValidator (BUG-025)."""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.models import SpDescription
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class _ConcreteValidator(BaseValidator):
    """Minimal concrete `BaseValidator` subclass usable only inside this test module."""

    def run(self) -> Tuple[List[str], List[str]]:
        return [], []

    def _prepare_statement(self) -> None:
        pass


def _build_validator(mocker) -> _ConcreteValidator:
    """Instantiate a bare `BaseValidator` with a minimal mocked context.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.

    Returns
    -------
    _ConcreteValidator
        A validator whose `_data_model` resolves to `None` (no model needed
        for `check_columns_in_models_dataframes`, which only reads its two
        explicit arguments).
    """
    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.return_value = None
    data_models_context.context.config.get_verify_names.return_value = {}

    return _ConcreteValidator(
        data_models_context=data_models_context,
        validation_reports=ValidationReport(),
        type_class=SpDescription,
    )


class TestCheckColumnsInModelsDataframes:
    """Regression tests for BUG-025: `KeyError` on an unknown model name."""

    def test_missing_model_key_does_not_raise_key_error(self, mocker):
        """A model name absent from `model_dataframes` must not raise `KeyError`."""
        validator = _build_validator(mocker)

        errors = validator.check_columns_in_models_dataframes(
            required_columns={"missing_model": ["col_a", "col_b"]},
            model_dataframes={},
        )

        assert len(errors) == 2

    def test_missing_model_key_reports_every_required_column_as_missing(self, mocker):
        """Each column of a missing model must produce the standard abort message."""
        validator = _build_validator(mocker)

        errors = validator.check_columns_in_models_dataframes(
            required_columns={"missing_model": ["col_a", "col_b"]},
            model_dataframes={},
        )

        _, expected_col_a = DataFrameProcessing.column_exists(pd.DataFrame(), "missing_model", "col_a")
        _, expected_col_b = DataFrameProcessing.column_exists(pd.DataFrame(), "missing_model", "col_b")
        assert errors == [expected_col_a, expected_col_b]

    def test_present_model_with_all_columns_returns_no_errors(self, mocker):
        """A model whose dataframe has every required column produces no errors."""
        validator = _build_validator(mocker)

        errors = validator.check_columns_in_models_dataframes(
            required_columns={"present_model": ["col_x"]},
            model_dataframes={"present_model": pd.DataFrame({"col_x": [1]})},
        )

        assert errors == []

    def test_mix_of_present_and_missing_models_reports_only_missing_columns(self, mocker):
        """A missing model and a present model with a missing column both report errors."""
        validator = _build_validator(mocker)

        errors = validator.check_columns_in_models_dataframes(
            required_columns={
                "present_model": ["col_x", "col_missing"],
                "absent_model": ["col_a"],
            },
            model_dataframes={"present_model": pd.DataFrame({"col_x": [1]})},
        )

        assert len(errors) == 2
