#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

import pandas as pd

from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDescription, SpScenario, SpLegend, SpValue
from controller.context.data_context import DataModelsContext
from services.spreadsheets.validator_model_abc import ValidatorModelABC


class SpLegendValidator(ValidatorModelABC):
    """
    Validates the content of the SpLegend spreadsheet.
    """

    def __init__(self, data_models_context: DataModelsContext, report_list: ReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_models_context=data_models_context, report_list=report_list, type_class=SpLegend, **kwargs)

        # Configure
        self.model_sp_legend = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)
        self.model_sp_scenario = self._data_models_context.get_instance_of(SpScenario)

        # Get model properties once
        self.exists_scenario = self.model_sp_value.exists_scenario
        self.list_scenarios = self.model_sp_value.list_scenarios

        self.sp_name_legend = ""
        self.sp_name_description = ""
        self.sp_name_value = ""
        self.sp_name_scenario = ""

        self.global_required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_legend = self.model_sp_legend.CONSTANTS.SP_NAME
        self.sp_name_description = self.model_sp_description.CONSTANTS.SP_NAME
        self.sp_name_value = self.model_sp_value.CONSTANTS.SP_NAME
        self.sp_name_scenario = self.model_sp_scenario.CONSTANTS.SP_NAME

        # Define required columns efficiently
        self.global_required_columns = {
            self.sp_name_legend: [SpLegend.RequiredColumn.COLUMN_CODE.name, SpLegend.RequiredColumn.COLUMN_LABEL.name,
                                  SpLegend.RequiredColumn.COLUMN_COLOR.name, SpLegend.RequiredColumn.COLUMN_MINIMUM.name,
                                  SpLegend.RequiredColumn.COLUMN_MAXIMUM.name, SpLegend.RequiredColumn.COLUMN_ORDER.name],
            self.sp_name_description: [SpDescription.RequiredColumn.COLUMN_CODE.name, SpDescription.DynamicColumn.COLUMN_LEGEND.name],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_scenario: [SpScenario.RequiredColumn.COLUMN_SYMBOL.name] if self.exists_scenario else []
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_legend: self.model_sp_legend.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_scenario: self.model_sp_scenario.data_loader_model.df_data if self.exists_scenario else pd.DataFrame()
        }

    def validate_overlapping_multiple_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def validate_range_multiple_legend(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpLegend."""
        validations = []
        validations.append((self.validate_overlapping_multiple_legend, NamesEnum.LEG_OVER.value))
        validations.append((self.validate_range_multiple_legend, NamesEnum.LEG_RANGE.value))

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
