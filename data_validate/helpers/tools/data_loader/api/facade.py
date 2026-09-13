#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/facade.py
"""Facade to load all expected spreadsheet files from a bundle.

ARC-009/ARC-003: `DataLoaderFacade.load()` is a real method (no I/O in a property) that returns a
`LoadResult`; header layout, CSV separator and the required/optional flag all come from
`data_validate.specs.sheet_specs.SHEET_SPECS`, the single source of truth (ADR-0003) -- the facade
no longer imports the deleted `data_loader.common.config.Config` singleton. `load_all` is kept as a
thin, deprecated property (`DeprecationWarning`) for one release, returning the same
`(models, errors)` tuple shape callers already unpack.

BUG-015: the `"qmls"` key is gone from the returned mapping -- grep across `data_validate/` found
no consumer reading `raw_data_map["qmls"]` (`QMLReader`/`.qml` scanning were removed in the same
slice, see `engine/scanner.py` and `engine/factory.py`).

SEC-003: `DataLoaderFacade.load()` enforces a maximum file size (checked via `Path.stat()`
before a file is read) and a maximum sheet shape (rows/columns, checked after a file is read) as a
denial-of-service guard against zip-bomb-style or accidental huge input. Both limits are injected
through the constructor (`limits`) — the canonical values live on
`data_validate.config.application_config.ApplicationConfig`, kept out of this module to avoid a
`loading` -> `config` dependency (`.claude/rules/architecture-boundaries.md`); the caller
(`SpreadsheetProcessor._read_data`) reads them from `self.context.config` and passes them in.
User-facing violation messages go through an injected `translate` callable (falling back to a
`pt_BR` `MessageCatalog` when none is given) rather than a hardcoded string, per
`.claude/rules/i18n.md`.

PROTO-013: `DataLoaderFacade.load()` also loads the optional, server-generated territory registry
`spd_data.json` (`.specs/business-rules/territories.md`) directly (stdlib `json`, not a
`ReaderFactory`/header strategy, since it is not a declared sheet) and returns it as a
`TerritoryRegistry` on `LoadResult.territory_registry` -- absent is not an error; a malformed or
oversized registry is (SEC-003 applies to it too); a duplicate registry `id` is a warning, not an
error (the registry still loads, deduplicated).

SEC-004: `load()`'s per-file read loop catches only the specific, expected reader failures
(`FileNotFoundError`, `UnicodeDecodeError`, `pd.errors.ParserError`, `ValueError`, `IOError`, and
`python_calamine.CalamineError` -- the base of `python-calamine`'s own `ZipError`/`XmlError`/
`PasswordError`, raised by pandas' `engine="calamine"` for a malformed/corrupt `.xlsx` file, an
expected failure mode of untrusted input, not a programming error) and converts each into a
per-file message, leaving the rest of the batch to load. The former final `except Exception`
fallback (a duplicate: `Exception` already covered every one of those types, so it only ever
caught something none of the specific handlers anticipated) is gone -- a genuinely unexpected
reader failure now propagates out of `load()` instead of being downgraded to a per-file error
string, reaching `main()`'s boundary, which reports it as a fatal error and exits with code 2, per
`.claude/rules/security.md`.
"""

from __future__ import annotations

import json
import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import chardet
import pandas as pd
import python_calamine

from data_validate.i18n.catalog import MessageCatalog, default_catalog_dir
from data_validate.specs.sheet_specs import EXTRA_INPUT_FILES, HeaderLayout, SHEET_SPECS

from ..engine.factory import ReaderFactory
from ..engine.scanner import FileScanner
from ..strategies.header import SingleHeaderStrategy, DoubleHeaderStrategy

# Fallback DoS-guard limits, mirroring `ApplicationConfig.MAX_INPUT_FILE_BYTES`/`MAX_SHEET_ROWS`/
# `MAX_SHEET_COLUMNS` (SEC-003), used only when the facade is constructed without an explicit
# `limits` tuple (e.g. direct/legacy use, or a test that doesn't care about the limits).
_DEFAULT_MAX_FILE_BYTES = 100 * 1024 * 1024
_DEFAULT_MAX_SHEET_ROWS = 1_000_000
_DEFAULT_MAX_SHEET_COLUMNS = 5_000

