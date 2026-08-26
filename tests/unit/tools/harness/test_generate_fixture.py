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
    """Test suite for _build_values()."""

    def test_build_values_one_column_per_combination_without_scenarios(self) -> None:
        temporal_df = pd.DataFrame({"nome": [2025], "simbolo": [0]})

        result = generate_fixture._build_values(indicators=2, temporal_df=temporal_df, scenarios_df=None, rows=3)

        assert set(result.columns) == {"id", "1-2025", "2-2025"}
        assert len(result) == 3

    def test_build_values_includes_scenario_suffix(self) -> None:
        temporal_df = pd.DataFrame({"nome": [2025], "simbolo": [0]})
        scenarios_df = pd.DataFrame({"nome": [1, 2], "simbolo": [1, 2]})

        result = generate_fixture._build_values(
            indicators=1, temporal_df=temporal_df, scenarios_df=scenarios_df, rows=1
        )

        assert set(result.columns) == {"id", "1-2025-1", "1-2025-2"}


class TestMain:
    """Test suite for main()."""

    def test_main_success(self, tmp_path: Path) -> None:
        exit_code = generate_fixture.main(["--indicators", "2", "--out", str(tmp_path / "bundle")])

        assert exit_code == 0

    def test_main_reports_invalid_arguments(self, tmp_path: Path) -> None:
        exit_code = generate_fixture.main(["--indicators", "0", "--out", str(tmp_path / "bundle")])

        assert exit_code == 1
