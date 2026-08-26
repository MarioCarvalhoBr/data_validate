#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Golden end-to-end harness.

Runs the real CLI (`python -m data_validate.main`) against every fixture
folder under `data/input/`, exactly as the AdaptaBrasil platform does, and
compares a normalised extract of the generated HTML report and stdout JSON
summary against a stored golden file (`tests/e2e/golden/<fixture>.json`).

See `.claude/skills/golden-harness/SKILL.md` for how to read a diff and how
to update a golden with a reviewed reason.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "e2e" / "golden"
_ACTUAL_DIR = _REPO_ROOT / "dev-reports" / "e2e"
_INPUT_DIR = _REPO_ROOT / "data" / "input"
_MESSAGES_PT_BR_PATH = _REPO_ROOT / "data_validate" / "static" / "locales" / "pt_BR" / "messages.json"
_JSON_SUMMARY_RE = re.compile(r"<(\{.*\})>", re.DOTALL)
_SUBPROCESS_TIMEOUT_SECONDS = 600
_VERSION_PLACEHOLDER = "<version>"
_OUTPUT_DIR_PLACEHOLDER = "<OUTPUT_DIR>"


def _spelling_section_title() -> str:
    """Return the pt_BR verification title for the spelling check.

    Loaded from the message catalog (keyed by `NamesEnum.SPELL.value`)
    instead of hardcoded, so a catalog wording change does not silently
    break the spell-skip normalisation.

    Returns:
        str: The localized verification title shown in the report.
    """
    catalog = json.loads(_MESSAGES_PT_BR_PATH.read_text(encoding="utf-8"))
    message: str = catalog["verification_name_spelling"]["message"]
    return message


_SPELL_SECTION_TITLE = _spelling_section_title()


def _spell_backend_available() -> bool:
    """Detect whether a working pt_BR hunspell dictionary is available via enchant.

    Returns:
        bool: True when `enchant` is importable and can load a `pt_BR`
            dictionary; False otherwise (module missing or no word list
            installed for the language).
    """
    if importlib.util.find_spec("enchant") is None:
        return False
    try:
        # Deferred, optional import: pyenchant is a system-dependent runtime extra (see
        # `.claude/skills/spreadsheet-protocol/SKILL.md`), not guaranteed to be installed, so it
        # cannot be imported unconditionally at module level without breaking test collection on
        # environments without it.
        import enchant  # type: ignore[import-untyped]  # noqa: PLC0415

        enchant.Dict("pt_BR")
    except Exception:
        return False
    return True


_SPELL_AVAILABLE = _spell_backend_available()


def _discover_fixtures() -> list[str]:
    """List every fixture folder under `data/input/`, sorted by name.

    Returns:
        list[str]: Sorted fixture directory names.
    """
    if not _INPUT_DIR.is_dir():
        return []
    return sorted(entry.name for entry in _INPUT_DIR.iterdir() if entry.is_dir())


class _ReportSectionParser(HTMLParser):
    """Extract per-verification error/warning messages from the report HTML.

    Walks the `<span>` markers emitted by
    `FileReportGenerator._format_messages_as_html`: a `text-primary` span
    starts a new verification section, and each following
    `text-danger-errors`/`text-orange-warning` span is one message that
    belongs to the most recently seen section title.
    """

    _TITLE_CLASS = "text-primary"
    _ERROR_CLASS = "text-danger-errors"
    _WARNING_CLASS = "text-orange-warning"

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: dict[str, dict[str, list[str]]] = {}
        self.section_order: list[str] = []
        self._active_class: str | None = None
        self._active_title: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "span":
            return
        self._active_class = dict(attrs).get("class")
        self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._active_class is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "span" or self._active_class is None:
            return

        text = "".join(self._buffer).strip()
        if self._active_class == self._TITLE_CLASS:
            self._active_title = text
            if text not in self.sections:
                self.sections[text] = {"errors": [], "warnings": []}
                self.section_order.append(text)
        elif self._active_class == self._ERROR_CLASS and self._active_title is not None:
            self.sections[self._active_title]["errors"].append(text)
        elif self._active_class == self._WARNING_CLASS and self._active_title is not None:
            self.sections[self._active_title]["warnings"].append(text)

        self._active_class = None
        self._buffer = []