# PROTO-007 (STRUCT-013, gap G-01): only flag a confident, clearly-non-UTF-8 `chardet` guess --
# a low-confidence detection on a short/ambiguous sample is not reported, to avoid a false
# positive on a genuinely UTF-8 file `chardet` cannot fully tell apart from ASCII.
_ENCODING_SAMPLE_BYTES = 4096
_ENCODING_CONFIDENCE_THRESHOLD = 0.7
_ACCEPTED_ENCODINGS = frozenset({"utf-8", "ascii"})

# PROTO-013: the optional, server-generated territory registry (`.specs/business-rules/
# territories.md`); the sole entry of `EXTRA_INPUT_FILES` today, named here as its own constant
# for readability at each of this module's several call sites.
_TERRITORY_REGISTRY_FILENAME = EXTRA_INPUT_FILES[0]


def _parse_territory_registry_ids(payload: object) -> list[int]:
    """PROTO-013: validate and extract every `id` from a parsed `spd_data.json` payload.

    Expected shape: `{"values": [{"id": int, "name": str, "region": str}, ...]}` -- extra keys on
    each entry (`name`/`region`/anything else) are tolerated and ignored; only `id` matters here.

    Args:
        payload: The object `json.load` produced from `spd_data.json`.

    Returns:
        list[int]: Every entry's `id`, in file order (may contain duplicates -- the caller
            decides how to treat those).

    Raises:
        ValueError: If `payload` is not a `dict`, `payload["values"]` is not a `list`, or any
            entry is not an object with an integer `id` (`bool` is rejected too -- `isinstance(True,
            int)` is `True` in Python, but a boolean is not a territory id).
    """
    if not isinstance(payload, dict):
        raise ValueError("root JSON value must be an object")
    values = payload.get("values")
    if not isinstance(values, list):
        raise ValueError("'values' must be a list")

    ids: list[int] = []
    for entry in values:
        if not isinstance(entry, dict):
            raise ValueError(f"each entry of 'values' must be an object, got {entry!r}")
        entry_id = entry.get("id")
        if isinstance(entry_id, bool) or not isinstance(entry_id, int):
            raise ValueError(f"each entry's 'id' must be an integer, got {entry_id!r}")
        ids.append(entry_id)
    return ids


def _worksheet_names(path: Path) -> list[str]:
    """PROTO-003 (STRUCT-014, protocol §2 p.3, since v1.14): every worksheet name in an `.xlsx`.

    `python_calamine`/pandas' `engine="calamine"` silently reads only the first worksheet of an
    `.xlsx`; a workbook with more than one is not rejected, only reported here -- the first sheet
    is still what gets parsed and validated (today's silent behaviour, now surfaced to the user
    instead of invisible). A file this check cannot even open (`OSError`, e.g. the path vanished
    between the earlier `Path.stat()` size check and here; or `python_calamine.CalamineError` for
    a malformed/corrupt `.xlsx`) is swallowed and reported as "cannot determine" (`[]`) rather
    than raised here -- this check is a best-effort structural warning, not the file's actual read
    attempt, which still runs right after (via `reader.read()`) and reports its own, more specific
    STRUCT-007 error for a genuinely unreadable file, with that error's own original message
    (not this check's own, possibly differently-worded, attempt to open the same broken file).

    Args:
        path: Path to an `.xlsx` file.

    Returns:
        list[str]: Every sheet name, in workbook order, or `[]` when the workbook could not be
            opened for this check (treated the same as "nothing to report").
    """
    try:
        return list(python_calamine.CalamineWorkbook.from_path(str(path)).sheet_names)
    except (OSError, python_calamine.CalamineError):
        return []


