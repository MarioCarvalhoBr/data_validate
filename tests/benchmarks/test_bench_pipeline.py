#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
`pytest-benchmark` checks for the full CLI pipeline, small and budget-sized (PERF-009).

Marked `slow`. The two `pytest-benchmark` cases (`test_bench_full_pipeline[small]`/`[large]`) are
skipped unless `--benchmark-only` is passed, so they never slow down `pytest tests/unit`, `pytest
tests/e2e`, or a bare `pytest` run — they only run via `make bench`. See
`.claude/rules/performance.md` and `.specs/quality/performance.md` for the performance budget
these benchmarks track against, and `.specs/quality/backlog/05-performance.md`'s PERF-009/PERF-007
entries for the measured numbers this module's fixture sizing reproduces.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from tools.harness.generate_fixture import generate_fixture

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SMALL_FIXTURE_NAME = "data_ground_truth_01"

# PERF-009 budget-sized bundle. `.specs/quality/performance.md`'s "5,000 indicators x 60 value
# columns (approx 300k cells)" budget means 5,000 *rows* (one per territory, e.g. the ~5,570
# Brazilian municipalities a real sector bundle covers), not 5,000 indicator *codes* as `valores`
# columns: `FileStructureValidator`'s own structural size limit caps `valores` at 5,000 columns,
# so a bundle with 5,000 indicator codes as column-groups is rejected outright before any business
# rule runs (confirmed while building this fixture — see `tools/harness/generate_fixture.py`'s
# module docstring and this file's own measured numbers below). 6 indicators (1 root + 5 children)
# x 5 years x 3 scenarios yields 65 value columns; 5,000 rows gives approx 325k cells.
_LARGE_INDICATORS = 6
_LARGE_YEARS = 5
_LARGE_SCENARIOS = 3
_LARGE_ROWS = 5000

# Generous CI margin (PERF-009): measured locally, one full CLI run (validation + HTML + PDF)
# against the budget-sized bundle takes ~3.1s wall / ~180MB peak RSS — see
# `.specs/quality/performance.md`'s budget table and `.specs/quality/backlog/05-performance.md`'s
# PERF-009 entry for the `/usr/bin/time -v` numbers this bound is derived from.
_LARGE_BUDGET_SECONDS = 60.0

pytestmark = pytest.mark.slow


def _run_cli(input_dir: Path, output_dir: Path) -> None:
    """Run the CLI once against `input_dir` and assert it succeeded.

    Args:
        input_dir: Fixture input folder (absolute path) to validate.
        output_dir: Isolated output directory for the report.
    """
    command = [
        sys.executable,
        "-m",
        "data_validate.main",
        "--input_folder",
        f"{input_dir}/",
        "--output_folder",
        f"{output_dir}/",
        "--locale",
        "pt_BR",
        "--no-time",
        "--no-version",
        "--sector",
        "Setor A",
        "--protocol",
        "Protocolo B",
        "--user",
        "Usuário C",
    ]
    # The command list is built entirely from this module's own constants/parameters, never from
    # unsanitised external input, so the subprocess-injection risk S603 flags does not apply.
    result = subprocess.run(command, cwd=_REPO_ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    assert result.returncode == 0, f"CLI failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"


@pytest.fixture(scope="session")
def large_fixture_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate the PERF-009 budget-sized bundle once per test session.

    Args:
        tmp_path_factory: pytest's session-scoped temporary directory factory.

    Returns:
        Path: The generated bundle's input folder.
    """
    out_dir = tmp_path_factory.mktemp("perf009_large_fixture")
    generate_fixture(_LARGE_INDICATORS, _LARGE_YEARS, _LARGE_SCENARIOS, _LARGE_ROWS, out_dir)
    return out_dir


@pytest.mark.parametrize("fixture_kind", ["small", "large"])
def test_bench_full_pipeline(
    benchmark: Any,
    fixture_kind: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
    large_fixture_dir: Path,
) -> None:
    """Benchmark one full CLI run against the small (repo) or large (generated) fixture.

    Args:
        benchmark: The `pytest-benchmark` fixture.
        fixture_kind: `"small"` (`data/input/data_ground_truth_01`) or `"large"` (the generated
            PERF-009 budget-sized bundle, see `large_fixture_dir`).
        tmp_path: pytest's per-test temporary directory, used as an isolated output root.
        request: Pytest request object, used to check whether `--benchmark-only` was passed.
        large_fixture_dir: The generated large bundle's input folder (session-scoped, built once).
    """
    if not request.config.getoption("--benchmark-only"):
        pytest.skip("benchmarks only run with --benchmark-only (use `make bench`)")

    input_dir = _REPO_ROOT / "data" / "input" / _SMALL_FIXTURE_NAME if fixture_kind == "small" else large_fixture_dir
    output_dir = tmp_path / fixture_kind
    benchmark(_run_cli, input_dir, output_dir)


def test_large_bundle_validates_under_budget(large_fixture_dir: Path, tmp_path: Path) -> None:
    """PERF-009 CI smoke test: the large bundle validates well under a generous time budget.

    Deliberately not a `pytest-benchmark` case (no `--benchmark-only` gate, no statistical
    rounds): a single timed run, so it is cheap enough to run as a plain regression guard against
    a drastic slowdown, independent of whether `make bench` is invoked. Measured locally (see
    module docstring): ~3.1s; `_LARGE_BUDGET_SECONDS` gives a ~20x CI margin.

    Args:
        large_fixture_dir: The generated large bundle's input folder (session-scoped).
        tmp_path: pytest's per-test temporary directory, used as an isolated output root.
    """
    output_dir = tmp_path / "smoke"
    started_at = time.perf_counter()
    _run_cli(large_fixture_dir, output_dir)
    elapsed_seconds = time.perf_counter() - started_at

    assert elapsed_seconds < _LARGE_BUDGET_SECONDS, (
        f"large bundle took {elapsed_seconds:.1f}s, budget is {_LARGE_BUDGET_SECONDS}s"
    )