def _run_cli(fixture_name: str, output_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run `data_validate.main` against a fixture, exactly as the platform does.

    Args:
        fixture_name: Name of the fixture folder under `data/input/`.
        output_dir: Isolated output directory (never the repo's `data/output/`).

    Returns:
        subprocess.CompletedProcess[str]: The completed process, with
            captured text stdout/stderr.
    """
    command = [
        sys.executable,
        "-m",
        "data_validate.main",
        "--input_folder",
        f"data/input/{fixture_name}/",
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
    # The command list is built entirely from this function's own parameters/constants, never
    # from unsanitised external input, so the subprocess-injection risk S603 flags does not apply.
    return subprocess.run(  # noqa: S603
        command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )


def _extract_json_summary(stdout: str) -> dict[str, Any]:
    """Parse the `<{...}>` JSON summary fragment out of the CLI's stdout.

    `FileReportGenerator._print_json_summary` prints
    `str(dict).replace("'", '"')`, which is valid JSON for the shapes this
    summary can take (string/int leaves only).

    Args:
        stdout: Full captured stdout of the CLI process.

    Returns:
        dict[str, Any]: The parsed summary.

    Raises:
        AssertionError: If no summary fragment is found in stdout.
    """
    match = _JSON_SUMMARY_RE.search(stdout)
    if match is None:
        raise AssertionError(f"no JSON summary fragment found in stdout:\n{stdout}")
    return json.loads(match.group(1))  # type: ignore[no-any-return]


def _normalize_text(text: str, *, output_dir: Path) -> str:
    """Replace machine-specific substrings with stable placeholders.

    Args:
        text: Raw extracted title or message text.
        output_dir: The isolated, per-run output directory whose absolute
            path must not leak into the golden file.

    Returns:
        str: The normalised text.
    """
    normalized = text.replace(str(output_dir), _OUTPUT_DIR_PLACEHOLDER)
    return normalized.replace(output_dir.as_posix(), _OUTPUT_DIR_PLACEHOLDER)


def _build_actual(
    fixture_name: str,
    result: subprocess.CompletedProcess[str],
    output_dir: Path,
    html_content: str,
) -> dict[str, Any]:
    """Build the normalised, comparable structure for one fixture run.

    Args:
        fixture_name: Name of the fixture folder under `data/input/`.
        result: The completed CLI process.
        output_dir: The isolated output directory used for this run.
        html_content: The generated report's HTML source.

    Returns:
        dict[str, Any]: The normalised structure, ready to compare against
            or write as a golden file.
    """
    parser = _ReportSectionParser()
    parser.feed(html_content)

    # Message order within a section is not guaranteed stable by the pipeline: at least
    # `value_validator.py` builds "missing required column" messages from a `set` difference,
    # so the order can change between process runs (Python's hash randomisation). Confirmed by
    # running this harness three times in a row against `data_errors_11` and observing the same
    # two messages swap position with no other change. Sorting here (not fixing the pipeline,
    # which is out of scope for this change) keeps the golden comparison deterministic without
    # masking a real content change (an added/removed/reworded message still shows as a diff).
    sections = {
        title: {
            "errors": sorted(_normalize_text(message, output_dir=output_dir) for message in data["errors"]),
            "warnings": sorted(_normalize_text(message, output_dir=output_dir) for message in data["warnings"]),
        }
        for title, data in parser.sections.items()
    }
    section_order = list(parser.section_order)

    spell_skipped = not _SPELL_AVAILABLE
    if spell_skipped:
        sections.pop(_SPELL_SECTION_TITLE, None)
        section_order = [title for title in section_order if title != _SPELL_SECTION_TITLE]

    summary = _extract_json_summary(result.stdout)
    data_validate_summary = summary.get("data_validate")
    if isinstance(data_validate_summary, dict) and "version" in data_validate_summary:
        # The version string embeds a per-commit serial number (see
        # data_validate/config/metadata_info.py); freezing it in the golden
        # would fail on every unrelated commit, so it is replaced with a
        # stable placeholder. The JSON shape (the key exists) is still
        # verified.
        data_validate_summary["version"] = _VERSION_PLACEHOLDER

    return {
        "exit_code": result.returncode,
        "fixture": fixture_name,
        "json_summary": summary,
        "section_order": section_order,
        "sections": sections,
        "spell_skipped": spell_skipped,
    }


def _golden_path(fixture_name: str) -> Path:
    """Return the golden file path for a fixture.

    Args:
        fixture_name: Name of the fixture folder under `data/input/`.

    Returns:
        Path: The golden JSON path.
    """
    return _GOLDEN_DIR / f"{fixture_name}.json"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write `data` as pretty, deterministic JSON.

    Args:
        path: Destination file path; parent directories are created.
        data: The JSON-serialisable structure to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize("fixture_name", _discover_fixtures())
def test_golden_report(fixture_name: str, tmp_path: Path, request: pytest.FixtureRequest) -> None:
    """Run the CLI against a fixture and compare its report to the stored golden.

    Args:
        fixture_name: Name of the fixture folder under `data/input/` (parametrised).
        tmp_path: pytest's per-test temporary directory, used as an isolated output root.
        request: Pytest request object, used to read the `--update-golden` option.
    """
    output_dir = tmp_path / fixture_name
    result = _run_cli(fixture_name, output_dir)
    assert result.returncode == 0, (
        f"CLI exited with code {result.returncode} for fixture {fixture_name!r}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    html_path = output_dir / f"{fixture_name}_report.html"
    assert html_path.is_file(), f"HTML report not found at {html_path}"

    if shutil.which("wkhtmltopdf"):
        pdf_path = output_dir / f"{fixture_name}_report.pdf"
        assert pdf_path.is_file(), f"PDF report not found at {pdf_path} (wkhtmltopdf is installed)"

    html_content = html_path.read_text(encoding="utf-8")
    actual = _build_actual(fixture_name, result, output_dir, html_content)

    golden_path = _golden_path(fixture_name)
    update_golden = bool(request.config.getoption("--update-golden"))

    if update_golden:
        _write_json(golden_path, actual)
        return

    if not golden_path.is_file():
        pytest.fail(f"no golden file for fixture {fixture_name!r} at {golden_path}; run `make harness-update` first.")

    expected = json.loads(golden_path.read_text(encoding="utf-8"))

    if actual != expected:
        actual_path = _ACTUAL_DIR / f"{fixture_name}.actual.json"
        _write_json(actual_path, actual)
        assert actual == expected, (
            f"golden mismatch for fixture {fixture_name!r}.\nActual output written to {actual_path} for inspection.\n"
            "See .claude/skills/golden-harness/SKILL.md before updating the golden."
        )