def _detect_non_utf8_encoding(path: Path) -> str | None:
    """PROTO-007 (STRUCT-013, gap G-01): detect a confidently non-UTF-8 CSV encoding.

    Reads a sample of raw bytes and first tries to decode it as UTF-8 directly: a sample that
    round-trips through `bytes.decode("utf-8")` IS UTF-8 (accented characters included), full
    stop -- trusted over `chardet`'s own guess, which is known to mis-detect short samples
    containing only a couple of accented characters as `ISO-8859-1` with moderate-to-high
    confidence (a real false-positive risk this project must not surface as a false error). Only
    when the sample genuinely fails to decode as UTF-8 does `chardet` run, to name the encoding
    the FAQ message reports (the same detection
    `helpers.base.file_system_utils.FileSystemUtils.detect_encoding` performs, reproduced here
    directly on `chardet` -- without that class's `LanguageManager` dependency -- so the loading
    layer stays dependent only on `specs`/`util`, per `.claude/rules/architecture-boundaries.md`).
    A low-confidence `chardet` guess (`_ENCODING_CONFIDENCE_THRESHOLD`) on that already-invalid
    sample is still not reported, so an ambiguous case does not name a wrong encoding.

    An `OSError` opening the sample (e.g. the path vanished between the earlier `Path.stat()`
    size check and here) is swallowed and treated as "nothing to report" -- the file's actual
    read attempt still runs right after and reports its own, more specific error.

    Args:
        path: Path to a `.csv` file.

    Returns:
        str | None: The detected encoding name when the sample is confidently not UTF-8,
            otherwise `None` (empty/unreadable file, valid UTF-8, or a low-confidence guess).
    """
    try:
        with open(path, "rb") as handle:
            raw_sample = handle.read(_ENCODING_SAMPLE_BYTES)
    except OSError:
        return None
    if not raw_sample:
        return None
    try:
        raw_sample.decode("utf-8")
        return None
    except UnicodeDecodeError:
        pass
    detection = chardet.detect(raw_sample)
    encoding = detection.get("encoding")
    confidence = detection.get("confidence") or 0.0
    if not encoding or encoding.lower() in _ACCEPTED_ENCODINGS or confidence < _ENCODING_CONFIDENCE_THRESHOLD:
        return None
    return str(encoding)


class LoadedSheet:
    """Encapsulates loaded spreadsheet data and file metadata.

    Attributes:
        input_folder (str): Path to the folder where the data file is located.
        name (str): File stem (base name without extension).
        filename (str): Full file name including extension.
        extension (str): File extension (e.g. '.csv', '.xlsx').
        path (pathlib.Path): Full path to the file.
        raw_data (pd.DataFrame): Data extracted from the file.
        header_type (str): `"single"` or `"double"` based on the DataFrame's column levels.
        is_read_successful (bool): True if the file was successfully read.
        does_file_exist (bool): True if the file exists on disk.
    """

    def __init__(
        self,
        input_folder: str,
        path: Path,
        raw_data: pd.DataFrame,
        is_read_successful: bool = True,
    ):
        # SETUP
        self.input_folder = input_folder
        self.path = path
        self.raw_data = raw_data
        self.is_read_successful = is_read_successful
        self.does_file_exist = self.path.exists() if isinstance(self.path, Path) else False

        # UNPACKING VARIABLES
        self.name = self.path.stem
        self.filename = self.path.name
        self.extension = self.path.suffix
        self.path = self.path
        self.header_type = "single" if self.raw_data.columns.nlevels == 1 else "double"

    def __str__(self) -> str:
        return (
            f"LoadedSheet({self.name}):\n"
            + f"  input_folder: {self.input_folder}\n"
            + f"  name: {self.name}\n"
            + f"  filename: {self.filename}\n"
            + f"  extension: {self.extension}\n"
            + f"  path: {self.path}\n"
            + f"  raw_data: \n{self.raw_data.head()}\n"
            + f"  raw_data shape: {self.raw_data.shape}\n"
            + f"  raw_data columns: {self.raw_data.columns}\n"
            + f"  raw_data dtypes: {self.raw_data.dtypes}\n"
            + f"  header_type: {self.header_type}\n"
            + f"  is_read_successful: {self.is_read_successful}\n"
            + f"  does_file_exist: {self.does_file_exist}\n"
        )


