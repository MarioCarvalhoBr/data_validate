#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
This module provides classes for argument parsing, validation, and configuration
used in the Adapta Parser project.

Classes:
    DataModelABC: Abstract base class for argument parsing and validation.
    DataFile: Handles file-related arguments and operations.
    DataAction: Handles action-related arguments and operations.
    DataReport: Handles report-related arguments and operations.
    DataArgs: Main class for parsing and managing all program arguments.

"""

import argparse
import os
from abc import ABC, abstractmethod


class DataModelABC(ABC):
    """
    Abstract base class for argument parsing and validation.

    Methods:
        _validate_arguments(): Abstract method to validate parsed arguments.
    """

    def __init__(self):
        """
        Initializes the DataModelABC class.
        """
        pass

    @abstractmethod
    def _validate_arguments(self):
        """
        Validates the parsed arguments.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class DataFile(DataModelABC):
    """
    Handles file-related arguments and operations.

    Attributes:
        input_folder (str): Path to the input folder.
        output_folder (str): Path to the output folder.
        locale (str): Locale setting.

    Methods:
        _validate_arguments(): Validates the file-related arguments.
        run(): Parses and validates the arguments.
    """

    def __init__(self, input_folder=None, output_folder=None, locale=None):
        """
        Initializes the DataFile class with default attributes.

        Args:
            input_folder (str, optional): Path to the input folder.
            output_folder (str, optional): Path to the output folder.
            locale (str, optional): Locale setting.
        """
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.locale = locale

        # Run the argument parser
        self.run()

    def _validate_arguments(self):
        """
        Validates the file-related arguments.

        Raises:
            ValueError: If the input folder does not exist or the output folder name is invalid.
        """
        if not os.path.isdir(self.input_folder):
            raise ValueError(f"Input folder does not exist: {self.input_folder}")

        if not os.path.basename(self.output_folder):
            raise ValueError(f"Invalid output folder name: {self.output_folder}")

    def run(self):
        """
        Parses and validates the file-related arguments.
        """
        self._validate_arguments()


class DataAction(DataModelABC):
    """
    Handles action-related arguments and operations.

    Attributes:
        no_spellchecker (bool): Indicates whether the spell checker should be disabled.
        no_warning_titles_length (bool): Indicates whether warnings for title length should be disabled.
        no_time (bool): Indicates whether execution time and date information should be hidden.
        no_version (bool): Indicates whether the script version should be hidden in the final report.
        debug (bool): Indicates whether the program should run in debug mode.

    Methods:
        __init__(no_spellchecker=None, no_warning_titles_length=None, no_time=None, no_version=None, debug=None):
            Initializes the DataAction class with the provided arguments.
        _validate_arguments():
            Validates the action-related arguments.
        run():
            Parses and validates the command-line arguments.
    """
    def __init__(self, no_spellchecker=None, no_warning_titles_length=None, no_time=None, no_version=None, debug=None):
        """
        Initializes the DataAction class with default attributes.

        Args:
            no_spellchecker (bool, optional): Disables the spell checker. Defaults to None.
            no_warning_titles_length (bool, optional): Disables warnings for title length. Defaults to None.
            no_time (bool, optional): Hides execution time and date information. Defaults to None.
            no_version (bool, optional): Hides the script version in the final report. Defaults to None.
            debug (bool, optional): Runs the program in debug mode. Defaults to None.
        """
        super().__init__()
        self.no_spellchecker = no_spellchecker
        self.no_warning_titles_length = no_warning_titles_length
        self.no_time = no_time
        self.no_version = no_version
        self.debug = debug

        # Run the argument parser
        self.run()

    def _validate_arguments(self):
        """
        Validates the parsed arguments.

        Raises:
            ValueError: If any of the arguments are not of the expected type.
        """
        if not isinstance(self.no_spellchecker, bool):
            raise ValueError("no_spellchecker must be a boolean value.")
        if not isinstance(self.no_warning_titles_length, bool):
            raise ValueError("no_warning_titles_length must be a boolean value.")
        if not isinstance(self.no_time, bool):
            raise ValueError("no_time must be a boolean value.")
        if not isinstance(self.no_version, bool):
            raise ValueError("no_version must be a boolean value.")
        if not isinstance(self.debug, bool):
            raise ValueError("debug must be a boolean value.")

    def run(self):
        """
        Parses and validates the command-line arguments.
        """
        self._validate_arguments()


class DataReport(DataModelABC):
    """
    Handles report-related arguments and operations.

    Attributes:
        sector (str): Name of the strategic sector.
        protocol (str): Name of the protocol.
        user (str): Name of the user.
        file (str): Name of the file to be analyzed.

    Methods:
        __init__(sector=None, protocol=None, user=None, file=None):
            Initializes the DataReport class with the provided arguments.
        _validate_arguments():
            Validates the report-related arguments.
        run():
            Parses and validates the command-line arguments.
    """

    def __init__(self, sector=None, protocol=None, user=None, file=None):
        """
        Initializes the DataReport class with default attributes.

        Args:
            sector (str, optional): Name of the strategic sector. Defaults to None.
            protocol (str, optional): Name of the protocol. Defaults to None.
            user (str, optional): Name of the user. Defaults to None.
            file (str, optional): Name of the file to be analyzed. Defaults to None.
        """
        super().__init__()
        self.sector = sector
        self.protocol = protocol
        self.user = user
        self.file = file

        # Run the argument parser
        self.run()

    def _validate_arguments(self):
        """
        Validates the report-related arguments.

        Raises:
            ValueError: If any of the arguments are invalid.
        """
        pass

    def run(self):
        """
        Parses and validates the command-line arguments.
        """
        self._validate_arguments()


