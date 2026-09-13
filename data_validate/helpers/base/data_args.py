#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module provided to handle argument parsing, validation, and configuration.

This module defines classes for managing command-line arguments related to:
- Input/output files and folders (DataFile)
- Execution flags and actions (DataAction)
- Report metadata (DataReport)
- Main argument orchestration (DataArgs)
"""

import argparse
import sys
from abc import ABC, abstractmethod
from pathlib import Path


def _resolve_path(path: str) -> Path:
    """Resolve `path` to an absolute, normalized `Path` (SEC-010).

    Args:
        path: Absolute or relative filesystem path, as given on the command line.

    Returns:
        Path: The resolved path. `Path.resolve()` does not require `path` to exist.
    """
    return Path(path).resolve()


def _make_deprecated_alias_action(replacement: str) -> type[argparse.Action]:
    """Build an `argparse.Action` for a legacy, two-dash short flag (ARC-011).

    Flags like `--i`/`--o`/`--l`/`--d` only ever worked because
    `allow_abbrev=True` let argparse prefix-match them onto the long option
    names; now that `allow_abbrev` can be `False`, they are declared
    explicitly, sharing the same destination as their modern replacement, so
    they keep working for one deprecation window. Using one of them prints a
    single warning line to stderr (developer-facing, plain English) naming
    the replacement, then behaves exactly like the replacement flag.

    Args:
        replacement: Human-readable name of the flag(s) that replace this alias.

    Returns:
        type[argparse.Action]: A concrete `argparse.Action` subclass.
    """

    class _DeprecatedAliasAction(argparse.Action):
        """Stores a value under the replacement's destination, with a warning."""

        def __call__(self, parser, namespace, values, option_string=None):
            print(
                f"Warning: '{option_string}' is deprecated; use '{replacement}' instead.",
                file=sys.stderr,
            )
            value = self.const if self.nargs == 0 else values
            setattr(namespace, self.dest, value)

    return _DeprecatedAliasAction


class DataModelABC(ABC):
    """
    Abstract base class for argument parsing and validation.

    Defines the contract for argument collection classes, requiring implementation
    of validation logic.

    Methods:
        _validate_arguments(): Abstract method to validate parsed arguments.
    """

    def __init__(self):
        """Initialize the DataModelABC class."""
        pass

    @abstractmethod
    def _validate_arguments(self):
        """
        Validate the parsed arguments.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class DataFile(DataModelABC):
    """
    Handles file-related arguments and operations.

    Manages input and output paths and localization settings.
    Executes validation logic immediately upon instantiation.

    Attributes:
        input_folder (str): Absolute, resolved path to the input data directory
            (`Path.resolve()`, SEC-010). Accepted as an absolute or relative path
            on the command line; normalized on validation.
        output_folder (str): Absolute, resolved path to the output directory
            (`Path.resolve()`, SEC-010). Accepted as an absolute or relative path
            on the command line; normalized on validation.
        locale (str): Language/region code (e.g., 'pt_BR', 'en_US').
    """

    def __init__(self, input_folder=None, output_folder=None, locale=None):
        """
        Initialize the DataFile class with file paths and locale.

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
        Validate the file-related arguments.

        Both paths are resolved once, via `Path.resolve()` (SEC-010), so every downstream
        consumer (report generator, spreadsheet processor, data loader) sees an absolute,
        normalized path regardless of what was typed on the command line (relative,
        containing `.`/`..`, or a symlink). Checks if the input folder exists and if the
        output folder path is usable as a directory: any path is accepted, including ones
        whose basename contains a dot (e.g. `run.2026-08`, `v1.2`), except a path that
        already exists as a regular file, which can never become a directory.

        Raises:
            ValueError: If the input folder does not exist or the output folder path
                already exists as a regular file.
        """
        resolved_input_folder = _resolve_path(self.input_folder)
        resolved_output_folder = _resolve_path(self.output_folder)

        if not resolved_input_folder.is_dir():
            raise ValueError(f"Input folder does not exist: {self.input_folder}")

        if resolved_output_folder.is_file():
            raise ValueError(f"Output folder name is invalid: {self.output_folder}")

        self.input_folder = str(resolved_input_folder)
        self.output_folder = str(resolved_output_folder)

    def run(self):
        """Execute parsing and validation of file arguments."""
        self._validate_arguments()


class DataAction(DataModelABC):
    """
    Handles action-related arguments and operations settings.

    Manages boolean flags that control the behavior of the validation process,
    such as disabling checks, hiding information, or enabling debug mode.

    Attributes:
        no_spellchecker (bool): If True, disables spell checking.
        no_warning_titles_length (bool): If True, suppresses title length warnings.
        no_time (bool): If True, hides execution time metadata.
        no_version (bool): If True, hides version information in reports.
        debug (bool): If True, enables verbose debug logging.
    """

    def __init__(
        self,
        no_spellchecker=None,
        no_warning_titles_length=None,
        no_time=None,
        no_version=None,
        debug=None,
    ):
        """
        Initialize the DataAction class with configuration flags.

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
        Validate the action-related arguments.

        Ensures that all action flags are boolean values.

        Raises:
            ValueError: If any flag is not a boolean instance.
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
        """Execute parsing and validation of action arguments."""
        self._validate_arguments()


