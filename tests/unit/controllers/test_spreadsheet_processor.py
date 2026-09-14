#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `SpreadsheetProcessor._read_data`/`_run_rule_registries` (ARC-009 loader-consumer
migration; ARC-017 Phase 3b/Phase 3 Port 2 rules-engine port).

BUG-018/ARC-009: `_read_data` now calls `DataLoaderFacade.load()` (returning a `LoadResult`)
instead of the deprecated `load_all` property. Since ARC-001 (Phase 3 Port 8),
`SpreadsheetProcessor.__init__` no longer runs the whole pipeline as a side effect — `run()` must
be called explicitly — but `_read_data`/`_run_rule_registries` are still exercised in isolation on
a bare instance built via `__new__`, with only the attributes each method itself reads
pre-populated, rather than going through a full `run()`.

`_run_structure_rules` (a single-registry, folder-listing-only helper) was generalised into
`_run_rule_registries(registries, ctx)` when the description rules were ported (ARC-017 Phase 3
Port 2): `TestRunStructureRulesUsesTheEngine` below now builds a `RuleContext` directly (the same
way `tests/unit/rules/test_structure.py` does) and calls `_run_rule_registries([STRUCTURE_REGISTRY], ctx)`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from data_validate.helpers import tools
from data_validate.controllers.spreadsheet_processor import SpreadsheetProcessor
from data_validate import config, models
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet, LoadResult
from data_validate.rules import RuleContext, STRUCTURE_REGISTRY, TERRITORY_REGISTRY_RULES


def _fake_raw_data_map() -> dict[str, LoadedSheet]:
    """Build the minimal raw_data_map `_read_data` reads after loading (scenarios + legend)."""
    scenario_frame = pd.DataFrame({"simbolo": ["O", "P"]})

    return {
        models.SpScenario.CONSTANTS.SP_NAME: LoadedSheet(
            input_folder="/tmp/input",
            path=Path("cenarios.csv"),
            raw_data=scenario_frame,
            is_read_successful=True,
        ),
        models.SpLegend.CONSTANTS.SP_NAME: LoadedSheet(
            input_folder="/tmp/input",
            path=Path("legenda"),
            raw_data=pd.DataFrame(),
            is_read_successful=False,
        ),
    }


def _build_bare_processor(mocker) -> SpreadsheetProcessor:
    """Construct a `SpreadsheetProcessor` without running `__init__`'s full pipeline (ARC-001)."""
    processor = SpreadsheetProcessor.__new__(SpreadsheetProcessor)
    processor.context = mocker.MagicMock()
    processor.context.data_args.data_file.input_folder = "/tmp/input"
    processor.context.config.MAX_INPUT_FILE_BYTES = 100
    processor.context.config.MAX_SHEET_ROWS = 10
    processor.context.config.MAX_SHEET_COLUMNS = 10
    processor.language_manager = mocker.MagicMock()
    processor.input_folder = "/tmp/input"
    processor.validation_titles = {name.value: name.value for name in config.NamesEnum}
    processor.validation_reports = mocker.MagicMock()
    processor.scenarios = []
    processor._models_by_name = {}
    return processor


class TestReadDataUsesLoad:
    """`_read_data` calls `DataLoaderFacade.load()`, not the deprecated `load_all` property."""

    def test_read_data_calls_load_method_once(self, mocker) -> None:
        """The real method under ARC-009 is `load()`; `_read_data` must call exactly that."""
        processor = _build_bare_processor(mocker)

        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=_fake_raw_data_map(), errors=["some error"])
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        fake_facade.load.assert_called_once()

    def test_read_data_populates_raw_data_map_and_scenarios(self, mocker) -> None:
        """`raw_data_map`/`scenarios`/`model_configurations` are derived from the `LoadResult`."""
        processor = _build_bare_processor(mocker)

        raw_data_map = _fake_raw_data_map()
        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=raw_data_map, errors=[])
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        assert processor.raw_data_map is raw_data_map
        assert processor.scenarios == ["O", "P"]
        assert processor.model_configurations[models.SpModelABC.CONFIG_KEYS.SCENARIO_READ_SUCCESS] is True
        assert processor.model_configurations[models.SpModelABC.CONFIG_KEYS.LEGEND_READ_SUCCESS] is False
        assert processor.model_configurations[models.SpModelABC.CONFIG_KEYS.SCENARIOS] == ["O", "P"]

    def test_read_data_extends_report_with_load_errors(self, mocker) -> None:
        """Errors surfaced by `LoadResult.errors` are extended into the FS report category."""
        processor = _build_bare_processor(mocker)

        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=_fake_raw_data_map(), errors=["boom"])
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        processor.validation_reports.extend.assert_any_call(
            processor.validation_titles[config.NamesEnum.FS.value], errors=["boom"], warnings=[]
        )

    def test_read_data_stores_the_territory_registry_from_the_load_result(self, mocker) -> None:
        """PROTO-013: `_read_data` populates `self.territory_registry` from `LoadResult`."""
        processor = _build_bare_processor(mocker)

        registry = tools.TerritoryRegistry(ids=frozenset({1, 2}), loaded=True, error=None)
        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=_fake_raw_data_map(), errors=[], territory_registry=registry)
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        assert processor.territory_registry is registry

    def test_read_data_extends_report_with_registry_warnings(self, mocker) -> None:
        """PROTO-013: `LoadResult.warnings` (e.g. duplicate registry ids) reach the FS category."""
        processor = _build_bare_processor(mocker)

        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=_fake_raw_data_map(), errors=[], warnings=["dup"])
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        processor.validation_reports.extend.assert_any_call(
            processor.validation_titles[config.NamesEnum.FS.value], errors=[], warnings=["dup"]
        )


