from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Tuple

from data_validate.common.utils.validation.data_validation import check_text_length, column_exists
from data_validate.controller.report.model_report import ModelListReport
from data_validate.data_model.sp_model_abc import SpModelABC
from data_validate.controller.context.data_context import DataModelsContext


class ValidatorModelABC(ABC):

    def __init__(self, data_models_context: DataModelsContext, report_list: ModelListReport, type_class: Type[SpModelABC], **kwargs: Dict[str, Any]):
        # SETUP
        self._data_models_context = data_models_context
        self._report_list = report_list
        self._type_class = type_class

        # UNPACK DATA
        self._data_model = self._data_models_context.get_instance_of(self._type_class)
        self._filename = self._data_model.filename
        self._dataframe = self._data_model.data_loader_model.df_data.copy()
        self.TITLES_INFO = self._data_models_context.config.get_verify_names()

        # LIST OF ERRORS AND WARNINGS
        self._errors: List[str] = []
        self._warnings: List[str] = []

        self.init()

    def init(self):
        pass

    # Create static method to check if column exists
    def column_exists(self, dataframe, filename, column) -> Tuple[bool, str]:

        # How use: To use this method, you can call it directly with the dataframe and column name.
        # For example:
        # exists, msg_error_column = ValidatorModelABC.column_exists(dataframe, filename, column
        exists, msg_error_column = column_exists(dataframe, filename, column)
        return exists, msg_error_column


    def _column_exists(self, column: str) -> Tuple[bool, str]:
        exists, msg_error_column = column_exists(self._dataframe, self._filename, column)
        return exists, msg_error_column

    def _column_exists_dataframe(self, dataframe, column: str) -> Tuple[bool, str]:
        exists, msg_error_column = column_exists(dataframe, self._filename, column)
        return exists, msg_error_column

    def _check_text_length(self, column: str, max_len: int) -> Tuple[List[str], List[str]]:
        """Helper function to validate text length in a column."""
        warnings = []
        __, warnings_text_length = check_text_length(dataframe=self._dataframe, file_name=self._filename, column=column, max_len=max_len)
        warnings.extend(warnings_text_length)
        return [], warnings

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

    @abstractmethod
    def _prepare_statement(self):
        pass