class DataArgs:
    """
    A class to handle argument parsing, configuration, and validation.

    Attributes:
        data_file (DataFile): Instance for handling file-related arguments.
        data_action (DataAction): Instance for handling action-related arguments.
        data_report (DataReport): Instance for handling report-related arguments.
        allow_abbrev (bool): Indicates if argument abbreviations are allowed.

    Methods:
        _create_parser(): Creates and configures the argument parser.
        get_dict_args(): Returns the parsed arguments as a dictionary.
        __str__(): Returns a string representation of the parsed arguments.
        run(): Parses and validates the command-line arguments.
    """

    def __init__(self, allow_abbrev=True):
        """
        Initializes the DataArgs class with default attributes.

        Args:
            allow_abbrev (bool, optional): Allows argument abbreviations. Defaults to True.
        """
        self.data_file = None
        self.data_action = None
        self.data_report = None
        self.allow_abbrev = allow_abbrev

        # Run the argument parser
        self.run()

    def _create_parser(self):
        """
        Creates an argument parser with the required arguments.

        Returns:
            argparse.ArgumentParser: The configured argument parser.
        """
        parser = argparse.ArgumentParser(
            description="Adapta Parser - Processes the program arguments.",
            allow_abbrev=self.allow_abbrev
        )

        # Arguments for DataFile
        parser.add_argument("--input_folder", type=str, required=True, help="Path to the input folder.")
        parser.add_argument("--output_folder", default="output_data/", type=str, help="Path to the output folder.")
        parser.add_argument("--locale", "-l", type=str, choices=["pt_BR", "en_US"], default="pt_BR",
                            help="Sets the locale (pt_BR or en_US).")

        # Arguments for DataAction
        parser.add_argument("--no-spellchecker", action="store_true", help="Disables the spell checker.")
        parser.add_argument("--no-warning-titles-length", action="store_true",
                            help="Disables warnings for title length.")
        parser.add_argument("--no-time", action="store_true", help="Hides execution time and date information.")
        parser.add_argument("--no-version", action="store_true", help="Hides the script version in the final report.")
        parser.add_argument("--debug", action="store_true", help="Runs the program in debug mode.")

        # Arguments for DataReport
        parser.add_argument("--sector", type=str, default=None, help="Name of the strategic sector.")
        parser.add_argument("--protocol", type=str, default=None, help="Name of the protocol.")
        parser.add_argument("--user", type=str, default=None, help="Name of the user.")
        parser.add_argument("--file", type=str, default=None, help="Name of the file to be analyzed.")

        return parser

    def get_dict_args(self):
        """
        Returns the parsed arguments as a dictionary.

        Returns:
            dict: Dictionary of parsed arguments.
        """
        return {
            "input_folder": self.data_file.input_folder,
            "output_folder": self.data_file.output_folder,
            "locale": self.data_file.locale,
            "no_spellchecker": self.data_action.no_spellchecker,
            "no_warning_titles_length": self.data_action.no_warning_titles_length,
            "no_time": self.data_action.no_time,
            "no_version": self.data_action.no_version,
            "debug": self.data_action.debug,
            "sector": self.data_report.sector,
            "protocol": self.data_report.protocol,
            "user": self.data_report.user,
            "file": self.data_report.file
        }

    def __str__(self):
        """
        Returns a string representation of the parsed arguments.

        Returns:
            str: String representation of the parsed arguments.
        """
        return f"DataArgs(input_folder={self.data_file.input_folder}, " \
               f"output_folder={self.data_file.output_folder}, locale={self.data_file.locale}, " \
               f"no_spellchecker={self.data_action.no_spellchecker}, " \
               f"no_warning_titles_length={self.data_action.no_warning_titles_length}, " \
               f"no_time={self.data_action.no_time}, no_version={self.data_action.no_version}, " \
               f"debug={self.data_action.debug}, sector={self.data_report.sector}, " \
               f"protocol={self.data_report.protocol}, user={self.data_report.user}, " \
               f"file={self.data_report.file})"

    def run(self):
        """
        Parses and validates the command-line arguments.
        """
        # Create argument parser
        parser = self._create_parser()

        # Parse arguments
        args = parser.parse_args()

        # Set attributes: DataFile, DataAction, DataReport
        self.data_file = DataFile(args.input_folder, args.output_folder, args.locale)
        self.data_action = DataAction(args.no_spellchecker, args.no_warning_titles_length, args.no_time,
                                      args.no_version, args.debug)
        self.data_report = DataReport(args.sector, args.protocol, args.user, args.file)

