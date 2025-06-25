#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from logging import Logger
from types import MappingProxyType
from typing import List

import pandas as pd

from common.utils.file_system_utils import FileSystemUtils
from config.config import Config, NamesEnum
from controller import DataImporterFacade
from data_model import (
    SpDescription, SpComposition, SpValue, SpTemporalReference,
    SpProportionality, SpScenario, SpLegend, SpDictionary
)
from validation.description_validator import SpDescriptionValidator
from validation.validator_structure import ValidatorStructureFiles
from validation.data_context import DataContext
from .report import Report, ReportList

FLAG = None


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

        self.config = Config(self.language_manager)
        self.TITLES_VERITY = self.config.get_verify_names()

        self.list_scenarios = []

        # Lista de reportes: inicializa com um dicionário vazio
        self.report_list = ReportList()

        # Data Model Initialization
        # CONFIGURE
        self.classes_to_initialize = [
            SpDescription, SpComposition, SpValue, SpTemporalReference,
            SpProportionality, SpScenario, SpLegend, SpDictionary
        ]
        self.models_to_use = []

        # Running the main processing function
        self.run()

    def _read_data(self) -> None:
        # 0 ETL: Extract, Transform, Load
        importer = DataImporterFacade(self.input_folder)
        data, errors_data_importer = importer.load_all
        # APPEND ERRORS TO REPORT LIST
        self.report_list.extend(self.TITLES_VERITY[NamesEnum.FS.value], errors=errors_data_importer)


        # 1 STRUCTURE_VALIDATION: Validate the structure of the data
        self.structure_validator = ValidatorStructureFiles(self.input_folder, self.fs_utils)

        # 1.1 GENERAL STRUCTURE VALIDATION ERRORS: Errors from the general structure validation
        errors_structure_general = self.structure_validator.validate()
        self.report_list.extend(self.TITLES_VERITY[NamesEnum.FS.value], errors=errors_structure_general)

        if not data[SpScenario.INFO["SP_NAME"]].df_data.empty:
            if SpScenario.REQUIRED_COLUMNS["COLUMN_SYMBOL"] in data[SpScenario.INFO["SP_NAME"]].df_data.columns:
                self.list_scenarios = data[SpScenario.INFO["SP_NAME"]].df_data[
                    SpScenario.REQUIRED_COLUMNS["COLUMN_SYMBOL"]].tolist()

        # 1.2 SPECIFIC STRUCTURE VALIDATION ERRORS: Errors from the specific structure validation
        for model_class in self.classes_to_initialize:
            sp_name_key = model_class.INFO["SP_NAME"]

            # Dynamically create the attribute name, e.g., "sp_description"
            attribute_name = f"sp_{sp_name_key.lower()}"

            # Model instance creation and initialization
            model_instance = model_class(data_model=data.get(sp_name_key), **{"list_scenarios": self.list_scenarios})
            setattr(self, attribute_name, model_instance)
            self.models_to_use.append(model_instance)

            self.report_list.extend(self.TITLES_VERITY[NamesEnum.FS.value], errors=model_instance.STRUCTURE_LIST_ERRORS,
                                    warnings=model_instance.STRUCTURE_LIST_WARNINGS)
            self.report_list.extend(self.TITLES_VERITY[NamesEnum.FC.value], errors=model_instance.DATA_CLEAN_ERRORS,
                                    warnings=model_instance.DATA_CLEAN_WARNINGS)

            if FLAG is not None:
                self.logger.info(f"Initialized model: {attribute_name} = {model_instance}")

        # Process errors and warnings from the data model
        data_context = DataContext(self.models_to_use)

        # RUN ALL VALIDATIONS
        desc_validator = SpDescriptionValidator(data_context=data_context, config=self.config, report_list=self.report_list)

    def _configure(self) -> None:
        # Crie toda a lista dos 33 reportes vazia para ser preenchida posteriormente
        for name in NamesEnum:
            self.report_list.add_by_name(self.TITLES_VERITY[name.value])

    def _report(self) -> None:
        # Print all reports and their errors
        COUNT = 100
        for report in self.report_list:
            if COUNT <= 0:
                break
            self.logger.info(f"Report: {report.name_test}")
            self.logger.info(f"  Errors: {len(report.errors)}")
            for error in report.errors:
                self.logger.info(f"    - {error}")
            self.logger.info(f"  Warnings: {len(report.warnings)}")
            for warning in report.warnings:
                self.logger.info(f"    - {warning}")
            self.logger.info("---------------------------------------------------------------")
            COUNT -= 1

        # Imprime o número total de erros e avisos
        total_errors = sum(len(report.errors) for report in self.report_list)
        total_warnings = sum(len(report.warnings) for report in self.report_list)
        self.logger.info(f"Total errors: {total_errors}")
        self.logger.info(f"Total warnings: {total_warnings}")

    def run(self):
        self.logger.info("Iniciando processamento...")
        self._configure()
        self._read_data()
        self._report()