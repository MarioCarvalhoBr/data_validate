#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from logging import Logger
from typing import List, Any, Dict

from data_validate.common.utils.data_args import DataArgs
from data_validate.common.utils.file_system_utils import FileSystemUtils
from data_validate.config.config import Config


class GeneralContext:
    def __init__(self, config: Config=None, fs_utils: FileSystemUtils=None, data_args: DataArgs=None, logger: Logger=None, **kwargs: Dict[str, Any]):
        """
        Initialize the DataContext with a list of models to initialize.

        Args:
            models_to_use (List[Any]): List of models to initialize.
            config (Config): Configuration object containing settings.
            fs_utils (FileSystemUtils): File system utilities for file operations.
            data_args (DataArgs): Data arguments containing input and output folder paths.
        """
        self.config = config
        self.fs_utils = fs_utils
        self.data_args = data_args
        self.logger = logger
        self.locale_manager = fs_utils.locale_manager if fs_utils else None
        self.kwargs = kwargs