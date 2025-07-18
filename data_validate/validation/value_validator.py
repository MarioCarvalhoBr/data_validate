#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDescription, SpTemporalReference, SpScenario, SpValue
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC

class SpValueValidator(ValidatorModelABC):
    """
    Validates the content of the SpScenario spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_context=data_context, report_list=report_list, type_class=SpValue, **kwargs)

        # Configure
        self.model_sp_value = self._data_model
        self.model_sp_description = self._data_context.get_instance_of(SpDescription)
        self.model_sp_temporal_reference = self._data_context.get_instance_of(SpTemporalReference)
        self.model_sp_scenario = self._data_context.get_instance_of(SpScenario)

        # Run pipeline
        self.run()

    def validate_foo(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def validate_bar(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def validate_xyz(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""

        validations = [
            (self.validate_foo, NamesEnum.HTML_DESC.value),
            (self.validate_bar, NamesEnum.HTML_DESC.value),
            (self.validate_xyz, NamesEnum.HTML_DESC.value),
        ]

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings