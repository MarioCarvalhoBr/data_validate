#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Consistency proof for the `SheetSpec` registry (ARC-003).

Every test in this module asserts that `data_validate.specs.SHEET_SPECS` agrees with one of
the legacy sources it supersedes (ADR-0003): `SpreadsheetInfo` and each `models/sp_*.py`'s
`RequiredColumn`/`OptionalColumn`/`DynamicColumn`/`PluralColumn`. A failure here means the registry
has drifted from a source it should mirror.

BUG-018/ARC-003 (Phase 2 loader migration): the third legacy source this module used to compare
against, `data_loader.common.config.Config`, is deleted -- `SHEET_SPECS` is now the sole input the
loader (`FileScanner`, `DataLoaderFacade`) reads for header layout, CSV separator and the
required flag, so there is nothing left to prove consistent with it.
`TestSheetSpecsMatchDataLoaderConfig` is deleted along with `Config`; its former assertions
(header layout, separator, required flag) are pinned as fixed expected values in
`TestSheetSpecsPinnedLoaderFacts` below instead.
"""

from __future__ import annotations

import dataclasses
from typing import ClassVar

import pytest

# Import order matters: `data_validate.models` and `data_validate.controllers` share a circular
# import at package-init time (spellchecker_validator imports from `data_validate.models` while
# `data_validate.controllers` imports the validators package); importing `controllers` first
# forces full initialisation before `models` is imported directly.
from data_validate.controllers.report.validation_report import ValidationReport  # noqa: F401
from data_validate.models import (
    SpComposition,
    SpDescription,
    SpDictionary,
    SpLegend,
    SpProportionality,
    SpScenario,
    SpTemporalReference,
    SpValue,
)

from data_validate.config.spreadsheet_info import SpreadsheetInfo
from data_validate.specs.sheet_specs import (
    ALLOWED_EXTENSIONS,
    SHEET_SPECS,
    ColumnKind,
    ColumnSpec,
    HeaderLayout,
    SheetSpec,
)

MODEL_BY_SHEET = {
    "descricao": SpDescription,
    "composicao": SpComposition,
    "valores": SpValue,
    "referencia_temporal": SpTemporalReference,
    "proporcionalidades": SpProportionality,
    "cenarios": SpScenario,
    "legenda": SpLegend,
    "dicionario": SpDictionary,
}


class TestSheetSpecsMatchSpreadsheetInfo:
    """`SHEET_SPECS` required flags must mirror `SpreadsheetInfo.EXPECTED_FILES`/`OPTIONAL_FILES`."""

    @pytest.mark.parametrize("sheet_name", list(SHEET_SPECS))
    def test_required_flag_matches_spreadsheet_info(self, sheet_name):
        info = SpreadsheetInfo()
        expected_required = sheet_name in info.EXPECTED_FILES
        expected_optional = sheet_name in info.OPTIONAL_FILES

        assert expected_required or expected_optional, f"{sheet_name} missing from SpreadsheetInfo"
        assert SHEET_SPECS[sheet_name].required is expected_required

    def test_registry_covers_exactly_the_spreadsheet_info_sheets(self):
        info = SpreadsheetInfo()
        legacy_sheet_names = set(info.EXPECTED_FILES) | set(info.OPTIONAL_FILES)

        assert set(SHEET_SPECS) == legacy_sheet_names

    def test_allowed_extensions_match_spreadsheet_info(self):
        info = SpreadsheetInfo()

        assert list(ALLOWED_EXTENSIONS) == info.ALLOWED_EXTENSIONS


class TestSheetSpecsPinnedLoaderFacts:
    """Pinned header layout/separator/required values the loader now reads only from `SHEET_SPECS`.

    These are the exact values `TestSheetSpecsMatchDataLoaderConfig` used to prove against the now
    -deleted `data_loader.common.config.Config` (BUG-018/ARC-003); pinning them here still catches
    an accidental drift, just without a second source to compare against.
    """

    _EXPECTED: ClassVar[dict[str, tuple[bool, HeaderLayout, str]]] = {
        "descricao": (True, HeaderLayout.SINGLE, "|"),
        "composicao": (True, HeaderLayout.SINGLE, "|"),
        "valores": (True, HeaderLayout.SINGLE, "|"),
        "referencia_temporal": (True, HeaderLayout.SINGLE, "|"),
        "proporcionalidades": (False, HeaderLayout.DOUBLE, "|"),
        "cenarios": (False, HeaderLayout.SINGLE, "|"),
        "legenda": (False, HeaderLayout.SINGLE, "|"),
        "dicionario": (False, HeaderLayout.SINGLE, "|"),
    }

    @pytest.mark.parametrize("sheet_name", list(SHEET_SPECS))
    def test_header_layout_matches_pinned_value(self, sheet_name):
        _, expected_header, _ = self._EXPECTED[sheet_name]

        assert SHEET_SPECS[sheet_name].header is expected_header

    @pytest.mark.parametrize("sheet_name", list(SHEET_SPECS))
    def test_csv_separator_matches_pinned_value(self, sheet_name):
        _, _, expected_separator = self._EXPECTED[sheet_name]

        assert SHEET_SPECS[sheet_name].csv_separator == expected_separator

    @pytest.mark.parametrize("sheet_name", list(SHEET_SPECS))
    def test_required_flag_matches_pinned_value(self, sheet_name):
        expected_required, _, _ = self._EXPECTED[sheet_name]

        assert SHEET_SPECS[sheet_name].required is expected_required


class TestSheetSpecsMatchModelColumns:
    """`SHEET_SPECS` column sets must mirror each model's declared column groups."""

    @pytest.mark.parametrize("sheet_name", list(MODEL_BY_SHEET))
    def test_required_columns_match_model(self, sheet_name):
        model = MODEL_BY_SHEET[sheet_name]
        spec = SHEET_SPECS[sheet_name]
        required_names = [column.name for column in spec.required_columns]

        assert required_names == list(model.RequiredColumn.ALL)

    def test_optional_columns_match_description_model(self):
        spec = SHEET_SPECS["descricao"]
        optional_names = [column.name for column in spec.optional_columns]

        assert optional_names == list(SpDescription.OptionalColumn.ALL)

    def test_dynamic_columns_match_description_model(self):
        spec = SHEET_SPECS["descricao"]
        dynamic_names = [column.name for column in spec.dynamic_columns]

        assert dynamic_names == list(SpDescription.DynamicColumn.ALL)

    def test_plural_name_pairs_match_description_model(self):
        spec = SHEET_SPECS["descricao"]
        plural_names = [pair[1] for pair in spec.plural_name_pairs]

        assert plural_names == list(SpDescription.PluralColumn.ALL)

    @pytest.mark.parametrize(
        "sheet_name",
        [name for name in MODEL_BY_SHEET if name != "descricao"],
    )
    def test_sheets_without_optional_or_dynamic_columns_declare_none(self, sheet_name):
        spec = SHEET_SPECS[sheet_name]

        assert spec.optional_columns == ()
        assert spec.dynamic_columns == ()
        assert spec.plural_name_pairs == ()


