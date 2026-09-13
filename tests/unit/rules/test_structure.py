#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.structure` (ARC-017 Phase 3b, STRUCT-001…006).

Table-driven coverage per rule (pass, each failure mode, the STRUCT-002 short-circuit, boundary
cases) plus registry-shape checks. Every test builds real directories/files under `tmp_path` and a
`RuleContext` directly — no engine, no mocks (`.claude/rules/testing.md`).

Rewrites `tests/unit/validators/structure/test_file_structure_validator.py` (deleted): the legacy
suite exercised `FileStructureValidator`'s `__init__`-runs-`run()` pattern (ARC-001) through a
heavily `MagicMock`ed `DataModelContext`; every scenario it covered is reproduced here against the
pure `check_*` functions instead. Dropped, not reproduced: `TestFileStructureValidatorInstanceState`
(BUG-026's "no duplicate `errors`/`warnings` instance attributes" and "`validate_all_general_structure`
is idempotent" regressions) — both were about `FileStructureValidator`'s own mutable instance state,
which no longer exists now that each check is a pure function with no instance to duplicate state
on or re-invoke.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.structure import (
    STRUCTURE_REGISTRY,
    check_files_not_zipped_inside_a_folder,
    check_input_directory_not_empty,
    check_no_csv_xlsx_conflict,
    check_no_unexpected_files,
    check_no_unexpected_folders,
    check_required_files_present,
)
from data_validate.specs.issues import Severity


def _make_context(input_folder: Path, dir_entries: tuple[str, ...] | None = None) -> RuleContext:
    """Build a `RuleContext` pointed at a real `input_folder`.

    Args:
        input_folder: A real, on-disk directory the rule under test will stat.
        dir_entries: Entry names to declare in `options["dir_entries"]`; defaults to the
            directory's actual listing (sorted, for deterministic test assertions).
    """
    entries = dir_entries if dir_entries is not None else tuple(sorted(p.name for p in input_folder.iterdir()))
    return RuleContext(
        sheets={},
        cleaned={},
        options={"input_folder": input_folder, "dir_entries": entries},
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestStructureRegistryShape:
    """The registry declares exactly the STRUCT ids the legacy validator implemented."""

    def test_registry_contains_every_ported_struct_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in STRUCTURE_REGISTRY] == [
            "STRUCT-001",
            "STRUCT-002",
            "STRUCT-003",
            "STRUCT-004",
            "STRUCT-005",
            "STRUCT-006",
        ]

    def test_every_spec_reports_under_the_file_structure_category(self) -> None:
        assert all(spec.category == NamesEnum.FS.value for spec in STRUCTURE_REGISTRY)

    def test_topological_order_keeps_registration_order(self) -> None:
        # No rule declares depends_on: the STRUCT-002 short-circuit is handled inside
        # STRUCT-003/STRUCT-004's own check functions, not via the engine's dependency skip.
        assert STRUCTURE_REGISTRY.topological_order() == (
            "STRUCT-001",
            "STRUCT-002",
            "STRUCT-003",
            "STRUCT-004",
            "STRUCT-005",
            "STRUCT-006",
        )


class TestCheckInputDirectoryNotEmpty:
    """STRUCT-001: the input directory must contain at least one entry."""

    def test_empty_directory_reports_an_error(self, tmp_path: Path) -> None:
        ctx = _make_context(tmp_path, dir_entries=())

        issues = check_input_directory_not_empty(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "STRUCT-001"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.FS.value
        assert issue.message_key == "validator_structure_error_empty_directory"
        assert issue.params == {"dir_path": str(tmp_path)}

    def test_non_empty_directory_reports_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_input_directory_not_empty(ctx) == []

    def test_a_non_iterable_dir_entries_option_is_treated_as_empty(self, tmp_path: Path) -> None:
        """Defensive branch: a malformed `options["dir_entries"]` reads as no entries at all."""
        ctx = RuleContext(
            sheets={},
            cleaned={},
            options={"input_folder": tmp_path, "dir_entries": None},
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        issues = check_input_directory_not_empty(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "validator_structure_error_empty_directory"


class TestCheckFilesNotZippedInsideAFolder:
    """STRUCT-002: a single subfolder entry means the bundle was zipped with an extra level."""

    def test_single_subfolder_entry_reports_an_error(self, tmp_path: Path) -> None:
        (tmp_path / "inner").mkdir()
        ctx = _make_context(tmp_path)

        issues = check_files_not_zipped_inside_a_folder(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "STRUCT-002"
        assert issue.message_key == "validator_structure_error_files_not_in_folder"
        assert issue.params == {}

    def test_single_file_entry_reports_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_files_not_zipped_inside_a_folder(ctx) == []

    def test_multiple_entries_report_nothing_even_if_one_is_a_folder(self, tmp_path: Path) -> None:
        (tmp_path / "inner").mkdir()
        (tmp_path / "descricao.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_files_not_zipped_inside_a_folder(ctx) == []

    def test_empty_directory_reports_nothing(self, tmp_path: Path) -> None:
        ctx = _make_context(tmp_path, dir_entries=())

        assert check_files_not_zipped_inside_a_folder(ctx) == []


class TestCheckNoUnexpectedFolders:
    """STRUCT-003: every entry in the root must be a regular file, not a folder."""

    def test_a_folder_in_the_root_reports_an_error(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "unexpected_folder").mkdir()
        ctx = _make_context(tmp_path)

        issues = check_no_unexpected_folders(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "STRUCT-003"
        assert issue.message_key == "validator_structure_error_unexpected_folder"
        assert issue.params == {"file_name": "unexpected_folder"}

    def test_only_files_reports_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_folders(ctx) == []

    def test_the_struct_002_short_circuit_suppresses_this_check(self, tmp_path: Path) -> None:
        """A single subfolder entry is reported once as STRUCT-002, never also as STRUCT-003."""
        (tmp_path / "inner").mkdir()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_folders(ctx) == []


class TestCheckNoUnexpectedFiles:
    """STRUCT-004: every file must be `<base>.<ext>` with `<base>` a known sheet stem."""

    def test_an_unknown_file_reports_an_error(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "arquivo_aleatorio.xlsx").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_unexpected_files(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "STRUCT-004"
        assert issue.message_key == "validator_structure_error_unexpected_file"
        assert issue.params == {"file_name": "arquivo_aleatorio.xlsx"}

    def test_a_qml_file_reports_an_error(self, tmp_path: Path) -> None:
        """The loader no longer scans `.qml`, but the directory listing still flags it (BUG-015)."""
        (tmp_path / "legenda.qml").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_unexpected_files(ctx)

        assert issues[0].params == {"file_name": "legenda.qml"}

    def test_a_case_mismatched_expected_file_reports_an_error(self, tmp_path: Path) -> None:
        """Matching is case-sensitive: `Descricao.xlsx` is not `descricao.xlsx`."""
        (tmp_path / "Descricao.xlsx").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_unexpected_files(ctx)

        assert issues[0].params == {"file_name": "Descricao.xlsx"}

    def test_every_expected_and_optional_stem_reports_nothing(self, tmp_path: Path) -> None:
        for stem in ("descricao", "composicao", "valores", "referencia_temporal"):
            (tmp_path / f"{stem}.csv").touch()
        for stem in ("proporcionalidades", "cenarios", "legenda", "dicionario"):
            (tmp_path / f"{stem}.xlsx").touch()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_files(ctx) == []

    def test_the_struct_002_short_circuit_suppresses_this_check(self, tmp_path: Path) -> None:
        (tmp_path / "inner").mkdir()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_files(ctx) == []

    def test_a_folder_entry_is_skipped_not_reported_as_an_unexpected_file(self, tmp_path: Path) -> None:
        """A folder is STRUCT-003's concern; STRUCT-004 only inspects regular files."""
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "some_folder").mkdir()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_files(ctx) == []

    def test_the_territory_registry_file_is_whitelisted(self, tmp_path: Path) -> None:
        """PROTO-013: `spd_data.json` is accepted even though it is not a declared sheet."""
        (tmp_path / "spd_data.json").touch()
        ctx = _make_context(tmp_path)

        assert check_no_unexpected_files(ctx) == []

    def test_a_similarly_named_file_is_still_rejected(self, tmp_path: Path) -> None:
        """Only the exact `spd_data.json` name is whitelisted, not a lookalike."""
        (tmp_path / "spd_data.xlsx").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_unexpected_files(ctx)

        assert issues[0].params == {"file_name": "spd_data.xlsx"}


class TestCheckRequiredFilesPresent:
    """STRUCT-005: descricao/composicao/valores/referencia_temporal must each exist."""

    def test_all_four_required_files_present_reports_nothing(self, tmp_path: Path) -> None:
        for stem in ("descricao", "composicao", "valores", "referencia_temporal"):
            (tmp_path / f"{stem}.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_required_files_present(ctx) == []

    def test_missing_required_files_are_each_reported_in_sheet_specs_order(self, tmp_path: Path) -> None:
        (tmp_path / "composicao.csv").touch()
        ctx = _make_context(tmp_path)

        issues = check_required_files_present(ctx)

        assert [issue.params["file_base"] for issue in issues] == [
            "descricao",
            "valores",
            "referencia_temporal",
        ]
        assert all(issue.rule_id == "STRUCT-005" for issue in issues)
        assert all(issue.message_key == "validator_structure_error_missing_file" for issue in issues)

    def test_either_allowed_extension_satisfies_the_requirement(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.xlsx").touch()
        (tmp_path / "composicao.csv").touch()
        (tmp_path / "valores.csv").touch()
        (tmp_path / "referencia_temporal.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_required_files_present(ctx) == []

    def test_optional_files_are_never_reported_as_missing(self, tmp_path: Path) -> None:
        for stem in ("descricao", "composicao", "valores", "referencia_temporal"):
            (tmp_path / f"{stem}.csv").touch()
        ctx = _make_context(tmp_path)

        issues = check_required_files_present(ctx)
        assert not any(issue.params["file_base"] == "legenda" for issue in issues)


class TestCheckNoCsvXlsxConflict:
    """STRUCT-006: a sheet must not be delivered as both `.csv` and `.xlsx`."""

    def test_both_extensions_present_reports_a_conflict(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        (tmp_path / "descricao.xlsx").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_csv_xlsx_conflict(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "STRUCT-006"
        assert issue.message_key == "validator_structure_error_conflicting_files"
        assert issue.params == {"file_base": "descricao"}

    def test_a_single_extension_reports_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "descricao.csv").touch()
        ctx = _make_context(tmp_path)

        assert check_no_csv_xlsx_conflict(ctx) == []

    def test_an_unrelated_extension_pair_reports_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").touch()
        (tmp_path / "notes.md").touch()
        ctx = _make_context(tmp_path)

        assert check_no_csv_xlsx_conflict(ctx) == []

    def test_an_unexpected_stem_conflict_is_still_reported(self, tmp_path: Path) -> None:
        """STRUCT-006 does not consult SHEET_SPECS: any base counts, expected or not."""
        (tmp_path / "arquivo_aleatorio.csv").touch()
        (tmp_path / "arquivo_aleatorio.xlsx").touch()
        ctx = _make_context(tmp_path)

        issues = check_no_csv_xlsx_conflict(ctx)
        assert issues[0].params == {"file_base": "arquivo_aleatorio"}


class TestEmptyDirectoryCombinedBehaviour:
    """An empty directory reports itself empty and every required file missing, nothing else."""

    def test_empty_directory_reports_expected_combination(self, tmp_path: Path) -> None:
        ctx = _make_context(tmp_path, dir_entries=())

        assert [issue.rule_id for issue in check_input_directory_not_empty(ctx)] == ["STRUCT-001"]
        assert check_files_not_zipped_inside_a_folder(ctx) == []
        assert check_no_unexpected_folders(ctx) == []
        assert check_no_unexpected_files(ctx) == []
        assert [issue.params["file_base"] for issue in check_required_files_present(ctx)] == [
            "descricao",
            "composicao",
            "valores",
            "referencia_temporal",
        ]
        assert check_no_csv_xlsx_conflict(ctx) == []


@pytest.mark.parametrize(
    "rule_id",
    ["STRUCT-001", "STRUCT-002", "STRUCT-003", "STRUCT-004", "STRUCT-005", "STRUCT-006"],
)
def test_every_ported_rule_is_registered(rule_id: str) -> None:
    assert STRUCTURE_REGISTRY.get(rule_id) is not None
