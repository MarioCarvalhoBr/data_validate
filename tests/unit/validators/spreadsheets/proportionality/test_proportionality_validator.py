#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for SpProportionalityValidator (BUG-006)."""

from __future__ import annotations

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.models import SpComposition, SpDescription, SpProportionality, SpValue
from data_validate.validators.spreadsheets.proportionality.proportionality_validator import (
    SpProportionalityValidator,
)


def _proportionality_raw_data(id_level_two_name: str = "id") -> pd.DataFrame:
    """Build a minimal double-header proportionality raw dataframe.

    Args
    ----
    id_level_two_name : str
        Name to use for the level-2 header of the id column. Defaults to
        ``"id"``; pass a different value to simulate the id column being
        absent from level 2.

    Returns
    -------
    pd.DataFrame
        A dataframe with a `MultiIndex` column structure matching the real
        `proporcionalidades` sheet: level 0 is the parent code (or
        `Unnamed: 0_level_0` for the id column), level 1 is the child code
        (or the id column name).
    """
    columns = pd.MultiIndex.from_tuples(
        [
            ("Unnamed: 0_level_0", id_level_two_name),
            ("5008-2010", "5021-2010"),
        ]
    )
    return pd.DataFrame([[1100015, 0.5]], columns=columns)


def _value_raw_data(include_id_column: bool = True) -> pd.DataFrame:
    """Build a minimal value raw dataframe.

    Args
    ----
    include_id_column : bool
        Whether to include the `id` column. Defaults to `True`; pass
        `False` to simulate the id column being absent.

    Returns
    -------
    pd.DataFrame
        A single-header dataframe mirroring the real `valores` sheet.
    """
    data = {"5021-2010": [0.5]}
    if include_id_column:
        data = {"id": [1100015], **data}
    return pd.DataFrame(data)


def _build_data_models_context(
    mocker,
    *,
    proportionality_raw_data: pd.DataFrame | None = None,
    value_raw_data: pd.DataFrame | None = None,
):
    """Build a mocked DataModelContext wired with minimal per-model mocks.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    proportionality_raw_data : pd.DataFrame, optional
        Raw dataframe returned for the `SpProportionality` model. Defaults
        to a valid double-header frame with an `id` column at level 2.
    value_raw_data : pd.DataFrame, optional
        Raw dataframe returned for the `SpValue` model. Defaults to a valid
        frame with an `id` column.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` whose `get_instance_of` resolves each
        `Sp*` model class to a minimal mock carrying the raw dataframes
        `SpProportionalityValidator` needs.
    """
    # `BaseValidator` and `SpProportionalityValidator._prepare_statement` read each model's
    # own working frame (`.frame`), not `data_loader_model.raw_data` (BUG-003, see
    # `SpModelABC.frame`); mirror the same dataframe onto both attributes.
    proportionality_model = mocker.MagicMock()
    proportionality_model.filename = "proporcionalidades.csv"
    proportionality_frame = (
        proportionality_raw_data if proportionality_raw_data is not None else _proportionality_raw_data()
    )
    proportionality_model.data_loader_model.raw_data = proportionality_frame
    proportionality_model.frame = proportionality_frame

    description_model = mocker.MagicMock()
    description_model.filename = "descricao.csv"
    description_frame = pd.DataFrame({"codigo": [5008, 5021], "nivel": [1, 2]})
    description_model.data_loader_model.raw_data = description_frame
    description_model.frame = description_frame

    value_model = mocker.MagicMock()
    value_model.filename = "valores.csv"
    value_frame = value_raw_data if value_raw_data is not None else _value_raw_data()
    value_model.data_loader_model.raw_data = value_frame
    value_model.frame = value_frame
    value_model.scenario_exists_file = False
    value_model.scenarios = []

    composition_model = mocker.MagicMock()
    composition_model.filename = "composicao.csv"
    composition_frame = pd.DataFrame({"codigo_pai": [5008], "codigo_filho": [5021]})
    composition_model.data_loader_model.raw_data = composition_frame
    composition_model.frame = composition_frame

    models_by_class = {
        SpProportionality: proportionality_model,
        SpDescription: description_model,
        SpValue: value_model,
        SpComposition: composition_model,
    }

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.side_effect = lambda model_class: models_by_class[model_class]
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }

    return data_models_context


def _build_validator(
    mocker,
    *,
    proportionality_raw_data: pd.DataFrame | None = None,
    value_raw_data: pd.DataFrame | None = None,
) -> SpProportionalityValidator:
    """Instantiate a `SpProportionalityValidator` wired with a minimal mocked context.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    proportionality_raw_data : pd.DataFrame, optional
        Raw dataframe passed through to `_build_data_models_context`.
    value_raw_data : pd.DataFrame, optional
        Raw dataframe passed through to `_build_data_models_context`.

    Returns
    -------
    SpProportionalityValidator
        A validator instance that already ran its validation pipeline once
        (construction triggers `run()`, per ARC-001).
    """
    data_models_context = _build_data_models_context(
        mocker,
        proportionality_raw_data=proportionality_raw_data,
        value_raw_data=value_raw_data,
    )
    return SpProportionalityValidator(data_models_context=data_models_context, validation_reports=ValidationReport())


class TestSpProportionalityValidator:
    """Regression tests for BUG-006: `list.remove("id")` crashing when `id` is absent."""

    def test_validate_relation_indicators_reports_missing_id_in_proportionality_level_two(self, mocker):
        """A proportionality sheet without `id` at level 2 must not raise; the
        missing-column guard reports it instead."""
        validator = _build_validator(
            mocker,
            proportionality_raw_data=_proportionality_raw_data(id_level_two_name="territorio"),
        )

        errors, warnings = validator.validate_relation_indicators_in_value_and_proportionality()

        assert isinstance(errors, list)
        assert isinstance(warnings, list)
        assert any("id" in error for error in errors)

    def test_validate_relation_indicators_reports_missing_id_in_values(self, mocker):
        """A value sheet without an `id` column must not raise; the
        missing-column guard reports it instead."""
        validator = _build_validator(mocker, value_raw_data=_value_raw_data(include_id_column=False))

        errors, warnings = validator.validate_relation_indicators_in_value_and_proportionality()

        assert isinstance(errors, list)
        assert isinstance(warnings, list)
        assert any("id" in error for error in errors)

    def test_validate_relation_indicators_does_not_raise_when_id_missing_past_the_column_guard(self, mocker):
        """Drive `validate_relation_indicators_in_value_and_proportionality` past its
        own column-existence guard with frames that lack `id`, to exercise the
        `list.remove` call sites directly (BUG-006). Before the fix, this raised
        `ValueError: list.remove(x): x not in list`; after the fix it must return a
        plain issue list instead."""
        validator = _build_validator(mocker)
        mocker.patch.object(validator, "check_columns_in_models_dataframes", return_value=[])

        validator.model_dataframes[validator.sp_name_proportionality] = _proportionality_raw_data(
            id_level_two_name="territorio"
        )
        validator.model_dataframes[validator.sp_name_value] = _value_raw_data(include_id_column=False)

        errors, warnings = validator.validate_relation_indicators_in_value_and_proportionality()

        assert isinstance(errors, list)
        assert isinstance(warnings, list)
