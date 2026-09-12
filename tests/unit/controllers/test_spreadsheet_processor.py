#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `SpreadsheetProcessor._read_data` (ARC-009 loader-consumer migration).

BUG-018/ARC-009: `_read_data` now calls `DataLoaderFacade.load()` (returning a `LoadResult`)
instead of the deprecated `load_all` property. `SpreadsheetProcessor.__init__` runs the whole
pipeline as a side effect (ARC-001, a pre-existing debt this test does not attempt to fix), so
`_read_data` is exercised in isolation on a bare instance built via `__new__`, with only the
attributes `_read_data` itself reads pre-populated.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Import order matters: `data_validate.models` and `data_validate.controllers` share a circular
# import at package-init time (spellchecker_validator imports from `data_validate.models` while
# `data_validate.controllers` imports the validators package); importing `controllers` first
# forces full initialisation before `models` is imported directly (see
# `tests/unit/specs/test_sheet_specs.py` for the same workaround).
from data_validate.controllers.spreadsheet_processor import SpreadsheetProcessor
from data_validate import config, models
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel, LoadResult


def _fake_raw_data_map() -> dict[str, DataLoaderModel]:
    """Build the minimal raw_data_map `_read_data` reads after loading (scenarios + legend)."""
    scenario_frame = pd.DataFrame({"simbolo": ["O", "P"]})

    return {
        models.SpScenario.CONSTANTS.SP_NAME: DataLoaderModel(
            input_folder="/tmp/input",
            path=Path("cenarios.csv"),
            raw_data=scenario_frame,
            is_read_successful=True,
        ),
        models.SpLegend.CONSTANTS.SP_NAME: DataLoaderModel(
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
        assert processor.model_configurations[models.SpModelABC.VAR_CONSTS.SCENARIO_READ_SUCCESS] is True
        assert processor.model_configurations[models.SpModelABC.VAR_CONSTS.LEGEND_READ_SUCCESS] is False
        assert processor.model_configurations[models.SpModelABC.VAR_CONSTS.SCENARIOS] == ["O", "P"]

    def test_read_data_extends_report_with_load_errors(self, mocker) -> None:
        """Errors surfaced by `LoadResult.errors` are extended into the FS report category."""
        processor = _build_bare_processor(mocker)

        fake_facade = mocker.MagicMock()
        fake_facade.load.return_value = LoadResult(models=_fake_raw_data_map(), errors=["boom"])
        mocker.patch("data_validate.controllers.spreadsheet_processor.tools.DataLoaderFacade", return_value=fake_facade)

        processor._read_data()

        processor.validation_reports.extend.assert_any_call(
            processor.validation_titles[config.NamesEnum.FS.value], errors=["boom"]
        )
