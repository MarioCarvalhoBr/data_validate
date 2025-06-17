#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: data_importer/facade.py
"""
Facade para importar todos os arquivos esperados de forma simples.
"""

from pathlib import Path

from ..engine.scanner import FileScanner
from ..engine.factory import ReaderFactory
from ..common.config import Config
from ..strategies.header import SingleHeaderStrategy, DoubleHeaderStrategy
import pandas as pd

class DataModelImporter:
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
    :ivar df_data: Data extracted from the file as a pandas DataFrame.
    :type df_data: pd.DataFrame
    """
    def __init__(self, input_folder: str, path: Path, df_data: pd.DataFrame):
        self.input_folder = input_folder
        self.name = path.stem
        self.filename = path.name
        self.extension = path.suffix
        self.path = path
        self.df_data = df_data
        self.header_type = 'single' if self.df_data.columns.nlevels == 1 else 'double'

    def __str__(self):
        return f"DataModelImporter({self.name}):\n" + \
            f"  input_folder: {self.input_folder}\n" + \
            f"  name: {self.name}\n" + \
            f"  filename: {self.filename}\n" + \
            f"  extension: {self.extension}\n" + \
            f"  path: {self.path}\n" + \
            f"  df_data: \n{self.df_data.head()}\n" + \
            f"  df_data shape: {self.df_data.shape}\n" + \
            f"  df_data columns: {self.df_data.columns}\n" + \
            f"  df_data dtypes: {self.df_data.dtypes}\n" + \
            f"  header_type: {self.header_type}\n"



class DataImporterFacade:
    """
Carga todos os arquivos e retorna um dict nome_base→objeto (DataFrame ou texto).
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
            if header_type == 'single':
                strat = SingleHeaderStrategy()
            elif header_type == 'double':
                strat = DoubleHeaderStrategy()
            else:
                # qml não vai passar por aqui
                continue
            reader = ReaderFactory.get_reader(path, strat)

            # Configure DataModel
            df_local = pd.DataFrame()
            try:
                df_local = reader.read()
            except FileNotFoundError as e:
                errors.append(f"{path.name}: Arquivo não encontrado no diretório. Detalhes: {e} ({type(e)})")
            except UnicodeDecodeError as e:
                errors.append(f"{path.name}: Erro de codificação do arquivo. Verifique se está em UTF-8. Detalhes: {e} ({type(e)})")
            except pd.errors.ParserError as e:
                errors.append(f"{path.name}: Erro na estrutura da planilha. Verifique se há células mescladas ou formato inválido. Detalhes: {e} ({type(e)})")
            except ValueError as e:
                errors.append(f"{path.name}: Erro nos valores da planilha. Verifique se os tipos de dados estão corretos. Detalhes: {e} ({type(e)})")
            except IOError as e:
                errors.append(f"{path.name}: Erro de entrada/saída ao ler o arquivo. Verifique se ele não está aberto em outro programa. Detalhes: {e} ({type(e)})")
            except Exception as e:
                errors.append(f"{path.name}: Erro inesperado ao processar o arquivo. Detalhes: {e} ({type(e)})")

            data_model = DataModelImporter(
                input_folder=str(self.input_dir),
                path=path,
                df_data = df_local
            )

            data[name] = data_model

        # adiciona QMLs brutas
        data['qmls'] = [ReaderFactory.get_reader(q, SingleHeaderStrategy()).read() for q in qml_files]

        # Adiciona arquivos faltando ou não obrigatórios como vazios
        for name, (req, _, _) in self.config.file_specs.items():
            if name not in data:
                data[name] = DataModelImporter(
                    input_folder=str(self.input_dir),
                    path=Path(name),
                    df_data=pd.DataFrame()
                )

        return data, errors