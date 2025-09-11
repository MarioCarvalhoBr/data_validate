#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Tree composition validation for spreadsheet composition structures."""
from typing import List, Tuple, Dict, Any

import pandas as pd
from pandas import DataFrame

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import (
    SpModelABC,
    SpComposition,
    SpDescription,
    SpValue,
    SpProportionality,
)
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)

from data_validate.helpers.common.processing.data_cleaning import (
    clean_dataframe_integers,
)
from data_validate.helpers.common.processing.collections_processing import (
    find_differences_in_two_set_with_message,
    extract_numeric_integer_ids_from_list,
)
from data_validate.helpers.common.validation.data_validation import check_dataframe_titles_uniques
from data_validate.helpers.common.validation.graph_processing import GraphProcessing


class SpCompositionGraphValidator(ValidatorModelABC):
    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the tree validator with required context and models.

        Args:
            data_models_context: Context containing all data models
            report_list: Report list for validation results
            **kwargs: Additional keyword arguments
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
        self.model_dataframes: Dict[str, pd.DataFrame] = {}
        self.graph_processing: GraphProcessing | None = None

        self._prepare_statement()
        self.run()

    def _prepare_statement(self) -> None:
        """Prepare validation context and column mappings."""
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
        df_composition, _ = clean_dataframe_integers(
            df=df_composition,
            file_name=self.sp_name_composition,
            columns_to_clean=[self.column_name_parent],
            min_value=0,
        )
        df_composition, _ = clean_dataframe_integers(
            df=df_composition,
            file_name=self.sp_name_composition,
            columns_to_clean=[self.column_name_child],
            min_value=1,
        )
        self.graph_processing = GraphProcessing(
            dataframe=df_composition,
            parent_column=self.column_name_parent,
            child_column=self.column_name_child,
        )

    def validate_relation_indicators_in_composition(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all indicators in composition exist in description.

        Returns:
            Tuple containing (errors, warnings) lists
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Somente com dados de descricao e composicao (deve ser igual, apenas extrair)
        local_requeired_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
            ],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_requeired_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Extract valid description codes
        list_codes = self.model_sp_description.RequiredColumn.COLUMN_CODE.astype(str).to_list()
        valid_description_codes, _ = extract_numeric_integer_ids_from_list(id_values_list=list(set(list_codes)))

        list_parents = self.model_sp_composition.RequiredColumn.COLUMN_PARENT_CODE.astype(str).to_list()
        valid_compositions_parent_codes, _ = extract_numeric_integer_ids_from_list(id_values_list=list(set(list_parents)))
        list_childs = self.model_sp_composition.RequiredColumn.COLUMN_CHILD_CODE.astype(str).to_list()
        valid_compositions_childs_codes, _ = extract_numeric_integer_ids_from_list(id_values_list=list(set(list_childs)))

        # Compare codes between description and values
        comparison_errors = find_differences_in_two_set_with_message(
            first_set=valid_description_codes,
            label_1=self.sp_name_description,
            second_set=valid_compositions_parent_codes.union(valid_compositions_childs_codes),
            label_2=self.sp_name_composition,
        )
        errors.extend(comparison_errors)

        return errors, warnings

    def validate_relations_hierarchy_with_graph(self) -> Tuple[List[str], List[str]]:
        """
        Validate tree composition structure and detect cycles.

        Returns:
            Tuple containing (errors, warnings) lists
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Somente com dados de descricao e composicao (deve ser igual, apenas extrair)
        local_requeired_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_requeired_columns, self.model_dataframes)
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
        errors: List[str] = []
        warnings: List[str] = []

        local_requeired_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
                SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
            ],
        }

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(local_requeired_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Create working copies and clean data
        df_description: DataFrame = self.model_dataframes[self.sp_name_description].copy()
        root_node = "1"
        column_plural_simple_name = SpDescription.PluralColumn.COLUMN_PLURAL_SIMPLE_NAME.name
        column_plural_complete_name = SpDescription.PluralColumn.COLUMN_PLURAL_COMPLETE_NAME.name

        # Clean integer columns: df_description
        df_description, _ = clean_dataframe_integers(
            df=df_description,
            file_name=self.sp_name_description,
            columns_to_clean=[self.column_name_code],
            min_value=1,
        )
        comparison_errors, __ = self.validate_relation_indicators_in_composition()
        if comparison_errors:
            return errors, warnings

        existe_ciclo, __ = self.graph_processing.detect_cycles()
        if existe_ciclo:
            return errors, warnings

        grafos_desconectados = self.graph_processing.detect_disconnected_components()
        if grafos_desconectados:
            return errors, warnings

        # Verifica se existe pelo menos 1 nó pai == 1, senão, mostrar erro e solicitar correção
        if not self.graph_processing.graph.has_node("1"):
            errors.append(f"{self.sp_name_composition}: Nó raiz '{root_node}' não encontrado.")
            return errors, warnings

        # Convert the graph to a tree
        tree = self.graph_processing.convert_to_tree(root_node)

        # All children of root node (1)
        childs_root_node = list(tree.neighbors(root_node))

        # Para cada filho de 1, pegar toda a sub-arvore abaixo
        for child in childs_root_node:
            # Rodar um BFS a partir do filho
            sub_tree = self.graph_processing.breadth_first_search_from_node(child)

            # Monta uma lista somente com os código dos nós
            nodes = list(sub_tree.nodes())

            # Busca todos um sub-dataframe de descrição com os códigos (SP_DESCRIPTION_COLUMNS.CODIGO) que estão na lista_nos
            df_slice_description = df_description[df_description[self.column_name_code].astype(str).isin(nodes)]

            # Check if the titles are unique
            warnings_i = check_dataframe_titles_uniques(
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
        local_requeired_columns = {
            self.sp_name_composition: self.global_required_columns[self.sp_name_composition],
            self.sp_name_value: self.global_required_columns[self.sp_name_value],
        }

        if self.model_sp_proportionality.data_loader_model.read_success:
            local_requeired_columns[self.sp_name_proportionality] = [SpProportionality.RequiredColumn.COLUMN_ID.name]

        column_errors = self.check_columns_in_models_dataframes(local_requeired_columns, self.model_dataframes)

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
        Execute all tree validation checks.

        Returns:
            Tuple containing (errors, warnings) lists
        """
        validations = [
            (self.validate_relation_indicators_in_composition, NamesEnum.IR.value),
            (self.validate_relations_hierarchy_with_graph, NamesEnum.IR.value),
            (self.validate_unique_titles_with_graph, NamesEnum.UT.value),
            (self.validate_associated_indicators_leafs, NamesEnum.LEAF_NO_DATA.value),
        ]

        if self.model_sp_composition.data_loader_model.df_data.empty or self.model_sp_description.data_loader_model.df_data.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        self.build_reports(validations)

        return self._errors, self._warnings
