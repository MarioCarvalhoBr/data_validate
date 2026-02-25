#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Tree composition validation for spreadsheet composition structures.

This module validates that composition data forms valid tree hierarchies without cycles
and maintains proper level relationships between parent and child indicators.
"""

from typing import List, Tuple, Dict, Any

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_model_context import DataModelContext
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.tree_processing import TreeProcessing
from data_validate.models import SpComposition, SpDescription
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class SpCompositionTreeValidator(BaseValidator):
    """
    Validates hierarchical tree structures in SpComposition spreadsheets.

    This validator ensures that composition data forms a valid tree structure
    without cycles and maintains proper level hierarchies between parent and
    child indicator relationships.

    Attributes
    ----------
    model_sp_composition : SpComposition
        Composition model instance containing parent-child relationships.
    model_sp_description : SpDescription
        Description model instance containing indicator metadata and levels.
    sp_name_description : str
        Description spreadsheet filename.
    sp_name_composition : str
        Composition spreadsheet filename.
    column_name_code : str
        Code column name from description spreadsheet.
    column_name_level : str
        Level column name from description spreadsheet.
    column_name_parent : str
        Parent code column name from composition spreadsheet.
    column_name_child : str
        Child code column name from composition spreadsheet.
    global_required_columns : Dict[str, List[str]]
        Required columns mapping for validation.
    model_dataframes : Dict[str, pd.DataFrame]
        DataFrames mapping for each model.
    """

    def __init__(
        self,
        data_models_context: DataModelContext,
        validation_reports: ValidationReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the tree validator with required context and models.

        Args
        ----
        data_models_context : DataModelContext
            Context containing all data models and configuration.
        validation_reports : ValidationReport
            Report list for validation results aggregation.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            validation_reports=validation_reports,
            type_class=SpComposition,
            **kwargs,
        )

        self.model_sp_composition = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)

        # Initialize attributes
        self.sp_name_description: str = ""
        self.sp_name_composition: str = ""
        self.column_name_code: str = ""
        self.column_name_level: str = ""
        self.column_name_parent: str = ""
        self.column_name_child: str = ""
        self.global_required_columns: Dict[str, List[str]] = {}
        self.model_dataframes: Dict[str, pd.DataFrame] = {}

        self._prepare_statement()
        self.run()

    def _prepare_statement(self) -> None:
        """
        Prepare validation context and column mappings.

        Sets up:
        - Spreadsheet names for composition and description
        - Column name mappings for validation
        - Required columns dictionary
        - DataFrame references for both models
        """
        # Set spreadsheet names
        self.sp_name_composition = self.model_sp_composition.filename
        self.sp_name_description = self.model_sp_description.filename

        # Set column names
        self.column_name_code = SpDescription.RequiredColumn.COLUMN_CODE.name
        self.column_name_level = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        self.column_name_parent = SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name
        self.column_name_child = SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name

        # Define required columns
        self.global_required_columns = {
            self.sp_name_composition: [
                SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name,
                SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name,
            ],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_LEVEL.name,
                SpDescription.OptionalColumn.COLUMN_RELATION.name,
            ],
        }

        # Set dataframes
        self.model_dataframes = {
            self.sp_name_composition: self.model_sp_composition.data_loader_model.raw_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.raw_data,
        }

    def validate_hierarchy_with_tree(self) -> Tuple[List[str], List[str]]:
        """
        Validate tree composition structure and detect cycles.

        Performs comprehensive tree validation including:
        - Required column presence checks
        - Data cleaning and integer conversion
        - Root node insertion if missing
        - Cycle detection in parent-child relationships
        - Level hierarchy validation

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for structure violations and cycles
                - List[str]: Warning messages (currently empty)
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

        # Clean integer columns: df_description
        df_description, _ = DataCleaningProcessing.clean_dataframe_integers(
            df=df_description,
            file_name=self.sp_name_description,
            columns_to_clean=[self.column_name_code, self.column_name_level],
            min_value=1,
        )

        # Add root node if not present
        if not (df_description[self.column_name_code] == 0).any():
            root_row = pd.DataFrame(
                [len(self.model_sp_description.EXPECTED_COLUMNS) * [0]],
                columns=self.model_sp_description.EXPECTED_COLUMNS,
            )
            df_description = pd.concat([df_description, root_row], ignore_index=True)

        # Build tree and check for cycles
        tree = TreeProcessing.create_tree_structure(df_composition, self.column_name_parent, self.column_name_child)

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)
        if cycle_found:
            errors.append(f"{self.sp_name_composition}: Ciclo encontrado: [{' -> '.join(cycle)}].")

        # Validate level composition
        level_errors = TreeProcessing.validate_level_hierarchy(
            df_composition,
            df_description,
            self.column_name_code,
            self.column_name_level,
            self.column_name_parent,
            self.column_name_child,
        )

        errors.extend(self._format_level_errors(level_errors, df_composition, df_description))

        return errors, warnings

    def validate_tree_levels_children(self) -> Tuple[List[str], List[str]]:
        """
        Validate that all children of the same parent have the same level.

        Ensures consistency in the tree structure by checking that all indicators
        sharing the same parent are at the same hierarchical level. This prevents
        inconsistent tree structures where siblings have different levels.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: Error messages for level inconsistencies and missing codes
                - List[str]: Warning messages (currently empty)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check required columns exist
        column_errors = self.check_columns_in_models_dataframes(self.global_required_columns, self.model_dataframes)
        if column_errors:
            return column_errors, warnings

        df_composition = self.model_dataframes[self.sp_name_composition].copy()
        df_description = self.model_dataframes[self.sp_name_description].copy()

        # Create level mapping
        levels = {row[self.column_name_code]: row[self.column_name_level] for _, row in df_description.iterrows()}

        # Group by parent and validate children levels
        parent_groups = df_composition.groupby(self.column_name_parent)
        for parent, group in parent_groups:
            if parent not in levels:
                errors.append(f"{self.sp_name_composition}: Código pai {parent} não encontrado na descrição.")
                continue

            children_info: List[Tuple[Any, Any]] = []

            for _, row in group.iterrows():
                child = row[self.column_name_child]
                if child not in levels:
                    errors.append(f"{self.sp_name_composition}: Código filho {child} não encontrado na descrição.")
                    continue
                child_level = levels[child]
                children_info.append((child, child_level))

            if children_info and len({level for _, level in children_info}) > 1:
                error_children = ", ".join([f"indicador {child} possui nível '{level}'" for child, level in children_info])
                errors.append(f"{self.sp_name_description}: Indicadores filhos do pai {parent} " f"não estão no mesmo nível: [{error_children}].")

        return errors, warnings

    def _format_level_errors(
        self,
        level_errors: List[Tuple[Any, Any]],
        df_composition: pd.DataFrame,
        df_description: pd.DataFrame,
    ) -> List[str]:
        """
        Format level composition errors with proper line numbers and descriptions.

        Creates detailed error messages for level hierarchy violations by looking up
        the specific row numbers, parent levels, and child levels involved in the error.

        Args
        ----
        level_errors : List[Tuple[Any, Any]]
            List of (parent, child) tuples representing invalid relationships.
        df_composition : pd.DataFrame
            Composition DataFrame for row number lookup.
        df_description : pd.DataFrame
            Description DataFrame for level lookup.

        Returns
        -------
        List[str]
            Formatted error messages with file names, line numbers, and level details.
        """
        formatted_errors: List[str] = []

        for parent, child in level_errors:
            if parent is not None and child is not None:
                # Find the row with this relationship
                matching_rows = df_composition[
                    (df_composition[self.column_name_parent] == int(parent)) & (df_composition[self.column_name_child] == int(child))
                ]

                if not matching_rows.empty:
                    row_index = matching_rows.index[0]
                    line_number = row_index + 2

                    parent_level = df_description[df_description[self.column_name_code] == int(parent)][self.column_name_level].values[0]

                    child_level = df_description[df_description[self.column_name_code] == int(child)][self.column_name_level].values[0]

                    formatted_errors.append(
                        f"{self.sp_name_composition}, linha {line_number}: "
                        f"O indicador {parent} (nível {parent_level}) não pode ser pai "
                        f"do indicador {child} (nível {child_level}). "
                        f"Atualize os níveis no arquivo de descrição."
                    )

        return formatted_errors

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all tree validation checks.

        Orchestrates the execution of tree hierarchy validations and child level
        consistency checks. If either composition or description dataframes are empty,
        all validations are marked as not executed.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List[str]: All validation errors collected during execution
                - List[str]: All validation warnings collected during execution

        Notes
        -----
        Validations are skipped if composition or description data is unavailable.
        """
        validations = [
            (self.validate_hierarchy_with_tree, NamesEnum.TH.value),
            (self.validate_tree_levels_children, NamesEnum.CHILD_LVL.value),
        ]

        if self.model_sp_composition.data_loader_model.raw_data.empty or self.model_sp_description.data_loader_model.raw_data.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        self.build_reports(validations)

        return self._errors, self._warnings
