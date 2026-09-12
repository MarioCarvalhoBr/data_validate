#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for SpLegendValidator (BUG-014)."""

from __future__ import annotations

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.models import SpDescription, SpLegend, SpValue
from data_validate.validators.spreadsheets.legend.legend_validator import SpLegendValidator


def _build_data_models_context(
    mocker,
    *,
    description_frame: pd.DataFrame,
    legend_frame: pd.DataFrame | None = None,
    value_frame: pd.DataFrame | None = None,
):
    """Build a mocked DataModelContext wired with minimal per-model mocks.

    Args
    ----
    mocker : pytest_mock.MockerFixture
        The pytest-mock fixture used to build MagicMock instances.
    description_frame : pd.DataFrame
        Working frame (`SpDescription.frame`) for the description model.
    legend_frame : pd.DataFrame, optional
        Working frame (`SpLegend.frame`) for the legend model. Defaults to an
        empty codes-only frame.
    value_frame : pd.DataFrame, optional
        Working frame (`SpValue.frame`) for the value model. Defaults to an
        empty frame.

    Returns
    -------
    unittest.mock.MagicMock
        A mocked `DataModelContext` whose `get_instance_of` resolves each
        `Sp*` model class to a minimal mock carrying the working dataframes
        `SpLegendValidator` needs.
    """
    legend_model = mocker.MagicMock()
    legend_model.filename = "legenda.csv"
    legend_model.frame = legend_frame if legend_frame is not None else pd.DataFrame({"codigo": []})
    legend_model.is_sanity_check_passed = True
    legend_model.legend_read_success = True
    legend_model.CONSTANTS.MIN_LOWER_LEGEND_DEFAULT = 0
    legend_model.CONSTANTS.MAX_UPPER_LEGEND_DEFAULT = 1

    description_model = mocker.MagicMock()
    description_model.filename = "descricao.csv"
    description_model.frame = description_frame

    value_model = mocker.MagicMock()
    value_model.filename = "valores.csv"
    value_model.frame = value_frame if value_frame is not None else pd.DataFrame()
    value_model.scenario_exists_file = False
    value_model.scenarios = []

    models_by_class = {
        SpLegend: legend_model,
        SpDescription: description_model,
        SpValue: value_model,
    }

    data_models_context = mocker.MagicMock()
    data_models_context.get_instance_of.side_effect = lambda model_class: models_by_class[model_class]
    data_models_context.context.config.get_verify_names.return_value = {
        member.value: member.value for member in NamesEnum
    }
    data_models_context.context.config.LABEL_DATA_UNAVAILABLE = "Dado indisponível"
    data_models_context.context.config.VALUE_DATA_UNAVAILABLE = "DI"

    return data_models_context


def _build_validator(
    mocker,
    *,
    description_frame: pd.DataFrame,
    legend_frame: pd.DataFrame | None = None,
    value_frame: pd.DataFrame | None = None,
) -> SpLegendValidator:
    """Instantiate a `SpLegendValidator` wired with a minimal mocked context.

    Returns
    -------
    SpLegendValidator
        A validator instance that already ran its validation pipeline once
        (construction triggers `run()`, per ARC-001).
    """
    data_models_context = _build_data_models_context(
        mocker,
        description_frame=description_frame,
        legend_frame=legend_frame,
        value_frame=value_frame,
    )
    return SpLegendValidator(data_models_context=data_models_context, validation_reports=ValidationReport())


class TestSpLegendValidatorBug014LevelComparison:
    """Regression tests for BUG-014: level comparisons relying on exact string "1"/"2"."""

    def test_validate_relation_indicators_in_legend_catches_level_one_with_float_formatted_level(self, mocker):
        """A level 1 indicator stored as `nivel = "1.0"` with an (illegal) legend
        reference must still be reported.

        Before the fix, `df_description_clean[COLUMN_LEVEL] == "1"` never matches
        `"1.0"`, so the level-1-must-not-reference-a-legend rule silently skips
        indicator 10 instead of reporting it.
        """
        description_frame = pd.DataFrame({"codigo": [10], "nivel": ["1.0"], "legenda": [5]})
        legend_frame = pd.DataFrame({"codigo": [5]})

        validator = _build_validator(mocker, description_frame=description_frame, legend_frame=legend_frame)

        errors, __ = validator.validate_relation_indicators_in_legend()

        assert any("nível 1 não podem ter referência de legenda" in error for error in errors)

    def test_validate_relation_indicators_in_legend_does_not_require_legend_for_float_formatted_level_two(self, mocker):
        """A level 2 indicator stored as `nivel = "2.0"` without a legend reference
        must not be reported as missing one.

        Before the fix, the compound mask `(level != "1") & (level != "2")` (used
        to find indicators that must carry a legend reference) never matches
        `"2.0"` against `"2"`, so a level 2 indicator is wrongly treated as
        "some other level" and flagged for lacking a legend it is not required to
        have.
        """
        description_frame = pd.DataFrame({"codigo": [20], "nivel": ["2.0"], "legenda": [pd.NA]})
        legend_frame = pd.DataFrame({"codigo": []})

        validator = _build_validator(mocker, description_frame=description_frame, legend_frame=legend_frame)

        errors, __ = validator.validate_relation_indicators_in_legend()

        assert not any("devem ter referência de legenda" in error for error in errors)

    def test_validate_range_multiple_legend_skips_level_one_with_float_formatted_level(self, mocker):
        """A level 1 indicator stored as `nivel = "1.0"` must be excluded from
        legend-range validation, even when its value falls outside the default
        `[0, 1]` range.

        Before the fix, `df_description_clean[COLUMN_LEVEL] == "1"` never matches
        `"1.0"`, so indicator 10 is not recognized as level 1 and its
        out-of-range value is wrongly flagged.
        """
        description_frame = pd.DataFrame({"codigo": [10], "nivel": ["1.0"], "legenda": [pd.NA]})
        value_frame = pd.DataFrame({"10-2020": [5.0]})

        validator = _build_validator(
            mocker,
            description_frame=description_frame,
            legend_frame=pd.DataFrame({"codigo": []}),
            value_frame=value_frame,
        )

        errors, __ = validator.validate_range_multiple_legend()

        assert not any("fora do intervalo" in error for error in errors)
