#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/engine/scanner.py
"""
Escaneia diretório de entrada e valida existência de arquivos.

BUG-018/ARC-003: the expected sheet stems and allowed extensions come from
`data_validate.specs.sheet_specs.SHEET_SPECS`/`ALLOWED_EXTENSIONS` (the single source of truth),
not from the deleted `data_loader.common.config.Config` singleton.

BUG-015: conflict policy is explicit and documented here, not just implied by which key wins.
When both a `.csv` and a `.xlsx` file exist for the same stem, `.csv` is preferred (matching the
pt-BR message `FileStructureValidator` already reports for the same situation, STRUCT-006); the
losing path is not silently dropped -- it is returned in `ignored` so a caller can inspect or log
it. `scan()` does not raise or record an error itself for a conflict; that remains
`FileStructureValidator.check_ignored_files_in_folder_root`'s job.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from data_validate.specs.sheet_specs import ALLOWED_EXTENSIONS, SHEET_SPECS, SheetSpec


class FileScanner:
    """Scans an input folder for the sheets declared in `SHEET_SPECS`.

    Args:
        directory: Folder to scan.
        sheet_specs: Mapping of sheet name to `SheetSpec`, defaults to the registry.
        extensions: Allowed file extensions, defaults to the registry's `ALLOWED_EXTENSIONS`.
    """

    def __init__(
        self,
        directory: Path,
        sheet_specs: Mapping[str, SheetSpec] = SHEET_SPECS,
        extensions: tuple[str, ...] = ALLOWED_EXTENSIONS,
    ):
        self.dir = directory
        self.sheet_specs = sheet_specs
        self.extensions = extensions

    def scan(self) -> tuple[dict[str, Path], dict[str, Path], list[str]]:
        """Scan `self.dir` for the sheets declared in `self.sheet_specs`.

        Returns:
            A `(found, ignored, missing)` tuple: `found` maps sheet name to the chosen path;
            `ignored` maps sheet name to a path that lost the CSV-over-XLSX conflict (present only
            when both extensions were delivered for the same stem); `missing` lists required sheet
            names with no matching file at all.
        """
        found: dict[str, Path] = {}
        ignored: dict[str, Path] = {}
        for f in self.dir.iterdir():
            base, ext = f.stem, f.suffix.lower()
            if base not in self.sheet_specs or ext not in self.extensions:
                continue
            if base not in found:
                found[base] = f
                continue
            if found[base].suffix == ".csv":
                # CSV already chosen for this stem; any other file for it loses.
                ignored[base] = f
            elif ext == ".csv":
                # A CSV arrives after a non-CSV was already found; CSV wins.
                ignored[base] = found[base]
                found[base] = f
            else:
                # Neither the existing nor the new file is CSV; keep the first, ignore the new one.
                ignored[base] = f

        missing = [name for name, spec in self.sheet_specs.items() if spec.required and name not in found]

        return found, ignored, missing
