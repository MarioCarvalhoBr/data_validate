from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type

from core.report import ReportList
from data_model.sp_model_abc import SpModelABC
from validation.data_context import DataContext


class ValidatorModelABC(ABC):

    def __init__(self, data_context: DataContext, report_list: ReportList, type_class: Type[SpModelABC], **kwargs: Dict[str, Any]):
        # SETUP
        self._data_context = data_context
        self._report_list = report_list
        self._type_class = type_class

        # UNPACK DATA
        self._data_model = self._data_context.get_instance_of(self._type_class)
        self._filename = self._data_model.FILENAME
        self._dataframe = self._data_model.DATA_MODEL_IMPORTER.df_data.copy()
        self.TITLES_INFO = self._data_context.config.get_verify_names()

        # LIST OF ERRORS AND WARNINGS
        self._errors: List[str] = []
        self._warnings: List[str] = []

        self.init()

    def init(self):
        self.run()

    def build_reports(self, validations):
        for func, report_key in validations:
            errors, warnings = func()
            if errors or warnings:
                self._report_list.extend(self.TITLES_INFO[report_key], errors=errors, warnings=warnings)
            self._errors.extend(errors)
            self._warnings.extend(warnings)

    @abstractmethod
    def run(self):
        pass
