from pathlib import Path
from types import MappingProxyType
from typing import List

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade


class SpDictionary(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "dicionario",
        "SP_DESCRIPTION": "O arquivo de dicionário descreve palavras a serem ignoradas durante a verificação ortográfica. Este arquivo deverá conter uma palavra por linha, sem qualquer nome nas colunas. As palavras serão ignoradas somente se estiverem escritas exatamente como no dicionário, diferenciando maiúsculas e minúsculas.",
    })
    # Como o arquivo é uma lista de palavras, não há colunas obrigatórias ou opcionais no sentido tradicional.
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_WORD": "palavra",
    })
    OPTIONAL_COLUMNS = MappingProxyType({})
    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter):
        super().__init__(data_model)

        # Vars
        structure_errors = []
        structure_warnings = []
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
        if self.DATA_MODEL and self.DATA_MODEL.df_data is not None:
            df = self.DATA_MODEL.df_data

            if len(df.columns) > 0:
                remaining_words = []
                if not df.empty:
                    remaining_words = df.iloc[:, 0].astype(str).tolist()

                self.words_to_ignore = remaining_words

    def expected_structure_columns(self) -> List[str]:
        # Para um arquivo de dicionário simples, não há uma estrutura de colunas definida.
        # Retornar uma lista vazia ou talvez o nome de uma única coluna genérica se o importer assim o fizer.
        return []

    def run(self):
        self.pre_processing()
        # A lógica principal aqui seria disponibilizar self.words_to_ignore
        # para o sistema de verificação ortográfica.
        # Por enquanto, apenas imprimimos as palavras carregadas para teste.
        print(f"Palavras carregadas do dicionário ({self.FILENAME}): {self.words_to_ignore}")


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
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    if SpDictionary.INFO["SP_NAME"] in data:
        sp_dictionary_instance = SpDictionary(data_model=data[SpDictionary.INFO["SP_NAME"]])
        # A impressão das palavras já ocorre dentro do run() quando __name__ == '__main__',
        # mas podemos adicionar outra aqui se necessário, ou acessar sp_dictionary_instance.words_to_ignore
        # print(sp_dictionary_instance)
    else:
        print(f"Data for '{SpDictionary.INFO['SP_NAME']}' not found. Please check your input data and ensure a 'dicionario' file exists.")
