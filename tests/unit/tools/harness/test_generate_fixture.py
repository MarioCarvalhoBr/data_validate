#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/harness/generate_fixture.py."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tools.harness import generate_fixture


class TestGenerateFixture:
    """Test suite for generate_fixture()."""

    def test_generate_fixture_creates_required_sheets_without_scenarios(self, tmp_path: Path) -> None:
        written = generate_fixture.generate_fixture(indicators=3, years=1, scenarios=0, rows=2, out_dir=tmp_path)

        names = {path.stem for path in written}
        assert names == {"descricao", "composicao", "valores", "referencia_temporal"}
        assert all(path.exists() for path in written)

    def test_generate_fixture_includes_scenarios_sheet_when_requested(self, tmp_path: Path) -> None:
        written = generate_fixture.generate_fixture(indicators=2, years=2, scenarios=2, rows=1, out_dir=tmp_path)

        assert "cenarios" in {path.stem for path in written}

    def test_generate_fixture_forces_single_temporal_row_without_scenarios(self, tmp_path: Path) -> None:
        generate_fixture.generate_fixture(indicators=2, years=5, scenarios=0, rows=1, out_dir=tmp_path)

        temporal_path = next(tmp_path.glob("referencia_temporal.*"))
        content = temporal_path.read_text(encoding="utf-8")
        # Header + exactly one data row (protocol rule: no cenarios means exactly one row).
        assert len([line for line in content.splitlines() if line.strip()]) == 2

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"indicators": 0, "years": 1, "scenarios": 0, "rows": 1},
            {"indicators": 1, "years": 0, "scenarios": 0, "rows": 1},
            {"indicators": 1, "years": 1, "scenarios": -1, "rows": 1},
            {"indicators": 1, "years": 1, "scenarios": 0, "rows": 0},
        ],
    )
    def test_generate_fixture_rejects_invalid_arguments(self, tmp_path: Path, kwargs: dict[str, int]) -> None:
        with pytest.raises(ValueError):
            generate_fixture.generate_fixture(out_dir=tmp_path, **kwargs)


class TestBuildValues:
    """Test suite for _build_values().

    VAL-003 (`rules/value.py::check_value_combination_relation`) only ever allows a `nivel == 1`
    (root) indicator zero `valores` columns, and builds every other indicator's expected column
    names from `referencia_temporal.simbolo` (never `nome`) — see `_build_values`'s own docstring.
    These cases pin exactly that shape, the bug this module used to have (PERF-009): the root
    indicator's columns used to be generated (and then flagged as "unnecessary for a level 1
    indicator" by VAL-003) and the year suffix used to be `nome` instead of `simbolo`.
    """

    def test_build_values_excludes_root_indicator(self) -> None:
        """Indicator 1 (the root, `_ROOT_CODE`) never gets a `valores` column."""
        temporal_df = pd.DataFrame({"nome": [2025], "simbolo": [2025]})

        result = generate_fixture._build_values(indicators=2, temporal_df=temporal_df, scenarios_df=None, rows=3)

        assert set(result.columns) == {"id", "2-2025"}
        assert len(result) == 3

    def test_build_values_one_column_per_combination_without_scenarios(self) -> None:
        temporal_df = pd.DataFrame({"nome": [2025], "simbolo": [2025]})

        result = generate_fixture._build_values(indicators=3, temporal_df=temporal_df, scenarios_df=None, rows=3)

        assert set(result.columns) == {"id", "2-2025", "3-2025"}
        assert len(result) == 3

    def test_build_values_base_year_column_uses_simbolo_not_nome(self) -> None:
        """The base-year column is named after `simbolo`, never `nome` (they can differ)."""
        temporal_df = pd.DataFrame({"nome": ["Ano base"], "simbolo": [2025]})

        result = generate_fixture._build_values(indicators=2, temporal_df=temporal_df, scenarios_df=None, rows=1)

        assert "2-2025" in result.columns
        assert "2-Ano base" not in result.columns

    def test_build_values_includes_scenario_suffix_only_for_years_after_the_first(self) -> None:
        temporal_df = pd.DataFrame({"nome": [2025, 2026], "simbolo": [2025, 2026]})
        scenarios_df = pd.DataFrame({"nome": [1, 2], "simbolo": [1, 2]})

        result = generate_fixture._build_values(
            indicators=2, temporal_df=temporal_df, scenarios_df=scenarios_df, rows=1
        )

        # Base year (2025): one column, no scenario suffix. Later year (2026): one column per
        # scenario symbol. No `2-2025-<symbol>` (base year is never scenario-suffixed) and no
        # bare `2-2026` (a later year always carries a scenario suffix).
        assert set(result.columns) == {"id", "2-2025", "2-2026-1", "2-2026-2"}

    def test_build_values_cells_are_two_decimal_strings_within_unit_range(self) -> None:
        """Every generated value is a `"0.01"`..`"1.00"` string (LEG-015's default `[0, 1]`
        legend range applies whenever no `legenda` sheet is generated, which this harness never
        does)."""
        temporal_df = pd.DataFrame({"nome": [2025], "simbolo": [2025]})

        result = generate_fixture._build_values(indicators=2, temporal_df=temporal_df, scenarios_df=None, rows=4)

        for value in result["2-2025"]:
            assert isinstance(value, str)
            assert len(value.split(".")[1]) == 2
            assert 0.0 < float(value) <= 1.0


class TestMain:
    """Test suite for main()."""

    def test_main_success(self, tmp_path: Path) -> None:
        exit_code = generate_fixture.main(["--indicators", "2", "--out", str(tmp_path / "bundle")])

        assert exit_code == 0

    def test_main_reports_invalid_arguments(self, tmp_path: Path) -> None:
        exit_code = generate_fixture.main(["--indicators", "0", "--out", str(tmp_path / "bundle")])

        assert exit_code == 1
