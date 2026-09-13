#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Proportionality spreadsheet model.

This module defines the `SpProportionality` class, which handles the loading,
validation, and processing of proportionality data (influence weights between indicators).
"""

from typing import Any, List

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase

from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.models.sp_model_abc import SpModelABC


class SpProportionality(SpModelABC):
    """
    Model for the Proportionality spreadsheet.

    Manages specific validations for proportionality data, handling multi-level
    column structures (ID/Indicator) and verifying calculation integrity.

    Attributes:
        CONSTANTS (Constants): Immutable constants specific to this model.
    """

    # CONSTANTS
    class Constants(ConstantBase):
        """
        Immutable constants for the Proportionality model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('proporcionalidade').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self) -> None:
            """Initialize the model constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_PROPORTIONALITIES
            self.SP_DESCRIPTION = "Proportionality sheet with influence weights between indicators."
            self._finalize_initialization()

    CONSTANTS = Constants()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Proportionality spreadsheet.

        Attributes:
            COLUMN_ID (Series): Column definition for the ID (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_ID = pd.Series(dtype="int64", name="id")

        ALL: List[str] = [
            str(COLUMN_ID.name),
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: LoadedSheet,
        **kwargs: object,
    ) -> None:
        """
        Initialize the SpProportionality model.

        Args:
            context (GeneralContext): The application general context.
            data_model (LoadedSheet): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        # BUG-003: set once a structural error invalidates the sheet's header layout
        # (`post_processing`); replaces mutating `data_loader_model.header_type` to
        # `"invalid"`, which every other model/validator sharing that same
        # `LoadedSheet` instance would also observe.
        self.header_layout_invalid: bool = False

    def pre_processing(self) -> None:
        """
        Run pre-processing steps.

        Performs checks on level 1 and level 2 column names to ensure they follow the expected pattern.
        """
        translate = self.context.language_manager.text
        self.EXPECTED_COLUMNS = list(self.RequiredColumn.ALL)

        unique_columns_level_1 = self.frame.columns.get_level_values(0).unique().tolist()
        unique_columns_level_1 = [
            col for col in unique_columns_level_1 if not col.lower().startswith("unnamed: 0_level_0")
        ]

        __, level_1_codes_not_matched_by_pattern = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            unique_columns_level_1, self.scenarios
        )

        if level_1_codes_not_matched_by_pattern:
            self.structural_errors.append(
                translate("rule.PROP-001.level1", filename=self.filename, columns=level_1_codes_not_matched_by_pattern)
            )

        unique_columns_level_2 = self.frame.columns.get_level_values(1).unique().tolist()
        unique_columns_level_2 = [col for col in unique_columns_level_2 if col != self.RequiredColumn.COLUMN_ID.name]

        __, level_2_codes_not_matched_by_pattern = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            unique_columns_level_2, self.scenarios
        )

        if level_2_codes_not_matched_by_pattern:
            self.structural_errors.append(
                translate("rule.PROP-001.level2", filename=self.filename, columns=level_2_codes_not_matched_by_pattern)
            )

    def expected_structure_columns(self, *args: Any, **kwargs: Any) -> None:
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors list.
        """
        translate = self.context.language_manager.text
        if self.data_loader_model.header_type == "double":
            unique_columns_level_1 = self.frame.columns.get_level_values(0).unique().tolist()
            unique_columns_level_2 = self.frame.columns.get_level_values(1).unique().tolist()

            # Check extra columns in level 1 (do not ignore 'id')
            _, extras_level_1 = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=unique_columns_level_1,
                strings_to_ignore=[],  # Do not ignore 'id' here
                suffixes_for_matching=self.scenarios,
            )
            for extra_column in extras_level_1:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(
                        translate("rule.PROP-002.level1_unexpected", filename=self.filename, column=extra_column)
                    )

            # Check extra columns in level 2 (ignore 'id')
            _, extras_level_2 = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=unique_columns_level_2,
                strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
                suffixes_for_matching=self.scenarios,
            )
            for extra_column in extras_level_2:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(
                        translate("rule.PROP-002.level2_unexpected", filename=self.filename, column=extra_column)
                    )

            # Check for missing expected columns in level 2
            for col in self.EXPECTED_COLUMNS:
                if col not in unique_columns_level_2:
                    self.structural_errors.append(
                        translate("rule.PROP-002.level2_missing", filename=self.filename, column=col)
                    )

    def data_cleaning(self, *args: Any, **kwargs: Any) -> None:
        """Run data cleaning steps (currently empty)."""

    def post_processing(self) -> None:
        """
        Invalidate this instance's working frame when the header layout is structurally broken.

        BUG-003: reassigns `self.frame` to a fresh empty `DataFrame` and sets
        `self.header_layout_invalid` instead of writing `pd.DataFrame()` into
        `data_loader_model.raw_data` and `"invalid"` into `data_loader_model.header_type` —
        both shared with every other model/validator that reads the same `LoadedSheet`.
        Consumers that used to check `data_loader_model.raw_data.empty` /
        `header_type == "invalid"` for this sheet must check `model.frame.empty` /
        `model.header_layout_invalid` instead.
        """
        if self.structural_errors:
            self.frame = pd.DataFrame()
            self.header_layout_invalid = True

    def run(self) -> None:
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        self.initialize()

        if (
            self.data_loader_model.does_file_exist
            and not self.data_loader_model.raw_data.empty
            and self.data_loader_model.header_type == "double"
        ):
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
            self.post_processing()
