#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Run the `data_validate` CLI against every fixture folder in an input directory.

Replaces `tools/legacy/run_main_pipeline.sh`/`.bat`: same behaviour (run the CLI once per
fixture folder with the platform's standard flags, write each fixture's report under a matching
output subfolder), but as a portable, testable Python script with a summary table and no reliance
on a POSIX shell. Used by `make run-all`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_JSON_SUMMARY_RE = re.compile(r"<(\{.*\})>", re.DOTALL)


@dataclass(frozen=True)
class FixtureRun:
    """Result of running the CLI against one fixture folder.

    Attributes:
        fixture: Name of the fixture folder.
        exit_code: Process exit code returned by the CLI.
        errors: Number of validation errors reported, or None if the summary could not be parsed.
        warnings: Number of validation warnings reported, or None if the summary could not be parsed.
        tests: Number of verifications executed, or None if the summary could not be parsed.
        duration_seconds: Wall-clock time the CLI process took.
        output_dir: Directory the CLI wrote its report into.
    """

    fixture: str
    exit_code: int
    errors: int | None
    warnings: int | None
    tests: int | None
    duration_seconds: float
    output_dir: Path


def _discover_fixtures(input_dir: Path) -> list[str]:
    """List every fixture subfolder of `input_dir`, sorted by name.

    Args:
        input_dir: Root folder containing one subfolder per fixture.

    Returns:
        list[str]: Sorted fixture folder names.
    """
    return sorted(entry.name for entry in input_dir.iterdir() if entry.is_dir())


def _parse_summary(stdout: str) -> tuple[int | None, int | None, int | None]:
    """Parse the `<{...}>` JSON summary fragment the CLI prints to stdout.

    Args:
        stdout: Captured stdout of the CLI process.

    Returns:
        tuple[int | None, int | None, int | None]: `(errors, warnings, tests)`, each `None` when
            the summary is missing or malformed.
    """
    match = _JSON_SUMMARY_RE.search(stdout)
    if match is None:
        return None, None, None
    try:
        summary = json.loads(match.group(1))
        report = summary["data_validate"]["report"]
        return report["errors"], report["warnings"], report["tests"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None, None, None


def run_fixture(input_dir: Path, output_dir: Path, fixture: str, locale: str) -> FixtureRun:
    """Run the CLI once against a single fixture folder.

    Args:
        input_dir: Root folder containing the fixture subfolders.
        output_dir: Root folder to write each fixture's report into.
        fixture: Name of the fixture subfolder to run.
        locale: Locale passed to the CLI (`pt_BR` or `en_US`).

    Returns:
        FixtureRun: The outcome of the run.
    """
    fixture_input = input_dir / fixture
    fixture_output = output_dir / fixture
    command = [
        sys.executable,
        "-m",
        "data_validate.main",
        "--input_folder",
        f"{fixture_input}/",
        "--output_folder",
        f"{fixture_output}/",
        "--locale",
        locale,
        "--no-time",
        "--no-version",
        "--sector",
        "Setor A",
        "--protocol",
        "Protocolo B",
        "--user",
        "Usuário C",
    ]

    start = time.monotonic()
    # The command list is built entirely from this function's own arguments/constants, never
    # from unsanitised external input, so the subprocess-injection risk S603 flags does not apply.
    result = subprocess.run(command, cwd=_REPO_ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    duration = time.monotonic() - start

    errors, warnings, tests = _parse_summary(result.stdout)
    return FixtureRun(fixture, result.returncode, errors, warnings, tests, duration, fixture_output)


def _format_cell(value: int | None) -> str:
    """Format an optional integer for the summary table.

    Args:
        value: The value to format, or None when unavailable.

    Returns:
        str: `"?"` when `value` is None, otherwise the value's string form.
    """
    return "?" if value is None else str(value)


def _print_summary_table(runs: list[FixtureRun]) -> None:
    """Print a fixed-width summary table of all runs.

    Args:
        runs: The fixture runs to summarise, in the order they ran.
    """
    header = f"{'fixture':<32}{'exit':>6}{'errors':>8}{'warnings':>10}{'tests':>8}{'seconds':>10}"
    print(header)
    print("-" * len(header))
    for run in runs:
        print(
            f"{run.fixture:<32}{run.exit_code:>6}"
            f"{_format_cell(run.errors):>8}"
            f"{_format_cell(run.warnings):>10}"
            f"{_format_cell(run.tests):>8}"
            f"{run.duration_seconds:>10.2f}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(
        description="Run the data_validate CLI against every fixture under an input folder.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=_REPO_ROOT / "data" / "input",
        help="Root folder containing fixture subfolders (default: data/input).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_REPO_ROOT / "data" / "output",
        help="Root folder to write each fixture's report into (default: data/output).",
    )
    parser.add_argument("--locale", default="pt_BR", choices=["pt_BR", "en_US"], help="Locale passed to the CLI.")
    parser.add_argument(
        "--fixtures",
        nargs="*",
        default=None,
        metavar="NAME",
        help="Specific fixture folder names to run (default: every folder under --input).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: run every requested fixture and print a summary table.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 if every fixture's CLI process exited 0, 1 if any failed, 2 on a setup error.
    """
    args = build_parser().parse_args(argv)
    input_dir: Path = args.input
    output_dir: Path = args.output

    if not input_dir.is_dir():
        print(f"input folder does not exist: {input_dir}", file=sys.stderr)
        return 2

    fixtures = args.fixtures if args.fixtures else _discover_fixtures(input_dir)
    if not fixtures:
        print(f"no fixtures found under {input_dir}", file=sys.stderr)
        return 1

    runs = [run_fixture(input_dir, output_dir, fixture, args.locale) for fixture in fixtures]
    _print_summary_table(runs)

    failed = [run for run in runs if run.exit_code != 0]
    if failed:
        failed_names = ", ".join(run.fixture for run in failed)
        print(f"\n{len(failed)} fixture(s) exited non-zero: {failed_names}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
