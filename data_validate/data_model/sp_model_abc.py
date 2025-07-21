from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import List, Dict, Any

from data_validate.tools.data_loader.api.facade import DataLoaderModel
from data_validate.common.utils.validation.data_validation import check_vertical_bar, check_unnamed_columns

class SpModelABC(ABC):
    INFO = MappingProxyType({
        "EXTENSIONS": [".csv", ".xlsx"],
        "CSV": ".csv",
        "XLSX": ".xlsx",
    })
    CONSTANTS = None
    def __init__(self, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):

        # SETUP
        self.data_loader_model: DataLoaderModel = data_model
        self._kwargs: Dict[str, Any] = kwargs

        # UNPACKING DATA ARGS
        self.filename: str =  self.data_loader_model.filename
        self.exists_scenario: bool = kwargs.get("exists_scenario", False)
        self.list_scenarios: List[str] = kwargs.get("list_scenarios", [])

        # CONFIGURE VARIABLES AND LISTS
        self.STRUCTURE_LIST_ERRORS: List[str] = []
        self.STRUCTURE_LIST_WARNINGS: List[str] = []

        self.DATA_CLEAN_ERRORS: List[str] = []
        self.DATA_CLEAN_WARNINGS: List[str] = []

        # DataFrame setup
        self.EXPECTED_COLUMNS: List[str] = []
        self.DF_COLUMNS: List[str] = []

        self.init()


    def init(self):
        self.list_scenarios = list(set(self.list_scenarios))

        # CHECK 0: Add COLUMNS
        if not self.data_loader_model.df_data.empty:
            self.DF_COLUMNS = list(self.data_loader_model.df_data.columns)

        if self.data_loader_model.df_data.empty and self.data_loader_model.read_success:
            self.STRUCTURE_LIST_ERRORS.append(f"{self.filename}: O arquivo enviado está vazio.")

        # CHECK 1: Vertical Bar Check
        _, errors_vertical_bar = check_vertical_bar(self.data_loader_model.df_data, self.filename)
        self.STRUCTURE_LIST_ERRORS.extend(errors_vertical_bar)

        # CHECK 2: Expected Structure Columns Check: check_unnamed_columns
        _, errors_unnamed_columns = check_unnamed_columns(self.data_loader_model.df_data, self.filename)
        self.STRUCTURE_LIST_ERRORS.extend(errors_unnamed_columns)

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
    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """
        Defines an abstract method for data cleaning. This method is intended to be implemented
        by subclasses to perform necessary operations for cleaning the data.

        This serves as a placeholder for subclass-specific data cleaning logic, and forces derived
        classes to provide their own implementation.

        :raises NotImplementedError: If the method is not overridden in a subclass.
        """
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
        return f"SpModelABC(FILENAME: {self.filename}):\n" + \
               f"  DATA_MODEL: {self.data_loader_model}\n"