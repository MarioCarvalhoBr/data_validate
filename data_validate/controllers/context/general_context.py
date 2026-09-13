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

import os
import sys
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
        extra_config (Dict[str, Any]): Additional keyword arguments passed during initialization.
        language_manager (LanguageManager): Manager for handling internationalization and localized strings.
        config (ApplicationConfig): Central configuration object for application settings and constants.
        file_system_utils (FileSystemUtils): Utilities for file system operations.
        logger_manager (LoggerManager): Manager responsible for configuring the logging system.
        logger (logging.Logger): The primary logger instance for the application.
        skipped_validations (list): A list to track validations that were skipped or not executed.
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
        1.  Storing arguments and model_configurations.
        2.  Initializing a single `LanguageManager` from `data_args.data_file.locale`
            (BUG-004/BUG-023: one locale source of truth, threaded into every
            component that needs localized text).
        3.  Loading the application `ApplicationConfig`, injected with the same
            `LanguageManager` instance.
        4.  Setting up `FileSystemUtils`, injected with the same `LanguageManager` instance.
        5.  Configuring the logging system via `LoggerManager`: a file handler is only
            created in debug mode, under `<output_folder>/logs` (BUG-021) — never a
            `logs/` directory relative to the current working directory.
        6.  Disabling the logger if debug mode is not active.
        """
        # Unpack the arguments
        self.data_args = data_args
        self.extra_config = kwargs

        # Configure the Toolkit: one shared LanguageManager built from the parsed locale.
        self.language_manager: LanguageManager = LanguageManager(locale=self.data_args.data_file.locale)
        self.config: ApplicationConfig = ApplicationConfig(language_manager=self.language_manager)
        self.file_system_utils: FileSystemUtils = FileSystemUtils(language_manager=self.language_manager)

        is_debug = bool(self.data_args.data_action.debug)
        log_folder = os.path.join(self.data_args.data_file.output_folder, "logs") if is_debug else None
        self.logger_manager = LoggerManager(
            log_folder=log_folder,
            console_logger="console_logger",
            prefix="data_validate",
            logger_name="data_validate_file_logger",
        )
        self.logger = self.logger_manager.file_logger

        # Configure the file logger
        if not is_debug:
            self.logger.disabled = True

        self.skipped_validations = []

    def finalize(self):
        """
        Finalize the application context and cleanup resources.

        This method handles post-execution tasks: closing and detaching every handler
        from the file logger (BUG-021 — handlers were previously never closed, which
        left file descriptors open and made deleting the log file fail on Windows),
        and printing the log file location when running in debug mode.

        Logic:
            - If debug mode is ON: prints the location of the log file to stdout.
            - Always: closes and removes every handler attached to the file logger.
              When not in debug mode there is no log file to begin with (BUG-021), so
              there is nothing to delete.
        """
        if self.data_args.data_action.debug:
            # ARC-012: machine stdout carries only the `<{json}>` summary fragment; every
            # other progress/debug line goes to stderr.
            print("\nLog file created at:", self.logger_manager.log_file, file=sys.stderr)

        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)
