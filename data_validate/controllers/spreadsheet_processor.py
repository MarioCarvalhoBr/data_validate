#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for processing spreadsheet data validation workflows.

This module defines the `SpreadsheetProcessor` class, which orchestrates the entire
data validation pipeline: loading data, initializing models, running validators,
aggregating results, and generating reports.
"""

import os
import time
from datetime import datetime
from pathlib import Path

import data_validate
import data_validate.config as config
import data_validate.controllers as controllers
import data_validate.helpers.tools as tools
import data_validate.models as models
from data_validate.rules import (
    COMPOSITION_REGISTRY,
    DESCRIPTION_REGISTRY,
    Engine,
    LEGEND_REGISTRY,
    PROPORTIONALITY_REGISTRY,
    RuleContext,
    RuleRegistry,
    SCENARIO_REGISTRY,
    SPELL_REGISTRY,
    STRUCTURE_REGISTRY,
    TEMPORAL_REGISTRY,
    VALUE_REGISTRY,
    compute_composition_facts,
    extend_report_from_outcomes,
)


class SpreadsheetProcessor:
    """
    Main processor class for spreadsheet validation and report generation.

    Orchestrates the data validation pipeline by coordinating data loading,
    model initialization, validation execution (structure, spelling, business rules),
    and result reporting.

    Attributes:
        context (GeneralContext): The application's dependency injection context.
        language_manager (LanguageManager): Localization manager for internationalized strings.
        validation_titles (Dict[str, str]): Dictionary mapping validation keys to human-readable titles.
        input_folder (str): Directory path containing input data files.
        output_folder (str): Directory path for generating output reports.
        scenarios (List[str]): List of detected scenarios (e.g., SSPs) from scenario file.
        raw_data_map (Dict[str, Any]): Raw data loaded from files via DataLoaderFacade.
        data_loader_facade (DataLoaderFacade): Facade handles reading/parsing input files.
        model_configurations (Dict[str, Any]): Shared arguments passed to model constructors.
        data_models_context (DataModelContext): Specialized context holding initialized data models.
        initialized_models (List[SpModelABC]): List of instantiated spreadsheet models.
        target_model_classes (List[Type[SpModelABC]]): List of model classes to process.
        validation_reports (ValidationReport): Aggregator for validation errors and warnings.
    """

    def __init__(self, context: controllers.GeneralContext):
        """
        Initialize the processor: store dependencies and prepare report structures.

        ARC-001: construction no longer triggers the `run()` pipeline as a side effect —
        callers construct a `SpreadsheetProcessor`, then explicitly call `run()`
        (`data_validate/main.py::main`).

        Args:
            context (GeneralContext): The main application context.
        """
        # SETUP GENERAL CONTEXT
        self.context = context

        # CONFIGURE VARIABLES
        self.language_manager = self.context.language_manager
        self.validation_titles = self.context.config.get_verify_names()

        # SETUP CONFIGURE VARIABLES
        self.input_folder = self.context.data_args.data_file.input_folder
        self.output_folder = self.context.data_args.data_file.output_folder

        # Setup model_configurations for model initialization
        self.scenarios = []

        # OBJECTS AND ARRAYS
        self.raw_data_map = None
        self.data_loader_facade = None
        self.model_configurations = None

        self.data_models_context: controllers.DataModelContext | None = None
        self.initialized_models = []
        self.target_model_classes = [
            models.SpDescription,
            models.SpComposition,
            models.SpValue,
            models.SpTemporalReference,
            models.SpProportionality,
            models.SpScenario,
            models.SpLegend,
            models.SpDictionary,
        ]
        self.validation_reports = controllers.ValidationReport(context=self.context)

        self._spell_backend = None

    def _prepare_statement(self) -> None:
        """
        Initialize the report structure with all known test categories.

        Pre-populates the `validation_reports` with empty reports for all validation
        categories defined in `NamesEnum` to ensure consistent reporting order.
        """
        self.context.logger.info("Preparing statements and environment...")
        for name in config.NamesEnum:
            self.validation_reports.add_by_name(self.validation_titles[name.value])

    def _read_data(self) -> None:
        """
        Execute the ETL (Extract) phase of the pipeline.

        Uses `DataLoaderFacade` to read all authorized files from the input folder.
        Populates `raw_data_map`, captures initial load errors (e.g., file not found),
        and extracts global metadata (e.g., available scenarios) for downstream validations.
        """
        self.context.logger.info("Data reading and preprocessing...")

        # 0 ETL: Extract, Transform, Load
        self.data_loader_facade = tools.DataLoaderFacade(
            self.input_folder,
            translate=self.language_manager.text,
            limits=(
                self.context.config.MAX_INPUT_FILE_BYTES,
                self.context.config.MAX_SHEET_ROWS,
                self.context.config.MAX_SHEET_COLUMNS,
            ),
        )
        load_result = self.data_loader_facade.load()
        self.raw_data_map, load_errors = load_result.models, load_result.errors
        self.validation_reports.extend(self.validation_titles[config.NamesEnum.FS.value], errors=load_errors)

        # Verify scenarios and legend existence
        if self.raw_data_map[models.SpScenario.CONSTANTS.SP_NAME].is_read_successful and (
            models.SpScenario.RequiredColumn.COLUMN_SYMBOL.name
            in self.raw_data_map[models.SpScenario.CONSTANTS.SP_NAME].raw_data.columns
        ):
            self.scenarios = (
                self.raw_data_map[models.SpScenario.CONSTANTS.SP_NAME]
                .raw_data[models.SpScenario.RequiredColumn.COLUMN_SYMBOL.name]
                .unique()
                .tolist()
            )
        # Setup model_configurations for model initialization
        self.model_configurations = {
            models.SpModelABC.VAR_CONSTS.SCENARIO_EXISTS_FILE: self.raw_data_map[
                models.SpScenario.CONSTANTS.SP_NAME
            ].does_file_exist,
            models.SpModelABC.VAR_CONSTS.SCENARIO_READ_SUCCESS: self.raw_data_map[
                models.SpScenario.CONSTANTS.SP_NAME
            ].is_read_successful,
            models.SpModelABC.VAR_CONSTS.SCENARIOS: self.scenarios,
            models.SpModelABC.VAR_CONSTS.LEGEND_EXISTS_FILE: self.raw_data_map[
                models.SpLegend.CONSTANTS.SP_NAME
            ].does_file_exist,
            models.SpModelABC.VAR_CONSTS.LEGEND_READ_SUCCESS: self.raw_data_map[
                models.SpLegend.CONSTANTS.SP_NAME
            ].is_read_successful,
        }

    def _configure(self) -> None:
        """
        Configure models and execute initial structural/cleaning validations.

        Instantiates specific spreadsheet models (e.g., `SpDescription`, `SpValue`).
        During initialization, models perform:
        1. Structural checks (required columns presence).
        2. Data cleaning (type conversion, trimming).

        Collected structural and cleaning errors are immediately added to the report.
        """
        self.context.logger.info("Configuring the processor...")
        # 1.2 SPECIFIC STRUCTURE VALIDATION ERRORS: Errors from the specific structure validation
        for model_class in self.target_model_classes:
            sp_name_key = model_class.CONSTANTS.SP_NAME

            # Dynamically create the attribute name, e.g., "sp_description"
            attribute_name = f"sp_{sp_name_key.lower()}"

            # Model instance creation; ARC-001: construction no longer runs the pipeline as a
            # side effect, so `run()` is called explicitly right after construction.
            model_instance = model_class(
                context=self.context,
                data_model=self.raw_data_map.get(sp_name_key),
                **self.model_configurations,
            )
            model_instance.run()
            setattr(self, attribute_name, model_instance)
            self.initialized_models.append(model_instance)

            self.validation_reports.extend(
                self.validation_titles[config.NamesEnum.FS.value],
                errors=model_instance.structural_errors,
                warnings=model_instance.structural_warnings,
            )
            self.validation_reports.extend(
                self.validation_titles[config.NamesEnum.FC.value],
                errors=model_instance.data_cleaning_errors,
                warnings=model_instance.data_cleaning_warnings,
            )

    def _build_rule_context(self) -> RuleContext:
        """
        Build the single, shared `RuleContext` every rule registry in this pipeline reads from.

        Assembles it from data already available once `_configure()` has run: every initialized
        model's own working frame (`model.frame`, BUG-002/BUG-003-safe) and cleaned columns
        (`model.cleaned`), keyed by sheet name; plus the input-folder listing, scenarios, and the
        CLI flags/limits a description-domain rule needs (ARC-017 Phase 3 Port 2). Reused,
        unchanged, by every `_run_rule_registries` call in `_build_pipeline` — one `RuleContext`
        per run, not one per registry.

        Builds the context twice (BUG-019): a first, otherwise-complete `RuleContext` is used to
        compute `composition_facts` once (`compute_composition_facts`) — the graph/tree/relation
        facts every `COMP-*` rule reads instead of recomputing — then a second, final
        `RuleContext` is returned with that result injected into `options`. Neither build copies
        any sheet/cleaned data; both are cheap mapping-shell constructions.

        Also constructs the `SpellChecker` backend once (ARC-017 Phase 3 Port 8), stored on
        `self._spell_backend` (so `_build_pipeline` can release its resources after the SPELL
        registry runs) and injected into `options["spell_backend"]` for `rules/spell.py`'s
        `SPELL-002`…`004` to call; built unconditionally, matching the legacy
        `SpellCheckerValidator.__init__`'s own unconditional `SpellChecker(...)` construction —
        `--no-spellchecker` only skips the per-model column checks (BUG-027: the dictionary/
        backend errors must still surface).

        Returns:
            RuleContext: The shared context for this run.
        """
        description_model = self.data_models_context.get_instance_of(models.SpDescription)
        legend_model = self.data_models_context.get_instance_of(models.SpLegend)
        dictionary_model = self.data_models_context.get_instance_of(models.SpDictionary)

        self._spell_backend = tools.SpellChecker(
            self.context.data_args.data_file.locale,
            dictionary_model.words_to_ignore if dictionary_model else [],
        )

        sheets = {model.CONSTANTS.SP_NAME: model.frame for model in self.initialized_models}
        cleaned = {model.CONSTANTS.SP_NAME: dict(model.cleaned) for model in self.initialized_models}
        base_options = {
            "input_folder": Path(self.input_folder),
            "dir_entries": os.listdir(self.input_folder),
            "scenarios": self.scenarios,
            "filenames": {model.CONSTANTS.SP_NAME: model.filename for model in self.initialized_models},
            "no_warning_titles_length": self.context.data_args.data_action.no_warning_titles_length,
            "expected_columns": tuple(description_model.EXPECTED_COLUMNS) if description_model else (),
            "title_max_length": self.context.config.TITLE_OVER_N_CHARS,
            "simple_desc_max_length": self.context.config.SIMPLE_DESCRIPTIONS_OVER_N_CHARS,
            "proportionality_read_successful": self.raw_data_map[
                models.SpProportionality.CONSTANTS.SP_NAME
            ].is_read_successful,
            "scenario_exists_file": self.model_configurations[models.SpModelABC.VAR_CONSTS.SCENARIO_EXISTS_FILE],
            "legend_sanity_ok": legend_model.is_sanity_check_passed if legend_model else False,
            "legend_read_success": self.model_configurations[models.SpModelABC.VAR_CONSTS.LEGEND_READ_SUCCESS],
            "min_lower_legend_default": models.SpLegend.CONSTANTS.MIN_LOWER_LEGEND_DEFAULT,
            "max_upper_legend_default": models.SpLegend.CONSTANTS.MAX_UPPER_LEGEND_DEFAULT,
            "label_data_unavailable": self.context.config.LABEL_DATA_UNAVAILABLE,
            "value_data_unavailable": self.context.config.VALUE_DATA_UNAVAILABLE,
            "precision_decimal_place_truncate": self.context.config.PRECISION_DECIMAL_PLACE_TRUNCATE,
            "current_language": self.language_manager.current_language,
            "spell_backend": self._spell_backend,
            "no_spellchecker": self.context.data_args.data_action.no_spellchecker,
        }

        preliminary_context = RuleContext(
            sheets=sheets,
            cleaned=cleaned,
            options=base_options,
            translate=self.language_manager.text,
            clock=datetime.now,
        )
        composition_facts = compute_composition_facts(preliminary_context)

        return RuleContext(
            sheets=sheets,
            cleaned=cleaned,
            options={**base_options, "composition_facts": composition_facts},
            translate=self.language_manager.text,
            clock=datetime.now,
        )

    def _run_rule_registries(self, registries: list[RuleRegistry], ctx: RuleContext) -> None:
        """
        Run one or more rule registries over the shared `ctx` and render their issues.

        Generalises the former `_run_structure_rules` (ARC-017 Phase 3b) so every later
        validator port (description, composition, ...) reuses the same call shape instead of
        each writing its own `Engine(...).run(...)` + `extend_report_from_outcomes(...)` pair.

        Args:
            registries: The rule registries to execute, in order; each is run independently
                (an `Engine` per registry), but all against the same `ctx`.
            ctx: The shared `RuleContext` built by `_build_rule_context`.
        """
        for registry in registries:
            result = Engine(registry).run(ctx)
            extend_report_from_outcomes(
                result.outcomes,
                translate=self.language_manager.text,
                report=self.validation_reports,
                titles=self.validation_titles,
            )

    def _build_pipeline(self) -> None:
        """
        Construct and execute the main validation pipeline.

        Initializes the `DataModelContext` with the configured models and runs
        a sequence of validators:
        1. **Structure**: File structure checks.
        2. **Spelling**: Spell checking on text fields.
        3. **Mandatory**: Core business rules (Description, Composition, Temporal Reference).
        4. **Optional**: Secondary business rules (Proportionality, Values, Scenarios, Legends).
        """
        self.context.logger.info("Building validation pipeline...")

        # Create the DataContext with the initialized models
        self.data_models_context = controllers.DataModelContext(
            context=self.context, initialized_models=self.initialized_models
        )

        # One shared, immutable RuleContext for every rule registry this pipeline runs.
        rule_context = self._build_rule_context()

        # RUN ALL VALIDATIONS PIPELINE

        # 1. Validate the structure of the data (ARC-017 Phase 3b: ported to the rules engine)
        self._run_rule_registries([STRUCTURE_REGISTRY], rule_context)

        # 2. Validate the spelling of the data (ARC-017 Phase 3 Port 8, ported to the rules
        # engine, replacing the deleted `validators.SpellCheckerValidator`)
        self._run_rule_registries([SPELL_REGISTRY], rule_context)
        self._spell_backend.clean_files_generated()

        # 3. Validate spreadsheet data mandatory (description: ARC-017 Phase 3 Port 2;
        # composition: ARC-017 Phase 3 Port 3, ported to the rules engine, replacing the
        # deleted `validators.SpCompositionGraphValidator`/`SpCompositionTreeValidator`;
        # temporal reference: ARC-017 Phase 3 Port 4, replacing the deleted
        # `validators.SpTemporalReferenceValidator`)
        self._run_rule_registries([DESCRIPTION_REGISTRY, COMPOSITION_REGISTRY], rule_context)
        self._run_rule_registries([TEMPORAL_REGISTRY], rule_context)

        # 4. Validate spreadsheet data optional (proportionality: ARC-017 Phase 3 Port 7, ported
        # to the rules engine, replacing the deleted `validators.SpProportionalityValidator`;
        # value: ARC-017 Phase 3 Port 5, ported to the rules engine, replacing the deleted
        # `validators.SpValueValidator`; scenario: ARC-017 Phase 3 Port 4, ported to the rules
        # engine, replacing the deleted `validators.SpScenarioValidator`; legend: ARC-017 Phase 3
        # Port 6, ported to the rules engine, replacing the deleted
        # `validators.SpLegendValidator`)
        self._run_rule_registries([PROPORTIONALITY_REGISTRY], rule_context)
        self._run_rule_registries([VALUE_REGISTRY], rule_context)
        self._run_rule_registries([SCENARIO_REGISTRY], rule_context)
        self._run_rule_registries([LEGEND_REGISTRY], rule_context)

    def _report(self) -> None:
        """
        Generate final validation reports.

        Compiles all collected errors and warnings into `ValidationReport`,
        logs debug information (if enabled), calculates summary statistics,
        and triggers the generation of HTML/PDF reports via `FileReportGenerator`.
        """
        self.context.logger.info("Generating reports...")
        # Debug all reports and their errors
        if self.context.data_args.data_action.debug:
            self.context.logger.info("\nModo DEBUG ativado.")
            self.context.logger.info("------ Resultados da verificação dos testes ------")

            for report in self.validation_reports:
                self.context.logger.info(f"Report: {report.test_name}")
                self.context.logger.error(f"  Errors: {len(report.errors)}")
                for error in report.errors:
                    self.context.logger.error(f"    - {error}")
                self.context.logger.warning(f"  Warnings: {len(report.warnings)}")
                for warning in report.warnings:
                    self.context.logger.warning(f"    - {warning}")
                self.context.logger.info("---------------------------------------------------------------")

        # Set summary of total errors and warnings
        total_errors = sum(len(report.errors) for report in self.validation_reports)
        total_warnings = sum(len(report.warnings) for report in self.validation_reports)

        if self.context.data_args.data_action.debug:
            self.context.logger.error(f"Total errors: {total_errors}")
            self.context.logger.warning(f"Total warnings: {total_warnings}")

        # Generate report in HTML and PDF formats
        controllers.FileReportGenerator(context=self.context).build_report(report_list=self.validation_reports)

    def run(self):
        """
        Execute the complete processing workflow.

        Orchestrates the sequential execution of:
        1. `_prepare_statement()`: Setup.
        2. `_read_data()`: Data loading.
        3. `_configure()`: Model initialization and cleaning.
        4. `_build_pipeline()`: Core validation logic.
        5. `_report()`: Output generation.

        ARC-001: this used to run automatically from `__init__`; callers (`main.py::main`) now
        construct a `SpreadsheetProcessor`, then call `run()` explicitly. The welcome banner and
        the total-execution-time print (both previously in `__init__`, around the old
        `self.run()` call) moved here unchanged, so timing still covers exactly the same work.
        """
        self.context.logger.info(data_validate.__welcome__)
        start_time = time.time()

        self.context.logger.info("Starting processing...")

        self._prepare_statement()
        self._read_data()
        self._configure()
        self._build_pipeline()
        self._report()

        # End time measurement if --no-time is not set
        if not self.context.data_args.data_action.no_time:
            print("Tempo total de execução: " + str(round(time.time() - start_time, 1)) + " segundos")
