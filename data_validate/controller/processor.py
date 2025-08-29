#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

from data_validate.config.config import NamesEnum
from data_validate.controller.report.model_report import ModelListReport
from data_validate.controller.report.report_generator_pdf import ReportGeneratorPDF
from data_validate.services.spreadsheets.legend_validator import SpLegendValidator
from data_validate.tools import DataLoaderFacade
from data_validate.data_model import (
    SpModelABC, SpDescription, SpComposition, SpValue, SpTemporalReference,
    SpProportionality, SpScenario, SpLegend, SpDictionary
)
from data_validate.services.spreadsheets.description_validator import SpDescriptionValidator
from data_validate.services.spreadsheets.scenario_validator import SpScenarioValidator
from data_validate.services.spell.spellchecker_validator import SpellCheckerValidator
from data_validate.services.spreadsheets.temporal_reference_validator import SpTemporalReferenceValidator
from data_validate.services.structure.validator_structure import ValidatorStructureFiles
from data_validate.controller.context.data_context import DataModelsContext
from data_validate.services.spreadsheets.value_validator import SpValueValidator
from data_validate.controller.context.general_context import GeneralContext

FLAG = None


class ProcessorSpreadsheet:
    """
    Classe principal para processar as planilhas, validar dados e gerar relatórios.
    """

    def __init__(self,  context: GeneralContext):
        # SETUP GENERAL CONTEXT
        self.context = context

        # CONFIGURE VARIABLES
        self.language_manager = self.context.locale_manager
        self.TITLES_INFO=self.context.config.get_verify_names()

        # SETUP CONFIGURE VARIABLES
        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder

        # Setup kwargs for model initialization
        self.scenarios_list = []

        # OBJECTS AND ARRAYS
        self.data_models_context: DataModelsContext | None = None
        self.models_to_use = []
        self.classes_to_initialize = [
            SpDescription, SpComposition, SpValue, SpTemporalReference,
            SpProportionality, SpScenario, SpLegend, SpDictionary
        ]
        self.report_list = ModelListReport(context=self.context)


        # Desative todas as saidas do logger temporariamente
        self.context.logger.disabled = False

        # Running the main processing function
        self.run()

    def _read_data(self) -> None:
        self.context.logger.info("Data reading and preprocessing...")
        # 0 ETL: Extract, Transform, Load
        importer = DataLoaderFacade(self.input_folder)
        data, errors_data_importer = importer.load_all
        self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=errors_data_importer)

        # 1 STRUCTURE_VALIDATION: Validate the structure of the data
        self.structure_validator = ValidatorStructureFiles(context=self.context)

        # 1.1 GENERAL STRUCTURE VALIDATION ERRORS: Errors from the general structure validation
        errors_structure_general = self.structure_validator.validate()
        self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=errors_structure_general)

        # Verify scenarios and legend existence
        if data[SpScenario.CONSTANTS.SP_NAME].read_success and (SpScenario.RequiredColumn.COLUMN_SYMBOL.name in data[SpScenario.CONSTANTS.SP_NAME].df_data.columns):
                self.scenarios_list = data[SpScenario.CONSTANTS.SP_NAME].df_data[SpScenario.RequiredColumn.COLUMN_SYMBOL.name].unique().tolist()
        # Setup kwargs for model initialization
        kwargs = {
            SpModelABC.VAR_CONSTS.SCENARIO_EXISTS_FILE: data[SpScenario.CONSTANTS.SP_NAME].exists_file,
            SpModelABC.VAR_CONSTS.SCENARIO_READ_SUCCESS: data[SpScenario.CONSTANTS.SP_NAME].read_success,
            SpModelABC.VAR_CONSTS.SCENARIOS_LIST: self.scenarios_list,

            SpModelABC.VAR_CONSTS.LEGEND_EXISTS_FILE: data[SpLegend.CONSTANTS.SP_NAME].exists_file,
            SpModelABC.VAR_CONSTS.LEGEND_READ_SUCCESS: data[SpLegend.CONSTANTS.SP_NAME].read_success,
        }

        # 1.2 SPECIFIC STRUCTURE VALIDATION ERRORS: Errors from the specific structure validation
        for model_class in self.classes_to_initialize:
            sp_name_key = model_class.CONSTANTS.SP_NAME

            # Dynamically create the attribute name, e.g., "sp_description"
            attribute_name = f"sp_{sp_name_key.lower()}"

            # Model instance creation and initialization
            model_instance = model_class(context=self.context, data_model=data.get(sp_name_key), **kwargs)
            setattr(self, attribute_name, model_instance)
            self.models_to_use.append(model_instance)

            self.report_list.extend(self.TITLES_INFO[NamesEnum.FS.value], errors=model_instance.structural_errors,
                                    warnings=model_instance.structural_warnings)
            self.report_list.extend(self.TITLES_INFO[NamesEnum.FC.value], errors=model_instance.data_cleaning_errors,
                                    warnings=model_instance.data_cleaning_warnings)

            if FLAG is not None:
                self.context.logger.info(f"Initialized model: {attribute_name} = {model_instance}")

    def _configure(self) -> None:
        self.context.logger.info("Configuring the processor...")
        # Crie toda a lista dos 33 reportes vazia para ser preenchida posteriormente
        for name in NamesEnum:
            self.report_list.add_by_name(self.TITLES_INFO[name.value])

    def _build_pipeline(self) -> None:
        """
        Build the validation pipeline by initializing the data context and running the validations.
        """
        self.context.logger.info("Building validation pipeline...")

        # Create the DataContext with the initialized models
        self.data_models_context = DataModelsContext(context=self.context, models_to_use=self.models_to_use)

        # RUN ALL VALIDATIONS PIPELINE
        SpDescriptionValidator(data_models_context=self.data_models_context, report_list=self.report_list)
        SpTemporalReferenceValidator(data_models_context=self.data_models_context, report_list=self.report_list)
        SpValueValidator(data_models_context=self.data_models_context, report_list=self.report_list)

        SpellCheckerValidator(data_models_context=self.data_models_context, report_list=self.report_list)

        SpScenarioValidator(data_models_context=self.data_models_context, report_list=self.report_list)
        SpLegendValidator(data_models_context=self.data_models_context, report_list=self.report_list)

    def _report(self) -> None:
        self.context.logger.info("Generating reports...")
        # Print all reports and their errors
        if self.context.data_args.data_action.debug:
            self.context.logger.info("\nModo DEBUG ativado.")
            self.context.logger.info(f'------ Resultados da verificação dos testes ------')

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
        self.context.logger.error(f"Total errors: {total_errors}")
        self.context.logger.warning(f"Total warnings: {total_warnings}")

        # Criar a pasta de saída para salvar os relatórios HMTL e PDF
        # util.create_directory(output_folder)
        self.context.fs_utils.create_directory(self.output_folder)
        report_generator = ReportGeneratorPDF(context=self.context)

        report_generator.build_report(report_list=self.report_list)

    def run(self):
        self.context.logger.info("Starting processing...")
        self._configure()
        self._read_data()
        self._build_pipeline()
        self._report()