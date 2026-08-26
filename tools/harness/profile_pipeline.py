#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Profile a full `data_validate` CLI run with `cProfile`.

Runs `data_validate.main` in-process (via `runpy`, with `sys.argv` set to the same flags the
platform uses) wrapped in a `cProfile.Profile()`, then writes a `.prof` file (loadable with
`snakeviz`/`pstats`) and a plain-text top-N report sorted by cumulative time. Used by `make
profile` and `.claude/agents/performance-engineer.md`; see `.claude/rules/performance.md` for the
performance budget this measures against.
"""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import runpy
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_FIXTURE = "data_ground_truth_01"
_DEFAULT_TOP_N = 40


def _resolve_input_dir(fixture: str) -> Path:
    """Resolve a fixture argument to an input directory.

    Args:
        fixture: Either a fixture name under `data/input/`, or a path (absolute or relative to
            the current working directory) to an input folder.

    Returns:
        Path: The resolved input directory (not guaranteed to exist).
    """
    candidate = Path(fixture)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    return _REPO_ROOT / "data" / "input" / fixture


def profile_pipeline(input_dir: Path, output_dir: Path, report_dir: Path, top: int) -> Path:
    """Run the CLI once under `cProfile` and write the profile artefacts.

    Args:
        input_dir: Fixture input folder to validate.
        output_dir: Isolated folder for the run's HTML/PDF report output.
        report_dir: Directory to write the `.prof` and top-N text report into.
        top: Number of functions to include in the cumulative-time text report.

    Returns:
        Path: The path of the written `.prof` file.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    argv_backup = sys.argv[:]
    sys.argv = [
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

    profiler = cProfile.Profile()
    try:
        profiler.enable()
        try:
            runpy.run_module("data_validate.main", run_name="__main__")
        finally:
            profiler.disable()
    finally:
        sys.argv = argv_backup

    prof_path = report_dir / f"{input_dir.name}.prof"
    profiler.dump_stats(str(prof_path))

    stats_stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_stream).sort_stats("cumulative")
    stats.print_stats(top)

    text_path = report_dir / f"{input_dir.name}.top{top}.txt"
    text_path.write_text(stats_stream.getvalue(), encoding="utf-8")

    return prof_path


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(description="Profile a full data_validate CLI run with cProfile.")
    parser.add_argument(
        "--fixture",
        default=_DEFAULT_FIXTURE,
        help=f"Fixture name under data/input/, or a path to an input folder (default: {_DEFAULT_FIXTURE}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_REPO_ROOT / "dev-reports" / "profile",
        help="Directory to write the .prof file and top-N text report into (default: dev-reports/profile).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=_DEFAULT_TOP_N,
        help="Number of functions to list in the cumulative-time report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: profile the requested fixture.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 on success, 2 if the fixture folder does not exist.
    """
    args = build_parser().parse_args(argv)
    input_dir = _resolve_input_dir(args.fixture)
    if not input_dir.is_dir():
        print(f"fixture input folder not found: {input_dir}", file=sys.stderr)
        return 2

    output_dir = args.out / "_run_output" / input_dir.name
    prof_path = profile_pipeline(input_dir, output_dir, args.out, args.top)
    print(f"Wrote profile: {prof_path}")
    print(f"Wrote top-{args.top} report: {prof_path.with_suffix('')}.top{args.top}.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
