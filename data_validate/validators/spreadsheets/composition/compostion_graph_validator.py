#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Tree composition validation for spreadsheet composition structures."""

from typing import List, Tuple, Dict, Any

import pandas as pd

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


class SpCompositionGraphValidator(ValidatorModelABC):
    """
    Validates hierarchical tree structures in SpComposition spreadsheets.

    This validator ensures that composition data forms a valid tree structure
    without cycles and maintains proper level hierarchies between parent and
    child indicator relationships.

    Attributes:
        model_sp_composition: SpComposition model instance
        model_sp_description: SpDescription model instance
        sp_name_description: Description spreadsheet filename
        sp_name_composition: Composition spreadsheet filename
        column_name_code: Code column name from description
        column_name_level: Level column name from description
        column_name_parent: Parent code column name from composition
        column_name_child: Child code column name from composition
        global_required_columns: Required columns mapping
        model_dataframes: DataFrames mapping
    """

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
        self.column_name_level: str = ""

        self.column_name_id: str = ""

        self.global_required_columns: Dict[str, List[str]] = {}
        self.model_dataframes: Dict[str, pd.DataFrame] = {}

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
        self.column_name_level = SpDescription.RequiredColumn.COLUMN_LEVEL.name

        self.column_name_id = SpValue.RequiredColumn.COLUMN_ID.name

        # Define required columns
        self.global_required_columns = {
            self.sp_name_composition: [
                SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name,
                SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name,
            ],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_LEVEL.name,
            ],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_proportionality: [SpProportionality.RequiredColumn.COLUMN_ID.name],
        }

        # Set dataframes
        self.model_dataframes = {
            self.sp_name_composition: self.model_sp_composition.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_proportionality: self.model_sp_proportionality.data_loader_model.df_data,
        }

    def validate_relation_indicators_in_composition(
        self,
    ) -> Tuple[List[str], List[str]]:
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
        valid_description_codes, _ = extract_numeric_integer_ids_from_list(
            id_values_list=list(set(self.model_sp_description.RequiredColumn.COLUMN_CODE.to_list().astype(str)))
        )

        list_parents = self.model_sp_composition.RequiredColumn.COLUMN_PARENT_CODE.to_list()
        valid_compositions_parent_codes, _ = extract_numeric_integer_ids_from_list(id_values_list=list(set(list_parents.astype(str))))
        list_childs = self.model_sp_composition.RequiredColumn.COLUMN_CHILD_CODE.to_list()
        valid_compositions_childs_codes, _ = extract_numeric_integer_ids_from_list(id_values_list=list(set(list_childs.astype(str))))

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

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(self.global_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        # Create working copies and clean data
        df_composition = self.model_dataframes[self.sp_name_composition].copy()
        df_description = self.model_dataframes[self.sp_name_description].copy()
        df_value = self.model_dataframes[self.sp_name_value].copy()

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

        # Clean integer columns: df_description
        df_description, _ = clean_dataframe_integers(
            df=df_description,
            file_name=self.sp_name_description,
            columns_to_clean=[self.column_name_code, self.column_name_level],
            min_value=1,
        )

        return errors, warnings

    def validate_unique_titles_with_graph(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all children of the same parent have the same level.

        Returns:
            Tuple containing (errors, warnings) lists
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(self.global_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        return errors, warnings

    def validate_associated_indicators_leafs(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all children of the same parent have the same level.

        Returns:
            Tuple containing (errors, warnings) lists
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
        column_errors = self.check_columns_in_models_dataframes(self.global_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all tree validation checks.

        Returns:
            Tuple containing (errors, warnings) lists
        """
        validations = [
            (self.validate_relation_indicators_in_composition, NamesEnum.IR.value),
            # (self.validate_relations_hierarchy_with_graph, NamesEnum.IR.value),
            # (self.validate_unique_titles_with_graph, NamesEnum.UT.value),
            # (self.validate_associated_indicators_leafs, NamesEnum.LEAF_NO_DATA.value)
        ]

        if self.model_sp_composition.data_loader_model.df_data.empty or self.model_sp_description.data_loader_model.df_data.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        self.build_reports(validations)

        return self._errors, self._warnings
