#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import SpProportionality, SpDescription, SpValue, SpComposition
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


class SpProportionalityValidator(ValidatorModelABC):
    """
    Validates the content of the SpProportionality spreadsheet.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpProportionality,
            **kwargs,
        )

        # Configure
        self.model_sp_proportionality = self._data_model
        self.model_sp_description = self._data_models_context.get_instance_of(SpDescription)
        self.model_sp_value = self._data_models_context.get_instance_of(SpValue)
        self.model_sp_composition = self._data_models_context.get_instance_of(SpComposition)

        # Get model properties once
        self.exists_scenario = self.model_sp_value.scenario_exists_file
        self.list_scenarios = self.model_sp_value.scenarios_list

        self.sp_name_proportionality = ""
        self.sp_name_description = ""
        self.sp_name_value = ""
        self.sp_name_composition = ""

        self.column_name_id: str = ""

        self.column_name_parent: str = ""
        self.column_name_child: str = ""

        self.column_name_code: str = ""
        self.column_name_level: str = ""
        self.column_name_scenario: str = ""

        self.global_required_columns = {}
        self.model_dataframes = {}

        # Prepare statements
        self._prepare_statement()

        # Run pipeline
        self.run()

    def _prepare_statement(self):
        # Get model properties once
        self.sp_name_proportionality = self.model_sp_proportionality.filename
        self.sp_name_description = self.model_sp_description.filename
        self.sp_name_value = self.model_sp_value.filename
        self.sp_name_composition = self.model_sp_composition.filename

        # Set column names
        self.column_name_parent = SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name
        self.column_name_child = SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name

        self.column_name_code = SpDescription.RequiredColumn.COLUMN_CODE.name
        self.column_name_level = SpDescription.RequiredColumn.COLUMN_LEVEL.name
        self.column_name_scenario = SpDescription.DynamicColumn.COLUMN_SCENARIO.name

        self.column_name_id = SpProportionality.RequiredColumn.COLUMN_ID.name

        # Define required columns efficiently
        self.global_required_columns = {
            self.sp_name_proportionality: [SpProportionality.RequiredColumn.COLUMN_ID.name],
            self.sp_name_description: [
                SpDescription.RequiredColumn.COLUMN_CODE.name,
                SpDescription.RequiredColumn.COLUMN_LEVEL.name,
            ],
            self.sp_name_value: [SpValue.RequiredColumn.COLUMN_ID.name],
            self.sp_name_composition: [
                SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name,
                SpComposition.RequiredColumn.COLUMN_CHILD_CODE.name,
            ],
        }

        # Validate all required columns exist
        self.model_dataframes = {
            self.sp_name_proportionality: self.model_sp_proportionality.data_loader_model.df_data,
            self.sp_name_description: self.model_sp_description.data_loader_model.df_data,
            self.sp_name_value: self.model_sp_value.data_loader_model.df_data,
            self.sp_name_composition: self.model_sp_composition.data_loader_model.df_data,
        }

    def validate_aaa(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - AAA")
        return errors, warnings

    def validate_bbb(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - BBB")

        return errors, warnings

    def validate_ccc(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - CCC")

        return errors, warnings

    def validate_xxx(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - XXX")

        return errors, warnings

    def validate_yyy(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        print(f"Validating {self.sp_name_proportionality} - YYY")

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpProportionality."""

        validations = [
            (self.validate_aaa, NamesEnum.IR.value),
            (self.validate_bbb, NamesEnum.IR.value),
            (self.validate_ccc, NamesEnum.IR.value),
            (self.validate_xxx, NamesEnum.IR.value),
            (self.validate_yyy, NamesEnum.IR.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
