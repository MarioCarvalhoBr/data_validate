from typing import List, Dict, Any
import pandas as pd

from data_validate.controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from data_validate.tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings

class SpDictionary(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "dicionario"
            self.SP_DESCRIPTION = "Planilha de dicionario"
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_WORD = pd.Series(dtype="str", name="palavra")

        ALL = [
            COLUMN_WORD.name,
        ]

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(context, data_model, **kwargs)

        self.words_to_ignore: List[str] = []

        self.run()

    def pre_processing(self):
        """
        Lê as palavras do arquivo de dicionário.
        Cada linha do arquivo é considerada uma palavra a ser ignorada.
        Esta versão corrige o problema da primeira palavra ser tratada como cabeçalho
        pelo leitor de DataFrame, comum quando não há cabeçalho explícito no arquivo.
        """
        self.words_to_ignore = []
        if self.data_loader_model and self.data_loader_model.df_data is not None:
            df = self.data_loader_model.df_data

            if len(df.columns) > 0:
                remaining_words = []
                if not df.empty:
                    remaining_words = df.iloc[:, 0].astype(str).tolist()

                self.words_to_ignore = remaining_words

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def post_processing(self):
        pass

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()

if __name__ == '__main__':
    # Para testar esta classe, você precisaria de um arquivo 'dicionario.csv' ou 'dicionario.xlsx'
    # no diretório de entrada, com uma palavra por linha.
    # Exemplo de dicionario.csv:
    # PalavraIgnorada1
    # Outr@Palavra
    # termoEspecifico

    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    # Certifique-se de que o DataImporterFacade consegue lidar com arquivos sem cabeçalho
    # e que o nome do arquivo 'dicionario' está correto.
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    if SpDictionary.INFO["SP_NAME"] in data:
        sp_dictionary_instance = SpDictionary(data_model=data[SpDictionary.INFO["SP_NAME"]])
        # A impressão das palavras já ocorre dentro do run() quando __name__ == '__main__',
        # mas podemos adicionar outra aqui se necessário, ou acessar sp_dictionary_instance.words_to_ignore
    else:
        print(f"Data for '{SpDictionary.INFO['SP_NAME']}' not found. Please check your input data and ensure a 'dicionario' file exists.")
