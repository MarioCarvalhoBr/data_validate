#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for BUG-013 (wrong dtypes/names in column declarations).

Pins the corrected placeholder ``pd.Series`` declarations on each ``Sp*`` model's
``RequiredColumn``/``DynamicColumn`` so a future edit cannot silently reintroduce the
``int64``-for-a-text-column mismatch these declarations used to carry. These placeholder
Series only ever have their ``.name`` read elsewhere in the codebase (confirmed by grep as
part of BUG-013's fix); their ``.dtype`` is not read by any validator, so this module is the
only place the corrected dtype is actually exercised until the ``ColumnSpec`` refactor
(BUG-002) replaces these placeholders entirely.
"""

from __future__ import annotations

# Import order matters: `data_validate.models` and `data_validate.controllers` share a circular
# import at package-init time (spellchecker_validator imports from `data_validate.models` while
# `data_validate.controllers` imports the validators package); importing `controllers` first
# forces full initialisation before `models` is imported directly (see
# `tests/unit/specs/test_sheet_specs.py` for the same workaround).
from data_validate.controllers.report.validation_report import ValidationReport  # noqa: F401
from data_validate.models.sp_description import SpDescription
from data_validate.models.sp_scenario import SpScenario
from data_validate.models.sp_temporal_reference import SpTemporalReference
from data_validate.models.sp_value import SpValue


class TestScenarioColumnDeclarations:
    """`SpScenario.RequiredColumn.COLUMN_NAME` must declare a text dtype, not an integer one."""

    def test_column_name_is_declared_as_string(self):
        column = SpScenario.RequiredColumn.COLUMN_NAME

        assert str(column.dtype) == "str"
        assert column.name == "nome"


class TestTemporalReferenceColumnDeclarations:
    """`SpTemporalReference.RequiredColumn.COLUMN_NAME` must declare a text dtype."""

    def test_column_name_is_declared_as_string(self):
        column = SpTemporalReference.RequiredColumn.COLUMN_NAME

        assert str(column.dtype) == "str"
        assert column.name == "nome"


class TestValueColumnDeclarations:
    """`SpValue.RequiredColumn.COLUMN_ID` is the id column; no `COLUMN_CODE` attribute exists."""

    def test_column_id_name_is_id(self):
        assert SpValue.RequiredColumn.COLUMN_ID.name == "id"

    def test_column_code_attribute_does_not_exist(self):
        assert not hasattr(SpValue.RequiredColumn, "COLUMN_CODE")


class TestDescriptionColumnDeclarations:
    """`SpDescription.DynamicColumn.COLUMN_LEGEND` must declare a nullable integer dtype."""

    def test_column_legend_is_declared_as_nullable_integer(self):
        column = SpDescription.DynamicColumn.COLUMN_LEGEND

        assert str(column.dtype) == "Int64"
        assert column.name == "legenda"
