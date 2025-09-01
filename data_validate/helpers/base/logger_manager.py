import logging
from typing import Optional
import os
from datetime import datetime


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )
    # logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LoggerManager:
    """
    A class to manage logger configuration and log file generation.

    Attributes:
        log_folder (str): The folder where log files will be stored.
        default_level (int): The default logging level.
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
        Initializes the LoggerManager.

        Args:
            log_folder (str): The folder where log files will be stored. Defaults to "logs".
            default_level (int): The default logging level. Defaults to logging.INFO.
        """
        self.log_folder = log_folder
        self.default_level = default_level
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        self.console_logger = self.configure_logger(console_logger)
        self.log_file = self.generate_log_file_name(prefix=prefix)
        self.file_logger = self.configure_logger(
            logger_name=logger_name, log_file=self.log_file
        )

    def configure_logger(
        self,
        logger_name: str,
        level: Optional[int] = None,
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        """
        Configures a logger with the specified name, level, and optional log file.

        Args:
            logger_name (str): The name of the logger.
            level (Optional[int]): The logging level. If not provided, the default level is used.
            log_file (Optional[str]): The path to the log file. If provided, logs will also be written to this file.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level or self.default_level)

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
        Generates a unique log file name with a timestamp.

        Args:
            prefix (str): The prefix for the log file name. Defaults to "app".

        Returns:
            str: The full path to the generated log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{prefix}_{timestamp}.log"
        return os.path.join(self.log_folder, file_name)


# Example usage
if __name__ == "__main__":
    logger_manager = LoggerManager(log_folder="logs/")

    # Configure a logger for console output only
    console_logger = logger_manager.configure_logger("console_logger")
    console_logger.info("This is an info message for the console logger.")

    # Configure a logger for both console and file output
    log_file = logger_manager.generate_log_file_name(prefix="my_app")
    file_logger = logger_manager.configure_logger("file_logger", log_file=log_file)
    file_logger.debug("This is a debug message for the file logger.")
    file_logger.error("This is an error message for the file logger.")

    file_logger.debug("debug message")
    file_logger.info("info message")
    file_logger.warning("warning message")
    file_logger.error("error message")
    file_logger.critical("critical message")
