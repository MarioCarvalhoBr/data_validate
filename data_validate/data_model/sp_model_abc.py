from abc import ABC, abstractmethod
from typing import List, Dict, Any

from data_validate.common.base.constant_base import ConstantBase
from data_validate.controller.context.general_context import GeneralContext
from data_validate.tools.data_loader.api.facade import DataLoaderModel
from data_validate.common.utils.validation.data_validation import check_vertical_bar, check_unnamed_columns

class SpModelABC(ABC):
    class DEFINITIONS(ConstantBase):
        def __init__(self):
            super().__init__()
            self.CSV = ".csv"
            self.XLSX = ".xlsx"
            self.EXTENSIONS = [self.CSV, self.XLSX]

            self.LEGEND_EXISTS_FILE = "legend_exists_file"
            self.LEGEND_READ_SUCCESS = "legend_read_success"

            self.SCENARIO_EXISTS_FILE = "scenario_exists_file"
            self.SCENARIO_READ_SUCCESS = "scenario_read_success"
            self.SCENARIOS_LIST = "scenarios_list"

            self.SP_NAMAE_SCENARIO = "cenarios"

            self._finalize_initialization()
    VAR_CONSTS = DEFINITIONS()

    CONSTANTS = None

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):

        # SETUP
        self.context: GeneralContext = context
        self.data_loader_model: DataLoaderModel = data_model
        self._kwargs: Dict[str, Any] = kwargs

        # UNPACKING DATA ARGS
        self.filename: str =  self.data_loader_model.filename

        self.legend_exists_file: bool = self._kwargs.get(self.VAR_CONSTS.LEGEND_EXISTS_FILE, False)
        self.legend_read_success: bool = self._kwargs.get(self.VAR_CONSTS.LEGEND_READ_SUCCESS, False)

        self.scenario_exists_file: bool = self._kwargs.get(self.VAR_CONSTS.SCENARIO_EXISTS_FILE, False)
        self.scenario_read_success: bool = self._kwargs.get(self.VAR_CONSTS.SCENARIO_READ_SUCCESS, False)
        self.scenarios_list: List[str] = self._kwargs.get(self.VAR_CONSTS.SCENARIOS_LIST, [])

        # CONFIGURE VARIABLES AND LISTS
        self.structural_errors: List[str] = []
        self.structural_warnings: List[str] = []

        self.data_cleaning_errors: List[str] = []
        self.data_cleaning_warnings: List[str] = []

        # DataFrame setup
        self.EXPECTED_COLUMNS: List[str] = []
        self.DF_COLUMNS: List[str] = []

        # Additional variables
        self.all_ok: bool = True

        self.init()


    def init(self):
        self.scenarios_list = list(set(self.scenarios_list))

        # CHECK 0: Add COLUMNS
        if not self.data_loader_model.df_data.empty:
            self.DF_COLUMNS = list(self.data_loader_model.df_data.columns)

        if self.data_loader_model.df_data.empty and self.data_loader_model.read_success:
            self.structural_errors.append(f"{self.filename}: O arquivo enviado está vazio.")

        # CHECK 1: Vertical Bar Check
        _, errors_vertical_bar = check_vertical_bar(self.data_loader_model.df_data, self.filename)
        self.structural_errors.extend(errors_vertical_bar)

        # CHECK 2: Expected Structure Columns Check: check_unnamed_columns
        _, errors_unnamed_columns = check_unnamed_columns(self.data_loader_model.df_data, self.filename)
        self.structural_errors.extend(errors_unnamed_columns)

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

    """@property
    def is_sanity_check_passed(self) ->
        exists_errors_legend = self.structural_errors or self.data_cleaning_errors
        exists_file_errors_legend = not self.data_loader_model.exists_file or self.data_loader_model.df_data.empty or not self.data_loader_model.read_success
        if exists_errors_legend or exists_file_errors_legend:
            return False
        return True"""

    @abstractmethod
    def post_processing(self):
        """
        Defines an abstract method for post-processing. This method is intended to be implemented
        by subclasses to perform necessary operations after executing the primary logic or task.

        This serves as a placeholder for subclass-specific postprocessing logic, and forces derived
        classes to provide their own implementation.

        :raises NotImplementedError: If the method is not overridden in a subclass.
        """
        pass

    @abstractmethod
    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check if there is a vertical bar in the column name
        pass


    @abstractmethod
    def data_cleaning(self, *args, **kwargs):
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