#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from logging import Logger
from types import MappingProxyType
from typing import List

import pandas as pd

from common.utils.file_system_utils import FileSystemUtils
from controller import DataImporterFacade
from data_model import (
    SpDescription, SpComposition, SpValue, SpTemporalReference,
    SpProportionality, SpScenario, SpLegend, SpDictionary
)
from validation.validator_structure import ValidatorStructureFiles


FLAG = None

VERIFICATIONS_NAMES = MappingProxyType({
    "errors": "Erros",
    "file_structure": "Estrutura dos arquivos da pasta de entrada",
    "file_cleaning": "Limpeza dos arquivos",
    "indicator_relations": "Relações entre indicadores",
    "tree_hierarchy": "Hierarquia como árvore",
    "indicator_levels": "Níveis de indicadores",
    "code_uniqueness": "Unicidade dos códigos",
    "html_codes_in_descriptions": "Códigos HTML nas descrições simples",
    "spelling": "Ortografia",
    "unique_titles": "Títulos únicos",
    "sequential_codes": "Códigos sequenciais",
    "empty_fields": "Campos vazios",
    "indicator_name_pattern": "Padrão para nomes dos indicadores",
    "titles_over_40_chars": "Títulos com mais de 40 caracteres",
    "simple_descriptions_over_150_chars": "Descrições simples com mais de 150 caracteres",
    "mandatory_and_prohibited_punctuation_in_descriptions": "Pontuações obrigatórias e proibidas em descrições",
    "mandatory_and_prohibited_punctuation_in_scenarios": "Pontuações obrigatórias e proibidas em cenários",
    "mandatory_and_prohibited_punctuation_in_temporal_reference": "Pontuações obrigatórias e proibidas em referência temporal",
    "unique_value_relations_in_scenarios": "Relações de valores únicos em cenários",
    "unique_value_relations_in_temporal_reference": "Relações de valores únicos em referência temporal",
    "value_combination_relations": "Relações de combinações de valores",
    "unavailable_and_invalid_values": "Valores indisponíveis e inválidos",
    "line_break_in_description": "Quebra de linha para descrição",
    "line_break_in_scenarios": "Quebra de linha para cenários",
    "line_break_in_temporal_reference": "Quebra de linha para referência temporal",
    "years_in_temporal_reference": "Anos em referência temporal",
    "legend_data_range": "Intervalo dos dados da legenda",
    "legend_value_overlap": "Sobreposição de valores na legenda",
    "sum_properties_in_influencing_factors": "Propriedades de soma nos fatores influenciadores",
    "repeated_indicators_in_proportionalities": "Indicadores repetidos em proporcionalidades",
    "indicator_relations_in_proportionalities": "Relações de indicadores em proporcionalidades",
    "indicators_in_values_and_proportionalities": "Indicadores em valores e proporcionalidades",
    "leaf_indicators_without_associated_data": "Indicadores folhas sem dados associados",
    "child_indicator_levels": "Níveis dos indicadores filhos",
})

class ProcessorSpreadsheet:
    """
    Classe principal para processar as planilhas, validar dados e gerar relatórios.
    """

    def __init__(self, input_folder: str, output_folder: str, logger: Logger, fs_utils: FileSystemUtils):
        # Configure variables
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.logger = logger
        self.fs_utils = fs_utils
        self.language_manager = fs_utils.locale_manager

        # Data Model Initialization
        self.structure_validator = None
        self.sp_description = None
        self.sp_composition = None
        self.sp_value = None
        self.sp_temporal_reference = None
        self.sp_proportionality = None
        self.sp_scenario = None
        self.sp_legend = None
        self.sp_dictionary = None
        
        # Running the main processing function
        self.run()

    def _read_data(self) -> None:
        # Structure Validation
        self.structure_validator = ValidatorStructureFiles(self.input_folder, self.fs_utils)
        errors_structure_general = self.structure_validator.validate()
        for error in errors_structure_general:
            self.logger.error(error)

        # ETL: Extract, Transform, Load
        importer = DataImporterFacade(self.input_folder)
        data, errors_data_importer = importer.load_all
        for error in errors_data_importer:
            self.logger.error(error)

        # CONFIGURE
        self.sp_description = SpDescription(data_model=data[SpDescription.INFO["SP_NAME"]])
        self.sp_composition = SpComposition(data_model=data[SpComposition.INFO["SP_NAME"]])
        self.sp_value = SpValue(data_model=data[SpValue.INFO["SP_NAME"]])
        self.sp_temporal_reference = SpTemporalReference(data_model=data[SpTemporalReference.INFO["SP_NAME"]])

        self.sp_proportionality = SpProportionality(data_model=data[SpProportionality.INFO["SP_NAME"]])
        self.sp_scenario = SpScenario(data_model=data[SpScenario.INFO["SP_NAME"]])
        self.sp_legend = SpLegend(data_model=data[SpLegend.INFO["SP_NAME"]])
        self.sp_dictionary = SpDictionary(data_model=data[SpDictionary.INFO["SP_NAME"]])

        if FLAG is not None:
            self.logger.info(self.sp_composition)
            self.logger.info(self.sp_description)
            self.logger.info(self.sp_value)
            self.logger.info(self.sp_temporal_reference)
            self.logger.info(self.sp_scenario)
            self.logger.info(self.sp_proportionality)
            self.logger.info(self.sp_legend)
            self.logger.info(self.sp_dictionary)

    def _validate_data(self, df: pd.DataFrame, tipo_dado: str) -> List[str]:
        pass

    def run(self):
        self.logger.info("Iniciando processamento...")
        self._read_data()
