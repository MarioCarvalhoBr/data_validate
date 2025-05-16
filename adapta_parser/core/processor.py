#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
# src/processador.py
import os
from logging import Logger
from typing import List

import pandas as pd

from common.locale.language_manager import LanguageManager
from common.utils.file_system_utils import FileSystemUtils
from controller import DataImporterFacade
from data_model import SpDescription, SpComposition, SpValues, SpProportionalities, SpScenario, SpTemporalReference
from validation.validator_structure import ValidatorStructureFiles


class ProcessadorPlanilhas:
    """
    Classe principal para processar as planilhas, validar dados e gerar relatórios.
    """

    def __init__(self, pasta_entrada: str, pasta_saida: str, logger: Logger, language_manager: LanguageManager, fs_utils: FileSystemUtils):
        self.pasta_entrada = pasta_entrada
        self.pasta_saida = pasta_saida
        self.leitor_factory = None
        self.logger = logger
        self.language_manager = language_manager
        self.fs_utils = fs_utils

        self.processar()
    def _ler_dados(self, nome_arquivo: str) -> pd.DataFrame:
        """Lê os dados de um arquivo usando o leitor apropriado."""
        caminho_completo = os.path.join(self.pasta_entrada, nome_arquivo)
        leitor = self.leitor_factory.create_reader(caminho_completo)
        return leitor.read_data(caminho_completo)

    def _validar_dados(self, df: pd.DataFrame, tipo_dado: str) -> List[str]:
        pass

    def processar(self):

        self.logger.info("Iniciando processamento...")
        structure_validator = ValidatorStructureFiles(self.pasta_entrada, self.fs_utils)
        errors = structure_validator.validate()

        if not errors:
            # input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/adapta_parser/data/input/data_ground_truth_01'
            importer = DataImporterFacade(self.pasta_entrada)
            data = importer.load_all

            sp_description = SpDescription(data_model=data[SpDescription.INFO["SP_NAME"]])
            print(sp_description)

            sp_composition = SpComposition(data_model=data[SpComposition.INFO["SP_NAME"]])
            print(sp_composition)

            sp_values = SpValues(data_model=data[SpValues.INFO["SP_NAME"]])
            print(sp_values)

            sp_proportionalities = SpProportionalities(data_model=data[SpProportionalities.INFO["SP_NAME"]])
            print(sp_proportionalities)

            sp_scenario = SpScenario(data_model=data[SpScenario.INFO["SP_NAME"]])
            print(sp_scenario)

            sp_temporal_reference = SpTemporalReference(data_model=data[SpTemporalReference.INFO["SP_NAME"]])
            print(sp_temporal_reference)

        for error in errors:
            self.logger.error(error)

        """arquivos = [f for f in os.listdir(self.pasta_entrada)]
        self.logger.info(f'arquivos: {arquivos}')

        my_reader = ReaderDataFactory.create_reader(os.path.join(self.pasta_entrada, arquivos[0]))
        print(my_reader.read_data(os.path.join(self.pasta_entrada, arquivos[0])))"""


