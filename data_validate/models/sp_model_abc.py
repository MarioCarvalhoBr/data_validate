#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module defining the abstract base class for spreadsheet models.

This module provides `SpModelABC`, the foundational template for all spreadsheet
models in the application. It establishes the interface for validation, data loading,
and processing required by all specific spreadsheet implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel


class SpModelABC(ABC):
    """
    Abstract base class for all spreadsheet models.

    Defines the contract and shared functionality for spreadsheet data models,
    including initialization, data loading, validation pipelines (pre-processing,
    structure checking, data cleaning), and error reporting.

    Attributes:
        structural_errors (List[str]): List of structural validation errors.
        structural_warnings (List[str]): List of structural validation warnings.
        data_cleaning_errors (List[str]): List of data cleaning/integrity errors.
        data_cleaning_warnings (List[str]): List of data cleaning/integrity warnings.
        filename (str): Name of the file associated with this model.
        data_loader_model (DataLoaderModel): Facade for data loading operations.
        context (GeneralContext): Application context.
    """

    class DEFINITIONS(ConstantBase):
        """
        Global definitions for spreadsheet models.

        Attributes:
            LEGEND_EXISTS_FILE (str): Key for legend file existence in kwargs.
            LEGEND_READ_SUCCESS (str): Key for legend file read success in kwargs.
            SCENARIO_EXISTS_FILE (str): Key for scenario file existence in kwargs.
            SCENARIO_READ_SUCCESS (str): Key for scenario file read success in kwargs.
            SCENARIOS_LIST (str): Key for scenarios list in kwargs.

        """

        def __init__(self):
            """Initialize the DEFINITIONS constants."""
            super().__init__()

            self.LEGEND_EXISTS_FILE = "legend_exists_file"
            self.LEGEND_READ_SUCCESS = "legend_read_success"

            self.SCENARIO_EXISTS_FILE = "scenario_exists_file"
            self.SCENARIO_READ_SUCCESS = "scenario_read_success"
            self.SCENARIOS_LIST = "scenarios_list"

            self._finalize_initialization()

    VAR_CONSTS = DEFINITIONS()

    CONSTANTS = None

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the Abstract Spreadsheet Model.

        Sets up error tracking lists, loads context and data model, and extracts
        optional configuration from kwargs (e.g. scenario availability).

        Args:
            context (GeneralContext): Application context.
            data_model (DataLoaderModel): Data loading facade.
            **kwargs: Additional configuration parameters.
        """
        # SETUP
        self.context: GeneralContext = context
        self.data_loader_model: DataLoaderModel = data_model
        self._kwargs: Dict[str, Any] = kwargs

        # UNPACKING DATA ARGS
        self.filename: str = self.data_loader_model.filename

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
        """
        Initialize the verification process by performing basic sanity checks.

        This method removes duplicates from the scenario list, checks if the data frame is empty,
        and performs initial validations like vertical bar checks and unnamed column checks.
        """
        self.scenarios_list = list(set(self.scenarios_list))

        # CHECK 0: Add COLUMNS
        if not self.data_loader_model.df_data.empty:
            self.DF_COLUMNS = list(self.data_loader_model.df_data.columns)

        if self.data_loader_model.df_data.empty and self.data_loader_model.read_success:
            self.structural_errors.append(f"{self.filename}: O arquivo enviado está vazio.")

        # CHECK 1: Vertical Bar Check
        _, errors_vertical_bar = DataFrameProcessing.check_dataframe_vertical_bar(self.data_loader_model.df_data, self.filename)
        self.structural_errors.extend(errors_vertical_bar)

        # CHECK 2: Expected Structure Columns Check: check_unnamed_columns
        _, errors_unnamed_columns = DataFrameProcessing.check_dataframe_unnamed_columns(self.data_loader_model.df_data, self.filename)
        self.structural_errors.extend(errors_unnamed_columns)

    @abstractmethod
    def pre_processing(self):
        """
        Abstract method for pre-processing logic.

        Should implement initial checks, column adjustments, or dependency verification
        before main validation starts.
        """
        pass

    @property
    def is_sanity_check_passed(self) -> bool:
        """
        Check if the basic sanity checks passed.

        Returns:
            bool: True if there are no structural or data cleaning errors and the file is valid, False otherwise.
        """
        exists_errors_legend = self.structural_errors or self.data_cleaning_errors
        exists_file_errors_legend = (
            not self.data_loader_model.exists_file or self.data_loader_model.df_data.empty or not self.data_loader_model.read_success
        )
        value = True
        if exists_errors_legend or exists_file_errors_legend:
            value = False
        return value

    @abstractmethod
    def post_processing(self):
        """
        Abstract method for post-processing logic.

        Should implement final adjustments or derived calculations after cleaning.
        """
        pass

    @abstractmethod
    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        """
        Abstract method for validating column structure.

        Should check if the DataFrame contains all required columns and verify column naming conventions.
        """
        pass

    @abstractmethod
    def data_cleaning(self, *args, **kwargs):
        """
        Abstract method for data cleaning.

        Should implement type conversion, valid value checks (e.g., positive integers),
        and cleaning of raw data.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Abstract method to execute the validation pipeline.

        Should orchestrate the calling of `pre_processing`, `expected_structure_columns`,
        `data_cleaning`, and `post_processing`.
        """
        pass

    def __str__(self):
        """
        Return a string representation of the model.

        Returns:
            str: String containing information about the file and data model.
        """
        return f"SpModelABC(FILENAME: {self.filename}):\n" + f"  DATA_MODEL: {self.data_loader_model}\n"
