#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/facade.py
"""
Facade para importar todos os arquivos esperados de forma simples.
"""

from pathlib import Path

import pandas as pd

from ..common.config import Config
from ..engine.factory import ReaderFactory
from ..engine.scanner import FileScanner
from ..strategies.header import SingleHeaderStrategy, DoubleHeaderStrategy


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
    """

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.scanner = FileScanner(self.input_dir)
        self.config = Config()

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
                df_local = reader.read()
            except FileNotFoundError as e:
                errors.append(f"{path.name}: Arquivo não encontrado no diretório. Detalhes: {e} ({type(e)})")
            except UnicodeDecodeError as e:
                errors.append(f"{path.name}: Erro de codificação do arquivo. Verifique se está em UTF-8. Detalhes: {e} ({type(e)})")
            except pd.errors.ParserError as e:
                errors.append(
                    f"{path.name}: Erro na estrutura da planilha. Verifique se há células mescladas ou formato inválido. Detalhes: {e} ({type(e)})"
                )
            except ValueError as e:
                errors.append(f"{path.name}: Erro nos valores da planilha. Verifique se os tipos de dados estão corretos. Detalhes: {e} ({type(e)})")
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