class DataReport(DataModelABC):
    """
    Handles report-related metadata arguments.

    Stores optional metadata information to be included in the generated reports,
    such as user name, sector, and protocol details.

    Attributes:
        sector (str): Name of the strategic sector being analyzed.
        protocol (str): Name of the protocol or standard used.
        user (str): Name of the user running the validation.
        file (str): Name of the file being processed.
    """

    def __init__(self, sector=None, protocol=None, user=None, file=None):
        """
        Initialize the DataReport class with metadata.

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
        Validate the report-related arguments.

        Currently performs no specific validation (placeholder for future rules).

        Raises:
            ValueError: If any validaton rule fails.
        """
        pass

    def run(self):
        """Execute parsing and validation of report arguments."""
        self._validate_arguments()


class DataArgs:
    """
    Main orchestration class for argument parsing, configuration, and validation.

    Aggregates `DataFile`, `DataAction`, and `DataReport` to provide a centralized
    access point for all application configuration parameters parsed from command line.

    Attributes:
        data_file (DataFile): Instance handling file/path inputs.
        data_action (DataAction): Instance handling execution flags.
        data_report (DataReport): Instance handling report metadata.
        allow_abbrev (bool): Whether to allow argument abbreviation in argparse.
        json_path (str | None): Path to write the JSON validation summary to, or None.
        fail_on (str): Exit-code policy: "error" (default), "warning", or "never".
    """

    def __init__(self, allow_abbrev=True):
        """
        Initialize the DataArgs class and parse CLI arguments immediately.

        Args:
            allow_abbrev (bool, optional): Allows argument abbreviations. Defaults to True.
        """

        self.data_file = None
        self.data_action = None
        self.data_report = None
        self.allow_abbrev = allow_abbrev
        self.json_path: str | None = None
        self.fail_on: str = "error"

        # Run the argument parser
        self.run()

    def _create_parser(self):
        """
        Create and configure the ArgumentParser object.

        Defines all supported command-line arguments across file, action, and report
        categories.

        Returns:
            argparse.ArgumentParser: The configured argument parser.
        """
        # Local import: `metadata_info` (via `data_validate.config`) transitively imports
        # `helpers.base.constant_base`, which would re-enter `helpers/base/__init__.py`
        # (which imports this very module) if this were a top-level import — a circular
        # import. Deferring it to call time (after the package has finished loading) avoids it.
        from data_validate.config.metadata_info import METADATA

        parser = argparse.ArgumentParser(
            description="Adapta Parser - Processes the program arguments.",
            allow_abbrev=self.allow_abbrev,
        )

        # Arguments for DataFile
        parser.add_argument(
            "-i",
            "--input",
            "--input_folder",
            dest="input_folder",
            type=str,
            default=None,
            help="Path to the input folder.",
        )
        parser.add_argument(
            "-o",
            "--output",
            "--output_folder",
            dest="output_folder",
            default="output_data/",
            type=str,
            help="Path to the output folder.",
        )
        parser.add_argument(
            "--locale",
            "-l",
            type=str,
            choices=["pt_BR", "en_US"],
            default="pt_BR",
            help="Sets the locale (pt_BR or en_US).",
        )

        # Deprecated two-dash short aliases (ARC-011) — see `_make_deprecated_alias_action`.
        parser.add_argument(
            "--i",
            dest="input_folder",
            action=_make_deprecated_alias_action("-i/--input"),
            default=argparse.SUPPRESS,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--o",
            dest="output_folder",
            action=_make_deprecated_alias_action("-o/--output"),
            default=argparse.SUPPRESS,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--l",
            dest="locale",
            choices=["pt_BR", "en_US"],
            action=_make_deprecated_alias_action("-l/--locale"),
            default=argparse.SUPPRESS,
            help=argparse.SUPPRESS,
        )

        # Arguments for DataAction
        parser.add_argument("--no-spellchecker", action="store_true", help="Disables the spell checker.")
        parser.add_argument(
            "--no-warning-titles-length",
            action="store_true",
            help="Disables warnings for title length.",
        )
        parser.add_argument(
            "--no-time",
            action="store_true",
            help="Hides execution time and date information.",
        )
        parser.add_argument(
            "--no-version",
            action="store_true",
            help="Hides the script version in the final report.",
        )
        parser.add_argument("--debug", action="store_true", help="Runs the program in debug mode.")
        parser.add_argument(
            "--d",
            dest="debug",
            nargs=0,
            const=True,
            action=_make_deprecated_alias_action("--debug"),
            default=argparse.SUPPRESS,
            help=argparse.SUPPRESS,
        )

        # Arguments for DataReport
        parser.add_argument("--sector", type=str, default=None, help="Name of the strategic sector.")
        parser.add_argument("--protocol", type=str, default=None, help="Name of the protocol.")
        parser.add_argument("--user", type=str, default=None, help="Name of the user.")
        parser.add_argument("--file", type=str, default=None, help="Name of the file to be analyzed.")

        # CLI-contract flags (ARC-011/SEC-008): JSON summary file and exit-code policy.
        parser.add_argument(
            "--json",
            dest="json_path",
            type=str,
            default=None,
            metavar="PATH",
            help="Write the JSON validation summary to PATH as pretty JSON (UTF-8).",
        )
        parser.add_argument(
            "--fail-on",
            dest="fail_on",
            choices=["error", "warning", "never"],
            default="error",
            help="Exit code policy: fail on validation errors (default), on any warning, or never.",
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {METADATA.__version__}",
            help="Show the program's version number and exit.",
        )

        return parser

    def get_dict_args(self):
        """
        Return the parsed arguments as a dictionary.

        Aggregates attributes from all sub-models (file, action, report) into a single
        dictionary for easier serialization or logging.

        Returns:
            dict: Dictionary of all parsed arguments.
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
            "file": self.data_report.file,
        }

    def __str__(self):
        """
        Return a string representation of the parsed arguments.

        Returns:
            str: String representation of the parsed arguments.
        """
        return (
            f"DataArgs(input_folder={self.data_file.input_folder}, "
            f"output_folder={self.data_file.output_folder}, locale={self.data_file.locale}, "
            f"no_spellchecker={self.data_action.no_spellchecker}, "
            f"no_warning_titles_length={self.data_action.no_warning_titles_length}, "
            f"no_time={self.data_action.no_time}, no_version={self.data_action.no_version}, "
            f"debug={self.data_action.debug}, sector={self.data_report.sector}, "
            f"protocol={self.data_report.protocol}, user={self.data_report.user}, "
            f"file={self.data_report.file})"
        )

    def run(self):
        """
        Parse and validate the command-line arguments.

        Orchestrates the parsing flow:
        1. Creates the parser.
        2. Parses arguments from sys.argv.
        3. Initializes `DataFile`, `DataAction`, and `DataReport` with parsed values.

        Raises:
            SystemExit: Via `parser.error()` when none of `--input_folder`/`--input`/`-i`
                was given (input is required, but shared across three aliases, so it
                cannot be declared `required=True` on a single `argparse` action).
        """
        # Create argument parser
        parser = self._create_parser()

        # Parse arguments
        args = parser.parse_args()

        if not args.input_folder:
            parser.error("the following arguments are required: --input_folder/--input/-i")

        # Set attributes: DataFile, DataAction, DataReport
        self.data_file = DataFile(args.input_folder, args.output_folder, args.locale)
        self.data_action = DataAction(
            args.no_spellchecker,
            args.no_warning_titles_length,
            args.no_time,
            args.no_version,
            args.debug,
        )
        self.data_report = DataReport(args.sector, args.protocol, args.user, args.file)
        self.json_path = args.json_path
        self.fail_on = args.fail_on
