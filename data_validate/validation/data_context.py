#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Any
from typing import Type, Optional

from common.utils.data_args import DataArgs
from common.utils.file_system_utils import FileSystemUtils
from config.config import Config
from data_model.sp_model_abc import SpModelABC


class DataContext:
    def __init__(self, models_to_use: List[Any]=None, config: Config=None, fs_utils: FileSystemUtils=None, data_args: DataArgs=None):
        """
        Initialize the DataContext with a list of models to initialize.

        Args:
            models_to_use (List[Any]): List of models to initialize.
            config (Config): Configuration object containing settings.
            fs_utils (FileSystemUtils): File system utilities for file operations.
            data_args (DataArgs): Data arguments containing input and output folder paths.
        """
        self.models_to_use = models_to_use or []
        self.config = config
        self.fs_utils = fs_utils
        self.data_args = data_args

        self.data = {}
        self.errors = []
        self.warnings = []
        self.report_list = []


    def _load_data(self):
        pass

    # file: data_validate/validation/data_context.py

    # file: data_validate/validation/data_context.py

    def get_instance_of(self, model_class: Type[SpModelABC]) -> Optional[SpModelABC]:
        """
        Return an existing instance of `model_class` or, if you only stored
        the class, instantiate and return it.
        """
        for model in self.models_to_use:
            # case A: model is already an instance
            if isinstance(model, model_class):
                # print(f"Model instance found: {model.__class__.__name__}")
                return model

        return None


    def run(self):
        pass