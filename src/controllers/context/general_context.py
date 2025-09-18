#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import Any, Dict

from src.helpers.tools import LanguageManager
from src.config import Config
from src.helpers.base import DataArgs, FileSystemUtils, LoggerManager


class GeneralContext:
    def __init__(
        self,
        data_args: DataArgs = None,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the GeneralContext with a toolkit, configuration, file system utilities, and logger.

        Args:
            data_args (DataArgs): Data arguments containing input and output folder paths.

        Atributes:
            lm (LanguageManager): Language manager for handling multilingual support.
            config (Config): Configuration manager for application settings.
            fs_utils (FileSystemUtils): File system utilities for file operations.
            logger (Logger): Logger for logging messages and errors.
            validations_not_run (list): List to track validations that were not executed.
        """
        # Unpack the arguments
        self.data_args = data_args
        self.kwargs = kwargs

        # Configure the Toolkit
        self.lm: LanguageManager = LanguageManager()
        self.config: Config = Config()
        self.fs_utils: FileSystemUtils = FileSystemUtils()
        self.logger_manager = LoggerManager(
            log_folder="data/output/logs",
            console_logger="console_logger",
            prefix="src",
            logger_name="data_validate_file_logger",
        )
        self.logger = self.logger_manager.file_logger

        # Configure the file logger
        if not self.data_args.data_action.debug:
            self.logger.disabled = True

        self.validations_not_run = []

    def finalize(self):
        # Remove log file if not in debug mode
        if not self.data_args.data_action.debug:
            self.fs_utils.remove_file(self.logger_manager.log_file)
        else:
            print("\nLog file created at:", self.logger_manager.log_file)
