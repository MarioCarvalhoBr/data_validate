#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing a customized logging system with color formatting.

This module defines the `LoggerManager` for managing application-wide logging
configurations and `CustomFormatter` for adding ANSI color codes to log
messages based on their severity level.
"""

import logging
import os
from datetime import datetime
from typing import Optional


class CustomFormatter(logging.Formatter):
    """
    Log formatter that adds colors to log levels for console output.

    Extends `logging.Formatter` to prepend ANSI color codes to log messages
    depending on the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Attributes:
        grey (str): ANSI code for grey text (Debug/Info).
        yellow (str): ANSI code for yellow text (Warning).
        red (str): ANSI code for red text (Error).
        bold_red (str): ANSI code for bold red text (Critical).
        reset (str): ANSI code to reset terminal formatting.
        format (str): The log message format string.
        FORMATS (dict): Mapping of log levels to formatted strings.
    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    # logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        """
        Format the specified record as text.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with color codes.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LoggerManager:
    """
    Manager for logger configuration and log file generation.

    Handles the setup of both console and file loggers, including directory creation
    and applying custom formatters.

    Attributes:
        log_folder (str): The directory path where log files will be stored.
        default_level (int): The default logging severity level.
        console_logger (logging.Logger): Configured logger for console output.
        log_file (str): Path to the generated log file.
        file_logger (logging.Logger): Configured logger for file output.
    """

    def __init__(
        self,
        log_folder: str = "logs",
        default_level: int = logging.DEBUG,
        console_logger="console_logger",
        prefix="data_validate",
        logger_name="data_validate_file_logger",
    ):
        """
        Initialize the LoggerManager.

        Sets up the log directory and initializes both the console and file loggers.

        Args:
            log_folder (str, optional): Directory for log files. Defaults to "logs".
            default_level (int, optional): Default log level. Defaults to logging.DEBUG.
            console_logger (str, optional): Name for the console logger. Defaults to "console_logger".
            prefix (str, optional): Prefix for the log file name. Defaults to "data_validate".
            logger_name (str, optional): Name for the file logger. Defaults to "data_validate_file_logger".
        """
        self.log_folder = log_folder
        self.default_level = default_level
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        self.console_logger = self.configure_logger(console_logger)
        self.log_file = self.generate_log_file_name(prefix=prefix)
        self.file_logger = self.configure_logger(logger_name=logger_name, log_file=self.log_file)

    def configure_logger(
        self,
        logger_name: str,
        level: Optional[int] = None,
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        """
        Configure a logger with the specified name, level, and optional output file.

        Creates or retrieves a logger, clears existing handlers to prevent duplication,
        and attaches a console handler (with colors) and optionally a file handler.

        Args:
            logger_name (str): The unique name of the logger.
            level (Optional[int]): The logging level. Uses default_level if None.
            log_file (Optional[str]): Path to a file where logs should be saved.

        Returns:
            logging.Logger: The fully configured logger instance.
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level or self.default_level)
        logger.propagate = False

        if logger.hasHandlers():
            logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()

        # Formatter for log messages
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(CustomFormatter())
            logger.addHandler(file_handler)

        return logger

    def generate_log_file_name(self, prefix: str = "app") -> str:
        """
        Generate a unique timestamped log file name.

        Creates a filename in the format `{prefix}_{YYYYMMDD}_{HHMMSS}.log` inside
        the configured log folder.

        Args:
            prefix (str, optional): Prefix for the filename. Defaults to "app".

        Returns:
            str: The absolute path to the generated log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{prefix}_{timestamp}.log"
        return os.path.join(self.log_folder, file_name)
