#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/facade.py
"""
Facade para importar todos os arquivos esperados de forma simples.

SEC-003: `DataLoaderFacade.load_all` enforces a maximum file size (checked via `Path.stat()`
before a file is read) and a maximum sheet shape (rows/columns, checked after a file is read) as a
denial-of-service guard against zip-bomb-style or accidental huge input. Both limits are injected
through the constructor (`limits`) — the canonical values live on
`data_validate.config.application_config.ApplicationConfig`, kept out of this module to avoid a
`loading` -> `config` dependency (`.claude/rules/architecture-boundaries.md`); the caller
(`SpreadsheetProcessor._read_data`) reads them from `self.context.config` and passes them in.
User-facing violation messages go through an injected `translate` callable (falling back to a
`pt_BR` `MessageCatalog` when none is given) rather than a hardcoded string, per
`.claude/rules/i18n.md`.
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from data_validate.i18n.catalog import MessageCatalog, default_catalog_dir

from ..common.config import Config
from ..engine.factory import ReaderFactory
from ..engine.scanner import FileScanner
from ..strategies.header import SingleHeaderStrategy, DoubleHeaderStrategy

# Fallback DoS-guard limits, mirroring `ApplicationConfig.MAX_INPUT_FILE_BYTES`/`MAX_SHEET_ROWS`/
# `MAX_SHEET_COLUMNS` (SEC-003), used only when the facade is constructed without an explicit
# `limits` tuple (e.g. direct/legacy use, or a test that doesn't care about the limits).
_DEFAULT_MAX_FILE_BYTES = 100 * 1024 * 1024
_DEFAULT_MAX_SHEET_ROWS = 1_000_000
_DEFAULT_MAX_SHEET_COLUMNS = 5_000


class DataLoaderModel:
    """
    Handles the importation and management of data models from a specified file path,
    providing access to metadata and data for further operations.

    The class is used to manage the details of data model files, encapsulating metadata
    such as the file name, extension, and path, as well as the associated data stored
    as a pandas DataFrame. It provides an informative string representation for debugging
    and logging purposes.

    :ivar input_folder: Path to the folder where the data model file is located.
    :type input_folder: str
    :ivar name: The stem (base name without extension) of the file.
    :type name: str
    :ivar filename: The full name of the file including the extension.
    :type filename: str
    :ivar extension: The file extension.
    :type extension: str
    :ivar path: Full path to the file.
    :type path: Path
    :ivar raw_data: Data extracted from the file as a pandas DataFrame.
    :type raw_data: pd.DataFrame
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

    def __str__(self):
        return (
            f"DataLoaderModel({self.name}):\n"
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


class DataLoaderFacade:
    """
    en_US: Loads all files and returns a dict of base_name→object (DataFrame or text).

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
        self.config = Config()
        self._translate = translate or MessageCatalog("pt_BR", default_catalog_dir()).text
        max_file_bytes, max_sheet_rows, max_sheet_columns = limits or (
            _DEFAULT_MAX_FILE_BYTES,
            _DEFAULT_MAX_SHEET_ROWS,
            _DEFAULT_MAX_SHEET_COLUMNS,
        )
        self._max_file_bytes = max_file_bytes
        self._max_sheet_rows = max_sheet_rows
        self._max_sheet_columns = max_sheet_columns

    @property
    def load_all(self):
        errors = []
        files_map, qml_files, missing_files = self.scanner.scan()

        data = {}
        for name, path in files_map.items():
            _, header_type, _ = self.config.file_specs[name]
            if header_type == "single":
                strat = SingleHeaderStrategy()
            elif header_type == "double":
                strat = DoubleHeaderStrategy()
            else:
                # qml will not pass through here
                continue
            reader = ReaderFactory.get_reader(path, strat)

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
            except Exception as e:
                errors.append(f"{path.name}: Erro inesperado ao processar o arquivo. Detalhes: {e} ({type(e)})")

            data_model = DataLoaderModel(
                input_folder=str(self.input_dir),
                path=path,
                raw_data=df_local if df_local is not None else pd.DataFrame(),
                is_read_successful=True if df_local is not None else False,
            )

            data[name] = data_model

        # Add raw QMLs
        data["qmls"] = [ReaderFactory.get_reader(q, SingleHeaderStrategy()).read() for q in qml_files]

        # Add missing or non-required files as empty
        for name, (req, _, _) in self.config.file_specs.items():
            if name not in data:
                data[name] = DataLoaderModel(
                    input_folder=str(self.input_dir),
                    path=Path(name),
                    raw_data=pd.DataFrame(),
                    is_read_successful=False,
                )

        return data, errors