# deprecated alias (ARC-009/ARC-013): kept one release for any external importer of the old
# name; `LoadedSheet` is the same class, not a subclass or wrapper.
DataLoaderModel = LoadedSheet


@dataclass(frozen=True)
class TerritoryRegistry:
    """PROTO-013: parsed state of the optional `spd_data.json` territory registry.

    `spd_data.json` is not a declared sheet (`SHEET_SPECS`) -- it is an optional, server-generated
    artefact (`.specs/business-rules/territories.md`) read directly by `DataLoaderFacade`, never
    through `ReaderFactory`/a header strategy.

    Attributes:
        ids: Every registry `id`, deduplicated. Empty when the registry is absent or malformed
            (`loaded` is `False` in both of those cases).
        loaded: Whether `spd_data.json` was present and parsed into a valid `{"values": [...]}`
            shape -- `True` even when `ids` also triggered the duplicate-id warning (a registry
            defect, not a fatal one). `False` when the file is simply absent (not an error) or
            malformed/oversized (an error; see `error`).
        error: The user-facing (translated) loading-error message when `loaded` is `False` because
            the file could not be parsed, or `None` (the file is absent, or it loaded fine).
    """

    ids: frozenset[int] = frozenset()
    loaded: bool = False
    error: str | None = None


@dataclass(frozen=True)
class LoadResult:
    """Outcome of `DataLoaderFacade.load()`.

    Attributes:
        models: Sheet name -> `LoadedSheet`, one entry per sheet declared in `SHEET_SPECS`
            (present even when the file was absent or failed to read, mirroring `load_all`'s
            historical "missing sheets fill in as empty" behaviour).
        errors: User-facing (translated) messages for read failures and SEC-003 size violations.
        warnings: User-facing (translated) non-fatal messages -- today, only the territory
            registry's duplicate-id case (PROTO-013).
        territory_registry: The parsed state of the optional `spd_data.json` registry (PROTO-013),
            defaulting to "absent" (`TerritoryRegistry()`) so every existing call site that builds
            a `LoadResult` without naming this field keeps working unchanged.
    """

    models: dict[str, LoadedSheet]
    errors: list[str]
    warnings: list[str] = field(default_factory=list)
    territory_registry: TerritoryRegistry = field(default_factory=TerritoryRegistry)


