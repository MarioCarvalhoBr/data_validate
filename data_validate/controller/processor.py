#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from logging import Logger

from common.utils.data_args import DataArgs
from common.utils.file_system_utils import FileSystemUtils
from config.config import Config, NamesEnum
from tools import DataLoaderFacade
from data_model import (
    SpDescription, SpComposition, SpValue, SpTemporalReference,
    SpProportionality, SpScenario, SpLegend, SpDictionary
)
from validation.description_validator import SpDescriptionValidator
from validation.scenario_validator import SpScenarioValidator
from validation.spellchecker_validator import SpellCheckerValidator
from validation.temporal_reference_validator import SpTemporalReferenceValidator
from validation.validator_structure import ValidatorStructureFiles
from validation.data_context import DataContext
from validation.value_validator import SpValueValidator
from .report import ReportList

FLAG = None


class ProcessorSpreadsheet:
    """
    Classe principal para processar as planilhas, validar dados e gerar relatórios.
    """

    def __init__(self, data_args: DataArgs, logger: Logger, fs_utils: FileSystemUtils):
        # SETUP
        self.data_args = data_args
        self.logger = logger
        self.fs_utils = fs_utils

        # UNPACKING DATA ARGS
        self.language_manager = fs_utils.locale_manager
        self.config = Config(self.language_manager)
        self.TITLES_INFO = self.config.get_verify_names()

        # SETUP CONFIGURE VARIABLES
        self.input_folder = data_args.data_file.input_folder
        self.output_folder = data_args.data_file.output_folder

        self.list_scenarios = []
        self.exists_scenario = False
        self.models_to_use = []
        self.classes_to_initialize = [
            SpDescription, SpComposition, SpValue, SpTemporalReference,
            SpProportionality, SpScenario, SpLegend, SpDictionary
        ]

        self.data_context: DataContext = DataContext(None, None, None, None)
        self.report_list = ReportList()

        # Running the main processing function
        self.run()

    def _read_data(self) -> None:
        # 0 ETL: Extract, Transform, Load
        importer = DataLoaderFacade(self.input_folder)
        data, errors_data_importer = importer.load_all
        # APPEND ERRORS TO REPORT LIST
        self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=errors_data_importer)

        # 1 STRUCTURE_VALIDATION: Validate the structure of the data
        self.structure_validator = ValidatorStructureFiles(self.input_folder, self.fs_utils)

        # 1.1 GENERAL STRUCTURE VALIDATION ERRORS: Errors from the general structure validation
        errors_structure_general = self.structure_validator.validate()
        self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=errors_structure_general)

        if data[SpScenario.CONSTANTS.SP_NAME].exists_file and data[SpScenario.CONSTANTS.SP_NAME].read_success:
            self.exists_scenario = True
            if SpScenario.RequiredColumn.COLUMN_SYMBOL.name in data[SpScenario.CONSTANTS.SP_NAME].df_data.columns:
                self.list_scenarios = data[SpScenario.CONSTANTS.SP_NAME].df_data[SpScenario.RequiredColumn.COLUMN_SYMBOL.name].unique().tolist()

        # 1.2 SPECIFIC STRUCTURE VALIDATION ERRORS: Errors from the specific structure validation
        for model_class in self.classes_to_initialize:
            sp_name_key = model_class.CONSTANTS.SP_NAME

            # Dynamically create the attribute name, e.g., "sp_description"
            attribute_name = f"sp_{sp_name_key.lower()}"

            # Model instance creation and initialization
            model_instance = model_class(data_model=data.get(sp_name_key), **{model_class.VAR_CONSTS.EXISTING_SCENARIO: self.exists_scenario, model_class.VAR_CONSTS.LIST_SCENARIOS: self.list_scenarios})
            setattr(self, attribute_name, model_instance)
            self.models_to_use.append(model_instance)

            self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=model_instance.STRUCTURE_LIST_ERRORS,
                                    warnings=model_instance.STRUCTURE_LIST_WARNINGS)
            self.report_list.extend(self.TITLES_INFO[NamesEnum.FC.value], errors=model_instance.DATA_CLEAN_ERRORS,
                                    warnings=model_instance.DATA_CLEAN_WARNINGS)

            if FLAG is not None:
                self.logger.info(f"Initialized model: {attribute_name} = {model_instance}")

    def _configure(self) -> None:
        # Crie toda a lista dos 33 reportes vazia para ser preenchida posteriormente
        for name in NamesEnum:
            self.report_list.add_by_name(self.TITLES_INFO[name.value])

    def _report(self) -> None:
        # Print all reports and their errors
        for report in self.report_list:
            print(f"Report: {report.name_test}")
            print(f"  Errors: {len(report.errors)}")
            for error in report.errors:
                print(f"    - {error}")
            print(f"  Warnings: {len(report.warnings)}")
            for warning in report.warnings:
                print(f"    - {warning}")
            print("---------------------------------------------------------------")

        # Imprime o número total de erros e avisos
        total_errors = sum(len(report.errors) for report in self.report_list)
        total_warnings = sum(len(report.warnings) for report in self.report_list)
        self.logger.error(f"Total errors: {total_errors}")
        self.logger.warning(f"Total warnings: {total_warnings}")
    def _build_pipeline(self) -> None:
        """
        Build the validation pipeline by initializing the data context and running the validations.
        """
        self.logger.info("Building validation pipeline...")

        # Create the DataContext with the initialized models
        self.data_context = DataContext(models_to_use=self.models_to_use, config=self.config, fs_utils=self.fs_utils, data_args=self.data_args)

        # RUN ALL VALIDATIONS PIPELINE
        SpDescriptionValidator(data_context=self.data_context, report_list=self.report_list)
        SpTemporalReferenceValidator(data_context=self.data_context, report_list=self.report_list)
        SpScenarioValidator(data_context=self.data_context, report_list=self.report_list)
        SpellCheckerValidator(data_context=self.data_context, report_list=self.report_list)
        SpValueValidator(data_context=self.data_context, report_list=self.report_list)
    def run(self):
        self.logger.info("Iniciando processamento...")
        self._configure()
        self._read_data()
        self._build_pipeline()
        self._report()