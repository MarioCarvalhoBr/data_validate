#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Graph composition validation for spreadsheet composition structures.

This module validates composition data using graph theory, detecting cycles, disconnected
components, and ensuring proper relationships between indicators across multiple models.
"""

from typing import List, Tuple, Dict, Any

from pandas import DataFrame

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing

from data_validate.helpers.common.validation.graph_processing import GraphProcessing
from data_validate.models import (
    SpModelABC,
    SpComposition,
    SpDescription,
    SpValue,
    SpProportionality,
)
from data_validate.validators.spreadsheets.base.validator_model_abc import ValidatorModelABC


class SpCompositionGraphValidator(ValidatorModelABC):
    """
    Validates composition structures using graph-based analysis.

    This validator uses graph theory to analyze composition hierarchies, detecting
    cycles, disconnected components, unique title constraints, and data associations
    for leaf indicators.

    Attributes
    ----------
    model_sp_composition : SpComposition
        Composition model instance containing parent-child relationships.
    model_sp_description : SpDescription | SpModelABC
        Description model instance containing indicator metadata.
    model_sp_value : SpValue
        Value model instance containing indicator data.
    model_sp_proportionality : SpProportionality
        Proportionality model instance containing indicator proportions.
    sp_name_composition : str
        Composition spreadsheet filename.
    sp_name_description : str
        Description spreadsheet filename.
    sp_name_value : str
        Value spreadsheet filename.
    sp_name_proportionality : str
        Proportionality spreadsheet filename.
    column_name_parent : str
        Parent code column name.
    column_name_child : str
        Child code column name.
    column_name_code : str
        Indicator code column name.
    column_name_simple_name : str
        Simple name column name.
    column_name_complete_name : str
        Complete name column name.
    column_name_id : str
        ID column name.
    global_required_columns : Dict[str, List[str]]
        Required columns mapping for validation.
    model_dataframes : Dict[str, DataFrame]
        DataFrames mapping for each model.
    graph_processing : GraphProcessing | None
        Graph processing utility for analysis.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the graph validator with required context and models.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all data models and configuration.
        report_list : ModelListReport
            Report list for validation results aggregation.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpComposition,
            **kwargs,
        )

        self.model_sp_composition = self._data_model
        self.model_sp_description: SpDescription | SpModelABC = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)
        self.model_sp_proportionality = self._data_models_context.get_instance_of(SpProportionality)

        # Initialize attributes
        self.sp_name_composition: str = ""
        self.sp_name_description: str = ""
        self.sp_name_value: str = ""
        self.sp_name_proportionality: str = ""

        self.column_name_parent: str = ""
        self.column_name_child: str = ""

        self.column_name_code: str = ""
        self.column_name_simple_name: str = ""
        self.column_name_complete_name: str = ""

        self.column_name_id: str = ""

        self.global_required_columns: Dict[str, List[str]] = {}
        self.model_dataframes: Dict[str, DataFrame] = {}
        self.graph_processing: GraphProcessing | None = None

        self._prepare_statement()
        self.run()

    def _prepare_statement(self) -> None:
        """
        Prepare validation context, column mappings, and graph processing.

        Sets up:
        - Spreadsheet names for all models
        - Column name mappings for validation
        - Required columns dictionary
        - DataFrame references for all models
        - Graph processing utility with cleaned composition data

        Notes
        -----
        Integer columns are cleaned during setup to ensure valid graph construction.
        """
        # Set spreadsheet names
        self.sp_name_composition = self.model_sp_composition.filename
        self.sp_name_description = self.model_sp_description.filename
        self.sp_name_value = self.model_sp_value.filename
        self.sp_name_proportionality = self.model_sp_proportionality.filename

        # Set column names
        self.column_name_parent = SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name
        self.column_name_child = SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name

        self.column_name_code = SpDescription.RequiredColumn.COLUMN_CODE.name
        self.column_name_simple_name = SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name
        self.column_name_complete_name = SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name

        self.column_name_id = SpValue.RequiredColumn.COLUMN_ID.name

        # Define required columns
        self.global_required_columns = {
            self.sp_name_composition: [
                SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name,
                SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name,
            ],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
            ],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
        }

        # Set dataframes
        self.model_dataframes = {
            self.sp_name_composition: self.model_sp_composition.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_proportionality: self.model_sp_proportionality.data_loader_model.df_data,
        }

        # Setup graph processing if composition data is available
        # Create working copies and clean data
        df_composition: DataFrame = self.model_dataframes[self.sp_name_composition].copy()

        # Clean integer columns: df_composition
        df_composition, _ = DataCleaningProcessing.clean_dataframe_integers(
            df=df_composition,
            file_name=self.sp_name_composition,
            columns_to_clean=[self.column_name_parent],
            min_value=0,
        )
        df_composition, _ = DataCleaningProcessing.clean_dataframe_integers(
            df=df_composition,
            file_name=self.sp_name_composition,
            columns_to_clean=[self.column_name_child],
            min_value=1,
        )
        # Configure processing helpers
        self.graph_processing = GraphProcessing(
            dataframe=df_composition,
            parent_column=self.column_name_parent,
            child_column=self.column_name_child,
        )

    def validate_relation_indicators_in_composition(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all indicators in composition exist in description.

        Ensures that every parent and child code referenced in the composition
        spreadsheet has a corresponding entry in the description spreadsheet.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for codes not found in description
                - List[str]: Warning messages (currently empty)

        Notes
        -----
        This validation is skipped if the description dataframe is empty.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if self.model_dataframes[self.sp_name_description].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_relation_indicators_in_composition,
                        NamesEnum.IR.value,
                    )
                ]
            )
            return errors, warnings

        # Only with description and composition data (should be equal, just extract)
        local_required_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
            ],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Extract valid description codes
        list_codes = self.model_sp_description.RequiredColumn.COLUMN_CODE.astype(str).to_list()
        valid_description_codes, _ = CollectionsProcessing.extract_numeric_integer_ids_from_list(id_values_list=list(set(list_codes)))

        # Extract valid composition parent
        list_parents = self.model_sp_composition.RequiredColumn.COLUMN_PARENT_CODE.astype(str).to_list()
        valid_compositions_parent_codes, _ = CollectionsProcessing.extract_numeric_integer_ids_from_list(id_values_list=list(set(list_parents)))

        # Extract valid composition child codes
        list_childs = self.model_sp_composition.RequiredColumn.COLUMN_CHILD_CODE.astype(str).to_list()
        valid_compositions_childs_codes, _ = CollectionsProcessing.extract_numeric_integer_ids_from_list(id_values_list=list(set(list_childs)))

        # Compare codes between description and values
        comparison_errors = CollectionsProcessing.find_differences_in_two_set_with_message(
            first_set=valid_description_codes,
            label_1=self.sp_name_description,
            second_set=valid_compositions_parent_codes.union(valid_compositions_childs_codes),
            label_2=self.sp_name_composition,
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_relations_hierarchy_with_graph(self) -> Tuple[List[str], List[str]]:
        """
        Detect cycles and disconnected components in the composition graph structure.

        Uses graph analysis to identify circular dependencies in parent-child
        relationships and disconnected indicator subgraphs, which would create
        invalid hierarchical structures.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for detected cycles and disconnected components
                - List[str]: Warning messages (currently empty)

        Notes
        -----
        - Cycles are formatted to show the complete path of the circular dependency
        - Disconnected components indicate isolated indicator groups not connected to main tree
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Only with description and composition data (should be equal, just extract)
        local_required_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        exists_cycle, cycle = self.graph_processing.detect_cycles()
        if exists_cycle:
            text_cycles = ""
            for source, target in cycle:
                text_cycles += f"{source} -> {target}, "
            errors.append(f"{self.sp_name_composition}: Ciclo encontrado: [{text_cycles[:-2]}].")

        graphs_disconnected = self.graph_processing.detect_disconnected_components()
        if graphs_disconnected:
            list_graphs_disconnected = []
            for i, grafo in enumerate(graphs_disconnected):
                text_disconnected = "[" + self.graph_processing.generate_graph_report(grafo) + "]"
                list_graphs_disconnected.append(text_disconnected)
            errors.append(f"{self.sp_name_composition}: Indicadores desconectados encontrados: " + ", ".join(list_graphs_disconnected) + ".")

        return errors, warnings

    def validate_unique_titles_with_graph(self) -> Tuple[List[str], List[str]]:
        """
        Validate uniqueness of indicator titles using graph analysis.

        Checks that simple names and complete names are unique within each subtree
        of the indicator hierarchy, using graph structure to determine sibling
        relationships. Validates by traversing from root node through all subtrees.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Empty list (no errors for title uniqueness issues)
                - List[str]: Warning messages for duplicate titles within same subtree

        Notes
        -----
        - This validation is skipped if the description dataframe is empty
        - Requires a valid tree structure without cycles or disconnected components
        - Root node must exist in the composition graph
        - Titles are checked within each subtree independently
        """
        errors: List[str] = []
        warnings: List[str] = []

        if self.model_dataframes[self.sp_name_description].empty:
            self.set_not_executed(
                [
                    (
                        self.validate_unique_titles_with_graph,
                        NamesEnum.UT.value,
                    )
                ]
            )
            return errors, warnings

        local_required_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
                SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
            ],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Create working copies and clean data
        df_description: DataFrame = self.model_dataframes[self.sp_name_description].copy()
        root_node = "1"
        column_plural_simple_name = SpDescription.PluralColumn.COLUMN_PLURAL_SIMPLE_NAME.name
        column_plural_complete_name = SpDescription.PluralColumn.COLUMN_PLURAL_COMPLETE_NAME.name

        # Clean integer columns: df_description
        df_description, _ = DataCleaningProcessing.clean_dataframe_integers(
            df=df_description,
            file_name=self.sp_name_description,
            columns_to_clean=[self.column_name_code],
            min_value=1,
        )
        comparison_errors, __ = self.validate_relation_indicators_in_composition()
        if comparison_errors:
            return errors, warnings

        exists_cycle, __ = self.graph_processing.detect_cycles()
        if exists_cycle:
            return errors, warnings

        graphs_disconnected = self.graph_processing.detect_disconnected_components()
        if graphs_disconnected:
            return errors, warnings

        # Check if there is at least 1 parent node == 1, otherwise show error and request correction
        if not self.graph_processing.graph.has_node("1"):
            errors.append(f"{self.sp_name_composition}: Nó raiz '{root_node}' não encontrado.")
            return errors, warnings

        # Convert the graph to a tree
        tree = self.graph_processing.convert_to_tree(root_node)

        # All children of root node (1)
        childs_root_node = list(tree.neighbors(root_node))

        # For each child of 1, get the entire subtree below
        for child in childs_root_node:
            # Run a BFS from the child
            sub_tree = self.graph_processing.breadth_first_search_from_node(child)

            # Build a list with only node codes
            nodes = list(sub_tree.nodes())

            # Search for a sub-dataframe from description with codes that are in the node list
            df_slice_description = df_description[df_description[self.column_name_code].astype(str).isin(nodes)]

            # Check if the titles are unique
            warnings_i = DataFrameProcessing.check_dataframe_titles_uniques(
                dataframe=df_slice_description,
                column_one=self.column_name_simple_name,
                column_two=self.column_name_complete_name,
                plural_column_one=column_plural_simple_name,
                plural_column_two=column_plural_complete_name,
            )
            # Add prefix to warnings
            warnings_i = [f"{self.sp_name_description}: {warning}" for warning in warnings_i]

            # Add to main warnings list
            warnings += warnings_i

        return errors, warnings

    def validate_associated_indicators_leafs(self) -> Tuple[List[str], List[str]]:
        """
        Validate that leaf indicators have associated data in value and proportionality.

        Checks that all leaf nodes (indicators with no children) have corresponding
        data entries in the value spreadsheet and optionally in the proportionality
        spreadsheet if it exists.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for leaf indicators without associated data
                - List[str]: Warning messages (currently empty)

        Notes
        -----
        - This validation is skipped if the value dataframe is empty
        - Proportionality validation is only performed if that model is available
        - Leaf nodes are determined from the composition graph structure
        """
        errors: List[str] = []
        warnings: List[str] = []

        if self.model_sp_value.data_loader_model.df_data.empty:
            self.set_not_executed(
                [
                    (
                        self.validate_associated_indicators_leafs,
                        NamesEnum.LEAF_NO_DATA.value,
                    )
                ]
            )
            return errors, warnings

        # Check required columns exist
        local_required_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_value: self.global_required_columns[self.sp_name_value],
        }

        if self.model_sp_proportionality.data_loader_model.read_success and not self.model_sp_proportionality.data_loader_model.df_data.empty:
            local_required_columns[self.sp_name_proportionality] = [SpProportionality.RequiredColumn.COLUMN_ID.name]

        column_errors = self.check_columns_in_models_dataframes(local_required_columns, self.model_dataframes)

        if column_errors:
            return column_errors, warnings

        # Create working copies and clean data
        df_value: DataFrame = self.model_dataframes[self.sp_name_value].copy()
        df_proportionality: DataFrame = self.model_dataframes[self.sp_name_proportionality].copy()

        leafs = self.graph_processing.get_leaf_nodes()

        # Validation for values
        codes_values = df_value.columns.tolist()
        codes_values = [code.split("-")[0] for code in codes_values]
        for leaf in leafs:
            if leaf not in codes_values:
                errors.append(f"{self.sp_name_value}: Indicador folha '{leaf}' não possui dados associados.")

        # Validation for proportionality (if available)
        if not df_proportionality.empty:
            level_two_columns = df_proportionality.columns.get_level_values(1).unique().tolist()

            if self.column_name_id in level_two_columns:
                level_two_columns.remove(self.column_name_id)

            level_two_columns = [col for col in level_two_columns if not col.startswith("Unnamed")]
            level_two_columns = [col for col in level_two_columns if not col.startswith("unnamed")]

            level_two_columns = [col.split("-")[0] for col in level_two_columns]
            all_columns = list(set(level_two_columns))

            # Check if all leaf codes are present in level_one_columns
            for leaf in leafs:
                if leaf not in all_columns:
                    errors.append(f"{self.sp_name_proportionality}: Indicador folha '{leaf}' não possui dados associados.")
        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all graph-based composition validations.

        Orchestrates the execution of all composition validators using graph analysis,
        including indicator relationships, hierarchy validation, title uniqueness,
        and leaf data associations.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        All validations are skipped if the composition dataframe is empty.
        """
        validations = [
            (self.validate_relation_indicators_in_composition, NamesEnum.IR.value),
            (self.validate_relations_hierarchy_with_graph, NamesEnum.IR.value),
            (self.validate_unique_titles_with_graph, NamesEnum.UT.value),
            (self.validate_associated_indicators_leafs, NamesEnum.LEAF_NO_DATA.value),
        ]

        if self.model_sp_composition.data_loader_model.df_data.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        self.build_reports(validations)

        return self._errors, self._warnings
