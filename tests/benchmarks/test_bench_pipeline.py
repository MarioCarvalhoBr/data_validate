#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Tiny pytest-benchmark check for the full CLI pipeline.

Marked `slow` and skipped unless `--benchmark-only` is passed, so it never slows down `pytest
tests/unit`, `pytest tests/e2e`, or a bare `pytest` run — it only runs via `make bench`. See
`.claude/rules/performance.md` for the performance budget this benchmark tracks against.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_NAME = "data_ground_truth_01"

pytestmark = pytest.mark.slow


def _run_cli(output_dir: Path) -> None:
    """Run the CLI once against `data_ground_truth_01` and assert it succeeded.

    Args:
        output_dir: Isolated output directory for the report.
    """
    command = [
        sys.executable,
        "-m",
        "data_validate.main",
        "--input_folder",
        f"data/input/{_FIXTURE_NAME}/",
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
    # The command list is built entirely from this module's own constants, never from unsanitised
    # external input, so the subprocess-injection risk S603 flags does not apply.
    result = subprocess.run(command, cwd=_REPO_ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    assert result.returncode == 0, f"CLI failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_bench_full_pipeline(benchmark: Any, tmp_path: Path, request: pytest.FixtureRequest) -> None:
    """Benchmark one full CLI run against `data_ground_truth_01`.

    Args:
        benchmark: The `pytest-benchmark` fixture.
        tmp_path: pytest's per-test temporary directory, used as an isolated output root.
        request: Pytest request object, used to check whether `--benchmark-only` was passed.
    """
    if not request.config.getoption("--benchmark-only"):
        pytest.skip("benchmarks only run with --benchmark-only (use `make bench`)")

    output_dir = tmp_path / _FIXTURE_NAME
    benchmark(_run_cli, output_dir)
