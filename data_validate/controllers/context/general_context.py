#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Context module for general application context management.

This module defines the `GeneralContext` class, which serves as the base context
container for the application. It initializes and holds references to the essential
utilities and configurations required throughout the validation pipeline, such as
language management, configuration, file system utilities, and logging.

Components managed by GeneralContext:
    - LanguageManager (i18n)
    - ApplicationConfig (application settings)
    - FileSystemUtils (file operations)
    - LoggerManager (logging)
    - DataArgs (command line arguments)
"""

from typing import Any, Dict

from data_validate.config import ApplicationConfig
from data_validate.helpers.base import DataArgs, FileSystemUtils, LoggerManager
from data_validate.helpers.tools import LanguageManager


class GeneralContext:
    """
    Base context class for the Data Validate application.

    This class serves as a dependency injection container, initializing and holding
    references to core services used across the application. It ensures that components
    like the logger, configuration, and language manager are instantiated once and
    available globally through the context object.

    Attributes:
        data_args (DataArgs): Command-line arguments and runtime data configurations.
        kwargs (Dict[str, Any]): Additional keyword arguments passed during initialization.
        lm (LanguageManager): Manager for handling internationalization and localized strings.
        config (ApplicationConfig): Central configuration object for application settings and constants.
        fs_utils (FileSystemUtils): Utilities for file system operations.
        logger_manager (LoggerManager): Manager responsible for configuring the logging system.
        logger (logging.Logger): The primary logger instance for the application.
        validations_not_run (list): A list to track validations that were skipped or not executed.
    """

    def __init__(
        self,
        data_args: DataArgs = None,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the GeneralContext with a toolkit, configuration, file system utilities, and logger.

        Args:
            data_args (DataArgs): Data arguments containing input and output folder paths and execution flags.
            **kwargs: Additional keyword arguments for extended context configuration.

        The initialization process involves:
        1.  Storing arguments and kwargs.
        2.  Initializing the `LanguageManager` for i18n support.
        3.  Loading the application `ApplicationConfig`.
        4.  Setting up `FileSystemUtils` for file handling.
        5.  Configuring the logging system via `LoggerManager`.
        6.  Disabling the logger if debug mode is not active.
        """
        # Unpack the arguments
        self.data_args = data_args
        self.kwargs = kwargs

        # Configure the Toolkit
        self.lm: LanguageManager = LanguageManager()
        self.config: ApplicationConfig = ApplicationConfig()
        self.fs_utils: FileSystemUtils = FileSystemUtils()
        self.logger_manager = LoggerManager(
            log_folder="data/output/logs",
            console_logger="console_logger",
            prefix="data_validate",
            logger_name="data_validate_file_logger",
        )
        self.logger = self.logger_manager.file_logger

        # Configure the file logger
        if not self.data_args.data_action.debug:
            self.logger.disabled = True

        self.validations_not_run = []

    def finalize(self):
        """
        Finalize the application context and cleanup resources.

        This method handles post-execution tasks such as removing temporary log files
        if the application is not running in debug mode.

        Logic:
            - If debug mode is OFF: Removes the session log file.
            - If debug mode is ON: Prints the location of the log file to stdout.
        """
        # Remove log file if not in debug mode
        if not self.data_args.data_action.debug:
            self.fs_utils.remove_file(self.logger_manager.log_file)
        else:
            print("\nLog file created at:", self.logger_manager.log_file)
