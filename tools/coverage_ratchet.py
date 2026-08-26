#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Enforce the coverage ratchet: coverage may go up, never meaningfully down.

Reads the `line-rate` attribute from a Cobertura `coverage.xml` report (written by `make
coverage`), compares it against the stored baseline in `tools/coverage_baseline.txt`, and fails
when it dropped by more than a small tolerance. `--update` raises the baseline when the current
run is higher — never lowers it. See `.specs/quality/testing-strategy.md` (Coverage section).
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET  # nosec B405 - see justification on the ET.parse() call below
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_COVERAGE_XML = _REPO_ROOT / "dev-reports" / "coverage.xml"
_DEFAULT_BASELINE_PATH = _REPO_ROOT / "tools" / "coverage_baseline.txt"
_DEFAULT_TOLERANCE_PP = 0.05


def _read_line_rate_percent(coverage_xml: Path) -> float:
    """Read the overall line coverage percentage from a Cobertura XML report.

    Args:
        coverage_xml: Path to the `coverage.xml` file.

    Returns:
        float: Line coverage as a percentage (0-100).

    Raises:
        FileNotFoundError: If `coverage_xml` does not exist.
        ValueError: If the file has no `line-rate` attribute on its root element.
    """
    if not coverage_xml.is_file():
        raise FileNotFoundError(f"coverage report not found: {coverage_xml} (run `make coverage` first)")

    # coverage.xml is a build artefact this repo's own `make coverage` just generated locally, not
    # externally-sourced/untrusted data, so the stdlib parser's XXE risk (S314) does not apply here;
    # `defusedxml` is not a project dependency, and adding one is out of scope for this script.
    root = ET.parse(coverage_xml).getroot()  # noqa: S314 # nosec B314
    line_rate = root.get("line-rate")
    if line_rate is None:
        raise ValueError(f"no line-rate attribute found on the root element of {coverage_xml}")
    return float(line_rate) * 100.0


def _read_baseline(baseline_path: Path) -> float:
    """Read the stored baseline percentage.

    Args:
        baseline_path: Path to the baseline file (a single float, in percent).

    Returns:
        float: The baseline coverage percentage.

    Raises:
        FileNotFoundError: If `baseline_path` does not exist.
    """
    if not baseline_path.is_file():
        raise FileNotFoundError(f"coverage baseline not found: {baseline_path}")
    return float(baseline_path.read_text(encoding="utf-8").strip())


def _write_baseline(baseline_path: Path, value: float) -> None:
    """Write a new baseline percentage.

    Args:
        baseline_path: Path to the baseline file.
        value: The new baseline percentage to store.
    """
    baseline_path.write_text(f"{value:.2f}\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(description="Compare the latest coverage run against the stored ratchet baseline.")
    parser.add_argument(
        "--coverage-xml",
        type=Path,
        default=_DEFAULT_COVERAGE_XML,
        help="Path to the Cobertura coverage.xml report.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=_DEFAULT_BASELINE_PATH,
        help="Path to the stored baseline percentage file.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=_DEFAULT_TOLERANCE_PP,
        help="Allowed drop, in percentage points, before failing.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Write the new baseline when the current run is higher than the stored one.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: compare current coverage against the baseline.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 on pass (or successful update), 1 if coverage dropped beyond tolerance, 2 on a
            setup error (missing report/baseline).
    """
    args = build_parser().parse_args(argv)

    try:
        current = _read_line_rate_percent(args.coverage_xml)
        baseline = _read_baseline(args.baseline)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Coverage: {current:.2f}% (baseline: {baseline:.2f}%)")

    if current < baseline - args.tolerance:
        drop = baseline - current
        message = f"FAILED: coverage dropped by {drop:.2f} pp, more than the {args.tolerance:.2f} pp tolerance."
        print(message, file=sys.stderr)
        return 1

    if args.update and current > baseline:
        _write_baseline(args.baseline, current)
        print(f"Updated baseline: {baseline:.2f}% -> {current:.2f}%")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
