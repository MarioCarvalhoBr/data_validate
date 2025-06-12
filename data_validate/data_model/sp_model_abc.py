from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import List, Dict, Any
import pandas as pd


from data_validate.controller.data_importer.api.facade import DataModelImporter
from data_validate.common.utils.validation.data_validation import check_vertical_bar, check_unnamed_columns

class SpModelABC(ABC):
    INFO = MappingProxyType({
        "EXTENSIONS": [".csv", ".xlsx"],
        "CSV": ".csv",
        "XLSX": ".xlsx",
    })
    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        # Config vars
        self.FILENAME = data_model.filename
        self.DATA_MODEL = data_model

        self.ERROR_STRUCTURE_LIST: List[str] = []

        self.LIST_SCENARIOS: List[str] = kwargs.get("list_scenarios", [])
        self.EXPECTED_COLUMNS: List[str] = []

        self.init()


    def init(self):
        # CHECK 1: Vertical Bar Check
        is_error_vertical_bar, errors_vertical_bar = check_vertical_bar(self.DATA_MODEL.df_data, self.FILENAME)
        self.ERROR_STRUCTURE_LIST.extend(errors_vertical_bar)

        # CHECK 2: Expected Structure Columns Check: check_unnamed_columns
        is_error_unnamed_columns, errors_unnamed_columns = check_unnamed_columns(self.DATA_MODEL.df_data, self.FILENAME)
        self.ERROR_STRUCTURE_LIST.extend(errors_unnamed_columns)

    @abstractmethod
    def pre_processing(self):
        """
        Defines an abstract method for pre-processing. This method is intended to be implemented
        by subclasses to perform necessary operations prior to executing the primary logic or task.

        This serves as a placeholder for subclass-specific preprocessing logic, and forces derived
        classes to provide their own implementation.

        :raises NotImplementedError: If the method is not overridden in a subclass.
        """
        pass

    @abstractmethod
    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check if there is a vertical bar in the column name
        pass



    @abstractmethod
    def run(self):
        """
        Executa o processamento do arquivo.
        """
        pass

    def __str__(self):
        """
        Retorna uma representação em string do objeto.

        Returns:
            str: Representação em string do objeto.
        """
        return f"SpModelABC(FILENAME: {self.FILENAME}):\n" + \
               f"  DATA_MODEL: {self.DATA_MODEL}\n"