#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import data_validate
from config.config import NamesEnum
from data_validate.helpers.tools import DataLoaderFacade

from data_validate.controllers import (
    DataModelsContext,
    GeneralContext,
    ModelListReport,
    ReportGeneratorFiles,
)

from data_validate.models import (
    SpModelABC,
    SpDescription,
    SpComposition,
    SpValue,
    SpTemporalReference,
    SpProportionality,
    SpScenario,
    SpLegend,
    SpDictionary,
)

from data_validate.validators import (
    SpellCheckerValidator,
    ValidatorStructureFiles,
    SpDescriptionValidator,
    SpValueValidator,
    SpCompositionTreeValidator,
    SpTemporalReferenceValidator,
    SpScenarioValidator,
    SpLegendValidator,
)

FLAG = None


class ProcessorSpreadsheet:
    """
    Classe principal para processar as planilhas, validar dados e gerar relatórios.
    """

    def __init__(self, context: GeneralContext):
        # SETUP GENERAL CONTEXT
        self.context = context

        # CONFIGURE VARIABLES
        self.language_manager = self.context.locale_manager
        self.TITLES_INFO = self.context.config.get_verify_names()

        # SETUP CONFIGURE VARIABLES
        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder

        # Setup kwargs for model initialization
        self.scenarios_list = []

        # OBJECTS AND ARRAYS
        self.all_load_data = None
        self.data_loader_facade = None
        self.kwargs = None

        self.data_models_context: DataModelsContext | None = None
        self.models_to_use = []
        self.classes_to_initialize = [
            SpDescription,
            SpComposition,
            SpValue,
            SpTemporalReference,
            SpProportionality,
            SpScenario,
            SpLegend,
            SpDictionary,
        ]
        self.report_list = ModelListReport(context=self.context)

        # Running the main processing function
        self.context.logger.info(data_validate.__text_init__)

        self.run()

    def _prepare_statement(self) -> None:
        self.context.logger.info("Preparing statements and environment...")
        for name in NamesEnum:
            self.report_list.add_by_name(self.TITLES_INFO[name.value])

    def _read_data(self) -> None:
        self.context.logger.info("Data reading and preprocessing...")

        # 0 ETL: Extract, Transform, Load
        self.data_loader_facade = DataLoaderFacade(self.input_folder)
        self.all_load_data, errors_data_importer = self.data_loader_facade.load_all
        self.report_list.extend(
            self.TITLES_INFO[NamesEnum.FS.value], errors=errors_data_importer
        )

        # Verify scenarios and legend existence
        if self.all_load_data[SpScenario.CONSTANTS.SP_NAME].read_success and (
            SpScenario.RequiredColumn.COLUMN_SYMBOL.name
            in self.all_load_data[SpScenario.CONSTANTS.SP_NAME].df_data.columns
        ):
            self.scenarios_list = (
                self.all_load_data[SpScenario.CONSTANTS.SP_NAME]
                .df_data[SpScenario.RequiredColumn.COLUMN_SYMBOL.name]
                .unique()
                .tolist()
            )
        # Setup kwargs for model initialization
        self.kwargs = {
            SpModelABC.VAR_CONSTS.SCENARIO_EXISTS_FILE: self.all_load_data[
                SpScenario.CONSTANTS.SP_NAME
            ].exists_file,
            SpModelABC.VAR_CONSTS.SCENARIO_READ_SUCCESS: self.all_load_data[
                SpScenario.CONSTANTS.SP_NAME
            ].read_success,
            SpModelABC.VAR_CONSTS.SCENARIOS_LIST: self.scenarios_list,
            SpModelABC.VAR_CONSTS.LEGEND_EXISTS_FILE: self.all_load_data[
                SpLegend.CONSTANTS.SP_NAME
            ].exists_file,
            SpModelABC.VAR_CONSTS.LEGEND_READ_SUCCESS: self.all_load_data[
                SpLegend.CONSTANTS.SP_NAME
            ].read_success,
        }

    def _configure(self) -> None:
        self.context.logger.info("Configuring the processor...")
        # 1.2 SPECIFIC STRUCTURE VALIDATION ERRORS: Errors from the specific structure validation
        for model_class in self.classes_to_initialize:
            sp_name_key = model_class.CONSTANTS.SP_NAME

            # Dynamically create the attribute name, e.g., "sp_description"
            attribute_name = f"sp_{sp_name_key.lower()}"

            # Model instance creation and initialization
            model_instance = model_class(
                context=self.context,
                data_model=self.all_load_data.get(sp_name_key),
                **self.kwargs,
            )
            setattr(self, attribute_name, model_instance)
            self.models_to_use.append(model_instance)

            self.report_list.extend(
                self.TITLES_INFO[NamesEnum.FS.value],
                errors=model_instance.structural_errors,
                warnings=model_instance.structural_warnings,
            )
            self.report_list.extend(
                self.TITLES_INFO[NamesEnum.FC.value],
                errors=model_instance.data_cleaning_errors,
                warnings=model_instance.data_cleaning_warnings,
            )

            if FLAG is not None:
                self.context.logger.info(
                    f"Initialized model: {attribute_name} = {model_instance}"
                )

    def _build_pipeline(self) -> None:
        """
        Build the validation pipeline by initializing the data context and running the validations.
        """
        self.context.logger.info("Building validation pipeline...")

        # Create the DataContext with the initialized models
        self.data_models_context = DataModelsContext(
            context=self.context, models_to_use=self.models_to_use
        )

        # RUN ALL VALIDATIONS PIPELINE

        # 1 STRUCTURE_VALIDATION: Validate the structure of the data
        ValidatorStructureFiles(
            data_models_context=self.data_models_context, report_list=self.report_list
        )

        SpDescriptionValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )
        SpCompositionTreeValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )
        SpTemporalReferenceValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )
        SpValueValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )

        SpellCheckerValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )

        SpScenarioValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )
        SpLegendValidator(
            data_models_context=self.data_models_context, report_list=self.report_list
        )

    def _report(self) -> None:
        self.context.logger.info("Generating reports...")
        # Debug all reports and their errors
        if self.context.data_args.data_action.debug:
            self.context.logger.info("\nModo DEBUG ativado.")
            self.context.logger.info(
                "------ Resultados da verificação dos testes ------"
            )

            for report in self.report_list:
                self.context.logger.info(f"Report: {report.name_test}")
                self.context.logger.error(f"  Errors: {len(report.errors)}")
                for error in report.errors:
                    self.context.logger.error(f"    - {error}")
                self.context.logger.warning(f"  Warnings: {len(report.warnings)}")
                for warning in report.warnings:
                    self.context.logger.warning(f"    - {warning}")
                self.context.logger.info(
                    "---------------------------------------------------------------"
                )

        # Set summary of total errors and warnings
        total_errors = sum(len(report.errors) for report in self.report_list)
        total_warnings = sum(len(report.warnings) for report in self.report_list)

        if self.context.data_args.data_action.debug:
            self.context.logger.error(f"Total errors: {total_errors}")
            self.context.logger.warning(f"Total warnings: {total_warnings}")

        # Generate report in HTML and PDF formats
        ReportGeneratorFiles(context=self.context).build_report(
            report_list=self.report_list
        )

    def run(self):
        self.context.logger.info("Starting processing...")

        self._prepare_statement()
        self._read_data()
        self._configure()
        self._build_pipeline()
        self._report()
