#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Command-line entry point for `canoa-data-validate`.

Wires `DataArgs` (CLI parsing) into `GeneralContext` (dependency injection)
and `SpreadsheetProcessor` (the validation pipeline), then translates the
run's outcome into a process exit code and an optional `--json` summary
file, per the CLI contract (`.specs/api/cli-contract.md`, ADR-0005, SEC-008).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import data_validate
from data_validate.config.metadata_info import METADATA
from data_validate.controllers import GeneralContext, SpreadsheetProcessor
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.base import DataArgs


def _build_json_summary(validation_reports: ValidationReport) -> dict[str, Any]:
    """Build the machine-readable summary object written by `--json PATH`.

    Mirrors the shape `FileReportGenerator._print_json_summary` prints to
    stdout, so the `--json` file and the stdout `<{...}>` fragment always
    agree on content.

    Args:
        validation_reports: The completed run's aggregated report.

    Returns:
        dict[str, Any]: The summary object, ready to serialise as JSON.
    """
    return {
        "data_validate": {
            "version": METADATA.__version__,
            "report": {
                "errors": validation_reports.get_total_errors(),
                "warnings": validation_reports.get_total_warnings(),
                "tests": len(validation_reports),
            },
        }
    }


def _compute_exit_code(fail_on: str, total_errors: int, total_warnings: int) -> int:
    """Compute the process exit code from the `--fail-on` policy (SEC-008).

    Args:
        fail_on: One of `"error"`, `"warning"`, `"never"`.
        total_errors: Total validation errors found across the run.
        total_warnings: Total validation warnings found across the run.

    Returns:
        int: `0` when nothing at/above the configured severity was found (or
            `fail_on == "never"`), `1` otherwise.
    """
    if fail_on == "never":
        return 0
    if fail_on == "warning":
        return 1 if (total_errors > 0 or total_warnings > 0) else 0
    return 1 if total_errors > 0 else 0


def main() -> int:
    """Run the CLI end to end and return its process exit code.

    Returns:
        int: `0` on a clean run (no issues at/above `--fail-on`), `1` when
            validation found issues at/above `--fail-on`, `2` on an
            unexpected runtime failure (bad arguments, unreadable input, a
            crash inside the pipeline) — see SEC-008.
    """
    print(f"{data_validate.__welcome__}\n", file=sys.stderr)

    try:
        data_args = DataArgs()
        general_context = GeneralContext(data_args=data_args)
        processor = SpreadsheetProcessor(context=general_context)
        processor.run()
        general_context.finalize()
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 2

    total_errors = processor.validation_reports.get_total_errors()
    total_warnings = processor.validation_reports.get_total_warnings()

    if data_args.json_path:
        summary = _build_json_summary(processor.validation_reports)
        Path(data_args.json_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return _compute_exit_code(data_args.fail_on, total_errors, total_warnings)


if __name__ == "__main__":
    sys.exit(main())

# Example usage:
# python3 data_validate/main.py --output data/output/temp/ --input data/input/data_ground_truth_01/