class TestSheetSpecHelpers:
    """Behaviour of the `SheetSpec`/`ColumnSpec` convenience properties."""

    def test_column_names_returns_every_column_in_declaration_order(self):
        spec = SHEET_SPECS["descricao"]

        assert spec.column_names[0] == "codigo"
        assert spec.column_names[-1] == "legenda"
        assert len(spec.column_names) == len(spec.columns)

    def test_filename_candidates_uses_allowed_extensions(self):
        spec = SHEET_SPECS["composicao"]

        assert spec.filename_candidates == ("composicao.csv", "composicao.xlsx")

    def test_required_columns_is_empty_when_no_required_columns(self):
        empty_spec = SheetSpec(
            name="empty",
            required=False,
            header=HeaderLayout.SINGLE,
            columns=(ColumnSpec(name="only_optional", dtype="str", kind=ColumnKind.OPTIONAL),),
            description="Fixture-only sheet with no required columns.",
        )

        assert empty_spec.required_columns == ()
        assert [column.name for column in empty_spec.optional_columns] == ["only_optional"]
        assert empty_spec.dynamic_columns == ()


class TestSheetSpecsAreImmutable:
    """`ColumnSpec`, `SheetSpec`, and `SHEET_SPECS` must all be frozen/read-only."""

    def test_column_spec_is_frozen(self):
        column = ColumnSpec(name="codigo", dtype="int", kind=ColumnKind.REQUIRED)

        with pytest.raises(dataclasses.FrozenInstanceError):
            column.name = "outro"  # type: ignore[misc]

    def test_sheet_spec_is_frozen(self):
        spec = SHEET_SPECS["descricao"]

        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.required = False  # type: ignore[misc]

    def test_sheet_specs_mapping_rejects_item_assignment(self):
        with pytest.raises(TypeError):
            SHEET_SPECS["descricao"] = SHEET_SPECS["descricao"]  # type: ignore[index]

    def test_sheet_specs_mapping_rejects_new_key(self):
        with pytest.raises(TypeError):
            SHEET_SPECS["a_new_sheet"] = SHEET_SPECS["descricao"]  # type: ignore[index]
