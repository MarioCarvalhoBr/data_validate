#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""STRUCT-001…006: the input-folder structural checks (ARC-017 Phase 3b, ADR-0006).

Ports `validators/structure/file_structure_validator.py::FileStructureValidator`'s four checks
(empty directory, unexpected files/folders, missing required files, csv/xlsx conflict) onto the
`rules` engine, one `RuleSpec` per `STRUCT-*` id documented in
`.specs/business-rules/file-structure.md`. Every emitted `Issue.message_key` is one of the
existing `validator_structure_error_*` catalog keys (`.claude/rules/i18n.md`: a rule never invents
a message, it renders through `ctx.translate`); no new catalog key was needed for this port.

Only the checks the legacy validator actually implements are ported here. `STRUCT-007`…`STRUCT-012`
and `STRUCT-015` are implemented elsewhere (the loader, `SpModelABC`, `DataFrameProcessing` — see
the spec) and are out of this module's scope; `STRUCT-013`/`STRUCT-014` are PROTO-007/PROTO-003,
not yet implemented anywhere.

Purity note: a rule here still performs read-only `Path.is_file()`/`Path.is_dir()` stat calls
against `ctx.options["input_folder"]` for the names listed in `ctx.options["dir_entries"]` — it
never lists a directory itself (`os.listdir`/`Path.iterdir()`), only the caller
(`SpreadsheetProcessor`) does that, once, before building the `RuleContext`. This keeps a rule
deterministic given its `RuleContext` (the same `dir_entries` + the same on-disk entries always
produce the same issues) without requiring the caller to precompute an entry-kind map the legacy
behaviour never needed. Rule tests build real directories under `tmp_path` accordingly.

Depends only on `data_validate.rules`/`data_validate.specs` and the standard library, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity
from data_validate.specs.sheet_specs import ALLOWED_EXTENSIONS, SHEET_SPECS

STRUCTURE_REGISTRY = RuleRegistry()
"""Every `STRUCT-*` rule ported from `FileStructureValidator`, in the legacy check order."""

_CATEGORY = NamesEnum.FS.value
"""Report bucket every structural issue belongs to (`verification_name_file_structure`)."""


def _input_folder(ctx: RuleContext) -> Path:
    """Return `ctx.options["input_folder"]` as a `Path`."""
    return Path(str(ctx.options["input_folder"]))


def _dir_entries(ctx: RuleContext) -> tuple[str, ...]:
    """Return `ctx.options["dir_entries"]` (the input folder's entry names) as a tuple."""
    entries = ctx.options.get("dir_entries", ())
    if not isinstance(entries, Iterable):
        return ()
    return tuple(str(entry) for entry in entries)


def _is_zipped_with_extra_folder(ctx: RuleContext) -> bool:
    """Whether the bundle was delivered as a single subfolder (STRUCT-002's condition).

    Matches `FileStructureValidator.check_not_expected_files_in_folder_root`'s early-return
    branch: true only when the input folder contains exactly one entry and that entry is itself
    a directory.
    """
    entries = _dir_entries(ctx)
    if len(entries) != 1:
        return False
    return (_input_folder(ctx) / entries[0]).is_dir()


def _issue(rule_id: str, message_key: str, params: Mapping[str, object]) -> Issue:
    """Build a folder-level (no sheet/row/column) error `Issue` for a structure rule."""
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=None,
        row=None,
        column=None,
        message_key=message_key,
        params=params,
        category=_CATEGORY,
    )


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-001", category=_CATEGORY)
def check_input_directory_not_empty(ctx: RuleContext) -> list[Issue]:
    """STRUCT-001: the input directory must contain at least one entry."""
    if _dir_entries(ctx):
        return []
    return [
        _issue(
            "STRUCT-001",
            "validator_structure_error_empty_directory",
            {"dir_path": str(_input_folder(ctx))},
        )
    ]


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-002", category=_CATEGORY)
def check_files_not_zipped_inside_a_folder(ctx: RuleContext) -> list[Issue]:
    """STRUCT-002: files must be in the root, not inside a single subfolder."""
    if not _is_zipped_with_extra_folder(ctx):
        return []
    return [_issue("STRUCT-002", "validator_structure_error_files_not_in_folder", {})]


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-003", category=_CATEGORY)
def check_no_unexpected_folders(ctx: RuleContext) -> list[Issue]:
    """STRUCT-003: every entry in the root must be a regular file, not a folder.

    Skipped entirely when STRUCT-002's zipped-subfolder condition holds — the legacy
    `check_not_expected_files_in_folder_root` returns immediately in that case, so the single
    subfolder entry is reported once (as STRUCT-002), never twice.
    """
    if _is_zipped_with_extra_folder(ctx):
        return []

    input_folder = _input_folder(ctx)
    issues: list[Issue] = []
    for entry_name in _dir_entries(ctx):
        if not (input_folder / entry_name).is_file():
            issues.append(
                _issue("STRUCT-003", "validator_structure_error_unexpected_folder", {"file_name": entry_name})
            )
    return issues


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-004", category=_CATEGORY)
def check_no_unexpected_files(ctx: RuleContext) -> list[Issue]:
    """STRUCT-004: every file must be `<base>.<ext>` with `<base>` a known sheet stem.

    Same zipped-subfolder short-circuit as STRUCT-003 (see its docstring).
    """
    if _is_zipped_with_extra_folder(ctx):
        return []

    input_folder = _input_folder(ctx)
    issues: list[Issue] = []
    for entry_name in _dir_entries(ctx):
        entry_path = input_folder / entry_name
        if not entry_path.is_file():
            continue
        file_base, file_ext = os.path.splitext(entry_name)
        if file_base in SHEET_SPECS and file_ext in ALLOWED_EXTENSIONS:
            continue
        issues.append(_issue("STRUCT-004", "validator_structure_error_unexpected_file", {"file_name": entry_name}))
    return issues


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-005", category=_CATEGORY)
def check_required_files_present(ctx: RuleContext) -> list[Issue]:
    """STRUCT-005: `descricao`, `composicao`, `valores`, `referencia_temporal` must each exist."""
    input_folder = _input_folder(ctx)
    issues: list[Issue] = []
    for name, spec in SHEET_SPECS.items():
        if not spec.required:
            continue
        file_found = any((input_folder / candidate).is_file() for candidate in spec.filename_candidates)
        if not file_found:
            issues.append(_issue("STRUCT-005", "validator_structure_error_missing_file", {"file_base": name}))
    return issues


@STRUCTURE_REGISTRY.rule(rule_id="STRUCT-006", category=_CATEGORY)
def check_no_csv_xlsx_conflict(ctx: RuleContext) -> list[Issue]:
    """STRUCT-006: a sheet must not be delivered as both `.csv` and `.xlsx`."""
    extensions_by_base: dict[str, set[str]] = {}
    for entry_name in _dir_entries(ctx):
        file_base, file_ext = os.path.splitext(entry_name)
        if file_ext in ALLOWED_EXTENSIONS:
            extensions_by_base.setdefault(file_base, set()).add(file_ext)

    issues: list[Issue] = []
    for file_base, extensions in extensions_by_base.items():
        if ".csv" in extensions and ".xlsx" in extensions:
            issues.append(_issue("STRUCT-006", "validator_structure_error_conflicting_files", {"file_base": file_base}))
    return issues