class TestRunStructureRulesUsesTheEngine:
    """`_run_rule_registries([STRUCTURE_REGISTRY], ctx)` renders findings into the FS report."""

    def _build_processor_for(self, mocker, input_folder: Path) -> SpreadsheetProcessor:
        processor = SpreadsheetProcessor.__new__(SpreadsheetProcessor)
        processor.input_folder = str(input_folder)
        processor.scenarios = []
        processor.validation_titles = {name.value: name.value for name in config.NamesEnum}
        # Mirrors `_prepare_statement`, which always runs before `_build_pipeline` in `run()`:
        # every `NamesEnum` bucket exists before a validator ever extends it.
        processor.validation_reports = ValidationReport()
        for title in processor.validation_titles.values():
            processor.validation_reports.add_by_name(title)
        processor.language_manager = mocker.MagicMock()
        processor.language_manager.text = mocker.MagicMock(side_effect=lambda key, **kwargs: key)
        return processor

    @staticmethod
    def _structure_context(input_folder: Path) -> RuleContext:
        """Build a minimal, structure-only `RuleContext` (no sheets/cleaned data needed)."""
        return RuleContext(
            sheets={},
            cleaned={},
            options={
                "input_folder": input_folder,
                "dir_entries": tuple(sorted(entry.name for entry in input_folder.iterdir())),
                "scenarios": [],
            },
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

    def test_an_unexpected_file_is_rendered_into_the_fs_report(self, mocker, tmp_path: Path) -> None:
        for stem in ("descricao", "composicao", "valores", "referencia_temporal"):
            (tmp_path / f"{stem}.csv").touch()
        (tmp_path / "arquivo_aleatorio.xlsx").touch()

        processor = self._build_processor_for(mocker, tmp_path)
        processor._run_rule_registries([STRUCTURE_REGISTRY], self._structure_context(tmp_path))

        fs_title = processor.validation_titles[config.NamesEnum.FS.value]
        assert "validator_structure_error_unexpected_file" in processor.validation_reports[fs_title].errors

    def test_a_clean_bundle_reports_no_structure_errors(self, mocker, tmp_path: Path) -> None:
        for stem in ("descricao", "composicao", "valores", "referencia_temporal"):
            (tmp_path / f"{stem}.csv").touch()

        processor = self._build_processor_for(mocker, tmp_path)
        processor._run_rule_registries([STRUCTURE_REGISTRY], self._structure_context(tmp_path))

        fs_title = processor.validation_titles[config.NamesEnum.FS.value]
        assert processor.validation_reports[fs_title].errors == []

    def test_an_empty_input_folder_reports_empty_directory_and_missing_files(self, mocker, tmp_path: Path) -> None:
        processor = self._build_processor_for(mocker, tmp_path)
        processor._run_rule_registries([STRUCTURE_REGISTRY], self._structure_context(tmp_path))

        fs_title = processor.validation_titles[config.NamesEnum.FS.value]
        errors = processor.validation_reports[fs_title].errors
        assert errors.count("validator_structure_error_empty_directory") == 1
        assert errors.count("validator_structure_error_missing_file") == 4


class _FakeModel:
    """Minimal `SpModelABC`-shaped double: construction never runs anything (ARC-001)."""

    class CONSTANTS:
        SP_NAME = "descricao"

    def __init__(self, context, data_model, **kwargs) -> None:
        self.context = context
        self.data_model = data_model
        self.kwargs = kwargs
        self.ran = False
        self.structural_errors: list[str] = []
        self.structural_warnings: list[str] = []
        self.data_cleaning_errors: list[str] = []
        self.data_cleaning_warnings: list[str] = []

    def run(self) -> None:
        self.ran = True


class TestConfigureCallsRunExplicitly:
    """ARC-001 (Phase 3 Port 8): `_configure` calls `model.run()` right after construction."""

    def test_each_constructed_model_has_run_called_on_it(self, mocker) -> None:
        processor = _build_bare_processor(mocker)
        processor.raw_data_map = {"descricao": mocker.MagicMock()}
        processor.model_configurations = {}
        processor.initialized_models = []
        processor.target_model_classes = [_FakeModel]

        processor._configure()

        assert processor.initialized_models[0].ran is True

    def test_configure_populates_models_by_name(self, mocker) -> None:
        """ARC-006: `_configure` keys `_models_by_name` by each model's `CONSTANTS.SP_NAME`,
        used for name-keyed lookups instead of a linear `isinstance` scan."""
        processor = _build_bare_processor(mocker)
        processor.raw_data_map = {"descricao": mocker.MagicMock()}
        processor.model_configurations = {}
        processor.initialized_models = []
        processor.target_model_classes = [_FakeModel]

        processor._configure()

        assert processor._models_by_name["descricao"] is processor.initialized_models[0]


class TestFinalizeTerritoryRegistryStatus:
    """PROTO-013/PROTO-018: `_finalize_territory_registry_status`'s skip/flag bookkeeping."""

    def _build_processor(self, mocker, *, registry: tools.TerritoryRegistry) -> SpreadsheetProcessor:
        processor = SpreadsheetProcessor.__new__(SpreadsheetProcessor)
        processor.context = mocker.MagicMock()
        processor.context.skipped_validations = []
        processor.validation_titles = {name.value: name.value for name in config.NamesEnum}
        processor.validation_reports = ValidationReport()
        for title in processor.validation_titles.values():
            processor.validation_reports.add_by_name(title)
        processor.territory_registry = registry
        return processor

    def test_absent_registry_is_appended_to_skipped_validations(self, mocker) -> None:
        processor = self._build_processor(mocker, registry=tools.TerritoryRegistry())

        processor._finalize_territory_registry_status()

        terr_title = processor.validation_titles[config.NamesEnum.TERR.value]
        assert terr_title in processor.context.skipped_validations
        assert processor.context.spatial_data_validated is False

    def test_loaded_registry_with_zero_errors_is_not_skipped_and_flag_is_true(self, mocker) -> None:
        processor = self._build_processor(
            mocker, registry=tools.TerritoryRegistry(ids=frozenset({1}), loaded=True, error=None)
        )

        processor._finalize_territory_registry_status()

        assert processor.context.skipped_validations == []
        assert processor.context.spatial_data_validated is True

    def test_loaded_registry_with_errors_is_not_skipped_but_flag_is_false(self, mocker) -> None:
        processor = self._build_processor(
            mocker, registry=tools.TerritoryRegistry(ids=frozenset({1}), loaded=True, error=None)
        )
        terr_title = processor.validation_titles[config.NamesEnum.TERR.value]
        processor.validation_reports.extend(terr_title, errors=["rule.TERR-001.error"])

        processor._finalize_territory_registry_status()

        assert processor.context.skipped_validations == []
        assert processor.context.spatial_data_validated is False

    def test_run_rule_registries_renders_terr_findings_into_the_terr_report(self, mocker) -> None:
        """`_run_rule_registries([TERRITORY_REGISTRY_RULES], ctx)` reaches the TERR bucket."""
        processor = self._build_processor(
            mocker, registry=tools.TerritoryRegistry(ids=frozenset({1}), loaded=True, error=None)
        )
        processor.language_manager = mocker.MagicMock()
        processor.language_manager.text = mocker.MagicMock(side_effect=lambda key, **kwargs: key)

        valores = pd.DataFrame({"id": ["1", "2"]})
        ctx = RuleContext(
            sheets={"valores": valores},
            cleaned={},
            options={
                "filenames": {"valores": "valores.xlsx"},
                "territory_registry_present": True,
                "territory_registry_ids": frozenset({1}),
            },
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        processor._run_rule_registries([TERRITORY_REGISTRY_RULES], ctx)

        terr_title = processor.validation_titles[config.NamesEnum.TERR.value]
        assert "rule.TERR-001.error" in processor.validation_reports[terr_title].errors
