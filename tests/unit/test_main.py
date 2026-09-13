#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.main` (ARC-011/SEC-008/ARC-012).

`SpreadsheetProcessor` and `GeneralContext` do real I/O and are mocked at the
`data_validate.main` namespace boundary; `DataArgs` is mocked for the exit-code
and `--json` scenarios (its own parsing is covered by
`tests/unit/helpers/base/test_data_args.py`) and left real only for the
deprecated-alias scenario, which needs actual argument parsing.
"""

from __future__ import annotations

import json


from data_validate import main as main_module


def _mock_run(
    mocker,
    *,
    errors: int = 0,
    warnings: int = 0,
    tests: int = 34,
    fail_on: str = "error",
    json_path: str | None = None,
    spatial_data_validated: bool = False,
):
    """Patch `DataArgs`/`GeneralContext`/`SpreadsheetProcessor` for a scripted run.

    Args:
        mocker: The `pytest-mock` fixture.
        errors: Total errors the mocked `validation_reports` should report.
        warnings: Total warnings the mocked `validation_reports` should report.
        tests: Number of verification categories the mocked run should report.
        fail_on: Value assigned to `data_args.fail_on`.
        json_path: Value assigned to `data_args.json_path`.
        spatial_data_validated: PROTO-018 — value assigned to the mocked
            `GeneralContext.spatial_data_validated`, read by `_build_json_summary`. A real `bool`
            (not the default `MagicMock` attribute), since it must serialise as JSON.

    Returns:
        tuple: The mocked `DataArgs` instance and the mocked `SpreadsheetProcessor` class.
    """
    mock_data_args_cls = mocker.patch("data_validate.main.DataArgs")
    mock_data_args = mock_data_args_cls.return_value
    mock_data_args.fail_on = fail_on
    mock_data_args.json_path = json_path

    mock_general_context_cls = mocker.patch("data_validate.main.GeneralContext")
    mock_general_context_cls.return_value.spatial_data_validated = spatial_data_validated

    mock_validation_reports = mocker.MagicMock()
    mock_validation_reports.get_total_errors.return_value = errors
    mock_validation_reports.get_total_warnings.return_value = warnings
    mock_validation_reports.__len__.return_value = tests

    mock_processor_cls = mocker.patch("data_validate.main.SpreadsheetProcessor")
    mock_processor_cls.return_value.validation_reports = mock_validation_reports

    return mock_data_args, mock_processor_cls


class TestMainExitCodes:
    """Exit-code contract: 0 clean, 1 issues at/above `--fail-on`, 2 a crash (SEC-008)."""

    def test_main_clean_run_returns_zero(self, mocker) -> None:
        """No errors, no warnings, default `--fail-on error` -> exit 0."""
        _mock_run(mocker, errors=0, warnings=0)

        assert main_module.main() == 0

    def test_main_errors_return_one(self, mocker) -> None:
        """Any error, default `--fail-on error` -> exit 1."""
        _mock_run(mocker, errors=3, warnings=0)

        assert main_module.main() == 1

    def test_main_fail_on_warning_with_only_warnings_returns_one(self, mocker) -> None:
        """`--fail-on warning` with warnings but no errors still fails the run."""
        _mock_run(mocker, errors=0, warnings=2, fail_on="warning")

        assert main_module.main() == 1

    def test_main_fail_on_never_with_errors_returns_zero(self, mocker) -> None:
        """`--fail-on never` restores the historical always-0 behaviour."""
        _mock_run(mocker, errors=5, warnings=1, fail_on="never")

        assert main_module.main() == 0

    def test_main_processor_raises_returns_two_and_logs_fatal_error(self, mocker, capsys) -> None:
        """An unexpected crash inside the pipeline -> exit 2, `Fatal error: ...` on stderr."""
        mocker.patch("data_validate.main.DataArgs")
        mocker.patch("data_validate.main.GeneralContext")
        mocker.patch("data_validate.main.SpreadsheetProcessor", side_effect=RuntimeError("boom"))

        exit_code = main_module.main()

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "Fatal error: boom" in captured.err


class TestMainJsonOutput:
    """`--json PATH` writes the same summary object as the stdout fragment."""

    def test_main_json_flag_writes_parseable_summary(self, mocker, tmp_path) -> None:
        json_path = tmp_path / "summary.json"
        _mock_run(mocker, errors=1, warnings=2, tests=34, json_path=str(json_path))

        exit_code = main_module.main()

        assert exit_code == 1
        written = json.loads(json_path.read_text(encoding="utf-8"))
        assert written["data_validate"]["report"] == {"errors": 1, "warnings": 2, "tests": 34}

    def test_main_json_flag_carries_spatial_data_validated_true(self, mocker, tmp_path) -> None:
        """PROTO-018: the `--json` file mirrors `GeneralContext.spatial_data_validated`."""
        json_path = tmp_path / "summary.json"
        _mock_run(mocker, json_path=str(json_path), spatial_data_validated=True)

        main_module.main()

        written = json.loads(json_path.read_text(encoding="utf-8"))
        assert written["data_validate"]["spatial_data_validated"] is True

    def test_main_json_flag_carries_spatial_data_validated_false(self, mocker, tmp_path) -> None:
        """PROTO-018: `False` (the default -- absent/malformed registry, or TERR errors) too."""
        json_path = tmp_path / "summary.json"
        _mock_run(mocker, json_path=str(json_path), spatial_data_validated=False)

        main_module.main()

        written = json.loads(json_path.read_text(encoding="utf-8"))
        assert written["data_validate"]["spatial_data_validated"] is False

    def test_main_without_json_flag_writes_no_file(self, mocker, tmp_path) -> None:
        json_path = tmp_path / "summary.json"
        _mock_run(mocker, errors=0, warnings=0, json_path=None)

        main_module.main()

        assert not json_path.exists()


class TestMainWelcomeBanner:
    """ARC-012: the welcome banner moved off stdout (import time) onto stderr (`main()`)."""

    def test_main_prints_welcome_banner_to_stderr_not_stdout(self, mocker, capsys) -> None:
        _mock_run(mocker)

        main_module.main()

        captured = capsys.readouterr()
        assert main_module.data_validate.__welcome__ in captured.err
        assert main_module.data_validate.__welcome__ not in captured.out


class TestMainDeprecatedAlias:
    """A deprecated two-dash alias still works but warns once, naming the replacement."""

    def test_main_deprecated_input_alias_warns_on_stderr(self, mocker, tmp_path, capsys) -> None:
        input_dir = tmp_path / "in"
        input_dir.mkdir()
        mocker.patch("sys.argv", ["prog", "--i", str(input_dir), "--fail-on", "never"])

        mocker.patch("data_validate.main.GeneralContext")
        mock_validation_reports = mocker.MagicMock()
        mock_validation_reports.get_total_errors.return_value = 0
        mock_validation_reports.get_total_warnings.return_value = 0
        mock_validation_reports.__len__.return_value = 34
        mocker.patch(
            "data_validate.main.SpreadsheetProcessor"
        ).return_value.validation_reports = mock_validation_reports

        exit_code = main_module.main()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "'--i' is deprecated" in captured.err