class DataLoaderFacade:
    """
    en_US: Loads all files declared in `SHEET_SPECS` and returns a `LoadResult`.

    SEC-003: enforces `MAX_INPUT_FILE_BYTES`/`MAX_SHEET_ROWS`/`MAX_SHEET_COLUMNS`-style limits
    (see module docstring) while loading, reporting a violation as an FS-category error and
    treating the offending file as unread rather than attempting to hold an oversized frame in
    memory.
    """

    def __init__(
        self,
        input_dir: str,
        translate: Callable[..., str] | None = None,
        limits: tuple[int, int, int] | None = None,
    ):
        """Initialize the facade.

        Args:
            input_dir: Path to the folder containing the bundle to load.
            translate: Callable rendering a catalog key + named params into localized text
                (typically `LanguageManager.text` or `MessageCatalog.text`). Defaults to a
                `pt_BR` `MessageCatalog` when not given, so the facade never needs a
                `GeneralContext` to report a size-limit violation.
            limits: `(max_file_bytes, max_sheet_rows, max_sheet_columns)`. Defaults to the
                module's fallback constants (mirroring `ApplicationConfig`'s SEC-003 limits)
                when not given.
        """
        self.input_dir = Path(input_dir)
        self.scanner = FileScanner(self.input_dir)
        self._translate = translate or MessageCatalog("pt_BR", default_catalog_dir()).text
        max_file_bytes, max_sheet_rows, max_sheet_columns = limits or (
            _DEFAULT_MAX_FILE_BYTES,
            _DEFAULT_MAX_SHEET_ROWS,
            _DEFAULT_MAX_SHEET_COLUMNS,
        )
        self._max_file_bytes = max_file_bytes
        self._max_sheet_rows = max_sheet_rows
        self._max_sheet_columns = max_sheet_columns

    def load(self) -> LoadResult:
        """Load every sheet declared in `SHEET_SPECS` from `self.input_dir`.

        Returns:
            LoadResult: one `LoadedSheet` per declared sheet name, plus any read/size-limit
            error messages collected along the way.
        """
        errors: list[str] = []
        files_map, _ignored, _missing_files = self.scanner.scan()

        data: dict[str, LoadedSheet] = {}
        for name, path in files_map.items():
            spec = SHEET_SPECS[name]
            strategy = DoubleHeaderStrategy() if spec.header is HeaderLayout.DOUBLE else SingleHeaderStrategy()
            reader = ReaderFactory.get_reader(path, strategy, sep=spec.csv_separator)

            # Configure DataModel
            df_local = None
            try:
                file_size_bytes = path.stat().st_size
                if file_size_bytes > self._max_file_bytes:
                    errors.append(
                        self._translate(
                            "loader_error_file_too_large",
                            filename=path.name,
                            size_mb=f"{file_size_bytes / (1024 * 1024):.1f}",
                            limit_mb=f"{self._max_file_bytes / (1024 * 1024):.0f}",
                        )
                    )
                else:
                    if path.suffix == ".xlsx":
                        sheet_names = _worksheet_names(path)
                        if len(sheet_names) > 1:
                            errors.append(
                                self._translate(
                                    "rule.STRUCT-014.error",
                                    filename=path.name,
                                    first_sheet=sheet_names[0],
                                    extra_sheets=", ".join(sheet_names[1:]),
                                )
                            )
                    elif path.suffix == ".csv":
                        non_utf8_encoding = _detect_non_utf8_encoding(path)
                        if non_utf8_encoding is not None:
                            errors.append(
                                self._translate(
                                    "rule.STRUCT-013.error",
                                    filename=path.name,
                                    encoding=non_utf8_encoding,
                                )
                            )

                    df_local = reader.read()
                    rows, columns = df_local.shape
                    if rows > self._max_sheet_rows or columns > self._max_sheet_columns:
                        errors.append(
                            self._translate(
                                "loader_error_sheet_too_big",
                                filename=path.name,
                                rows=rows,
                                columns=columns,
                                max_rows=self._max_sheet_rows,
                                max_columns=self._max_sheet_columns,
                            )
                        )
                        df_local = None
            except FileNotFoundError as e:
                errors.append(f"{path.name}: Arquivo não encontrado no diretório. Detalhes: {e} ({type(e)})")
            except UnicodeDecodeError as e:
                errors.append(
                    f"{path.name}: Erro de codificação do arquivo. Verifique se está em UTF-8. Detalhes: {e} ({type(e)})"
                )
            except pd.errors.ParserError as e:
                errors.append(
                    f"{path.name}: Erro na estrutura da planilha. Verifique se há células mescladas ou formato inválido. Detalhes: {e} ({type(e)})"
                )
            except ValueError as e:
                errors.append(
                    f"{path.name}: Erro nos valores da planilha. Verifique se os tipos de dados estão corretos. Detalhes: {e} ({type(e)})"
                )
            except IOError as e:
                errors.append(
                    f"{path.name}: Erro de entrada/saída ao ler o arquivo. Verifique se ele não está aberto em outro programa. Detalhes: {e} ({type(e)})"
                )
            except python_calamine.CalamineError as e:
                # A malformed/corrupt .xlsx (bad zip, bad XML, password-protected, ...) is an
                # expected failure mode of untrusted input, not a programming error (SEC-004).
                errors.append(f"{path.name}: Erro inesperado ao processar o arquivo. Detalhes: {e} ({type(e)})")

            data_model = LoadedSheet(
                input_folder=str(self.input_dir),
                path=path,
                raw_data=df_local if df_local is not None else pd.DataFrame(),
                is_read_successful=True if df_local is not None else False,
            )

            data[name] = data_model

        # Add missing or non-required files as empty
        for name in SHEET_SPECS:
            if name not in data:
                data[name] = LoadedSheet(
                    input_folder=str(self.input_dir),
                    path=Path(name),
                    raw_data=pd.DataFrame(),
                    is_read_successful=False,
                )

        territory_registry, registry_errors, registry_warnings = self._load_territory_registry()
        errors.extend(registry_errors)

        return LoadResult(models=data, errors=errors, warnings=registry_warnings, territory_registry=territory_registry)

    def _load_territory_registry(self) -> tuple[TerritoryRegistry, list[str], list[str]]:
        """PROTO-013: load the optional `spd_data.json` territory registry, if present.

        Untrusted input (`.claude/rules/security.md`): size-limited with the same
        `MAX_INPUT_FILE_BYTES`-derived limit (SEC-003) as every other input file, parsed with the
        stdlib `json` module, and only the specific exceptions a malformed/oversized file can
        raise are ever caught (`OSError` -- e.g. the file vanished or is unreadable;
        `json.JSONDecodeError` -- not valid JSON; `UnicodeDecodeError` -- not valid UTF-8; and this
        module's own `ValueError` from `_parse_territory_registry_ids` for well-formed JSON in the
        wrong shape) -- never a bare `except`, and a malformed registry never crashes `load()`.

        A duplicate `id` across registry entries is not treated as fatal: `.specs/business-rules/
        territories.md` calls it "a registry defect (server-side)", so the registry still loads
        (deduplicated) and a warning is returned instead of an error.

        Returns:
            tuple[TerritoryRegistry, list[str], list[str]]: the parsed registry state, error
                messages (empty unless the file is oversized or malformed), and warning messages
                (empty unless the registry contains duplicate ids).
        """
        path = self.input_dir / _TERRITORY_REGISTRY_FILENAME
        # `os.path.isfile`/`os.path.getsize` (not `Path.is_file`/`Path.stat`) deliberately: this
        # method reads a file no other code path in this class touches, and several existing
        # tests patch `Path.stat` globally to fake the size of the *sheet* files scanned earlier
        # in `load()` -- using the `os` module here keeps that unrelated mock from also making
        # this method believe a non-existent `spd_data.json` exists.
        if not os.path.isfile(path):
            return TerritoryRegistry(), [], []

        try:
            file_size_bytes = os.path.getsize(path)  # noqa: PTH202 -- see the comment above
            if file_size_bytes > self._max_file_bytes:
                message = self._translate(
                    "loader_error_file_too_large",
                    filename=path.name,
                    size_mb=f"{file_size_bytes / (1024 * 1024):.1f}",
                    limit_mb=f"{self._max_file_bytes / (1024 * 1024):.0f}",
                )
                return TerritoryRegistry(error=message), [message], []

            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            ids = _parse_territory_registry_ids(payload)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            message = self._translate("loader_error_registry_invalid", filename=path.name, details=str(error))
            return TerritoryRegistry(error=message), [message], []

        registry_warnings: list[str] = []
        unique_ids = frozenset(ids)
        if len(unique_ids) != len(ids):
            registry_warnings.append(self._translate("loader_warning_registry_duplicate_ids", filename=path.name))

        return TerritoryRegistry(ids=unique_ids, loaded=True, error=None), [], registry_warnings

    @property
    def load_all(self) -> tuple[dict[str, LoadedSheet], list[str]]:
        """Deprecated alias for `load()`, kept for one release.

        Returns:
            The `(models, errors)` tuple that `load_all` historically returned.

        Warns:
            DeprecationWarning: always, on every access.
        """
        warnings.warn(
            "DataLoaderFacade.load_all is deprecated; call DataLoaderFacade.load() and read "
            ".models/.errors off the returned LoadResult instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        result = self.load()
        return result.models, result.errors
