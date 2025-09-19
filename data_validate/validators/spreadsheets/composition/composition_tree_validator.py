#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Tree composition validation for spreadsheet composition structures."""

from typing import List, Tuple, Dict, Any

import pandas as pd

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.processing.data_cleaning import (
    clean_dataframe_integers,
)
from data_validate.helpers.common.validation.tree_data_validation import (
    create_tree_structure,
    validate_level_hierarchy,
    detect_tree_cycles,
)
from data_validate.models import SpComposition, SpDescription
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


class SpCompositionTreeValidator(ValidatorModelABC):
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
        """Prepare validation context and column mappings."""
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
            self.sp_name_composition: self.model_sp_composition.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
        }

    def validate_hierarchy_with_tree(self) -> Tuple[List[str], List[str]]:
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

        # Add root node if not present
        if not (df_description[self.column_name_code] == 0).any():
            root_row = pd.DataFrame(
                [len(self.model_sp_description.EXPECTED_COLUMNS) * [0]],
                columns=self.model_sp_description.EXPECTED_COLUMNS,
            )
            df_description = pd.concat([df_description, root_row], ignore_index=True)

        # Build tree and check for cycles
        tree = create_tree_structure(df_composition, self.column_name_parent, self.column_name_child)

        cycle_found, cycle = detect_tree_cycles(tree)
        if cycle_found:
            errors.append(f"{self.sp_name_composition}: Ciclo encontrado: [{' -> '.join(cycle)}].")

        # Validate level composition
        level_errors = validate_level_hierarchy(
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

        Returns:
            Tuple containing (errors, warnings) lists
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

        Args:
            level_errors: List of (parent, child) error tuples
            df_composition: Composition dataframe
            df_description: Description dataframe

        Returns:
            List of formatted error messages
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

        Returns:
            Tuple containing (errors, warnings) lists
        """
        validations = [
            (self.validate_hierarchy_with_tree, NamesEnum.TH.value),
            (self.validate_tree_levels_children, NamesEnum.CHILD_LVL.value),
        ]

        if self.model_sp_composition.data_loader_model.df_data.empty or self.model_sp_description.data_loader_model.df_data.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        self.build_reports(validations)

        return self._errors, self._warnings
