"""
Configuration module for the Data Validate application.

This module defines the configuration settings, constants, and enumerations used throughout
the application. It includes the `NamesEnum` for verification names and the `ApplicationConfig` class
for managing application-wide settings such as limits, date formats, and report templates.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from collections.abc import Callable
from datetime import datetime
from types import MappingProxyType

from data_validate.config.names_enum import NamesEnum
from data_validate.config.spreadsheet_info import SpreadsheetInfo
from data_validate.helpers.tools.locale.language_manager import LanguageManager


class ApplicationConfig:
    """
    Configuration class for Data Validate application.

    This class holds all the configuration constants and settings for the application.
    It includes settings for numeric precision, text limits, date/time formats,
    value representations, report generation settings, and file extensions.

    Attributes:
        language_manager (LanguageManager): Manager for handling localized text.
        spreadsheet_info (SpreadsheetInfo): Information about the spreadsheets used in the application.
        names_enum (NamesEnum): Enumeration of verification names used in the application.
    """

    # NUMBERS
    PRECISION_DECIMAL_PLACE_TRUNCATE = 3
    """int: The number of decimal places to truncate numbers to."""

    # INPUT SIZE LIMITS (SEC-003)
    MAX_INPUT_FILE_BYTES = 100 * 1024 * 1024
    """int: Maximum allowed size, in bytes, of a single input spreadsheet file (100 MB). A
    generous DoS guard against zip-bomb-style or accidental huge uploads exhausting memory —
    not a business rule. A file above this size is not read at all; see SEC-003."""
    MAX_SHEET_ROWS = 1_000_000
    """int: Maximum allowed number of rows in a loaded sheet, checked after reading. Same DoS-guard
    rationale as `MAX_INPUT_FILE_BYTES`; see SEC-003."""
    MAX_SHEET_COLUMNS = 5_000
    """int: Maximum allowed number of columns in a loaded sheet, checked after reading. Same
    DoS-guard rationale as `MAX_INPUT_FILE_BYTES`; see SEC-003."""

    # DESCRIPTION LIMITS
    TITLE_OVER_N_CHARS = 40
    """int: Maximum number of characters allowed for titles."""
    SIMPLE_DESCRIPTIONS_OVER_N_CHARS = 150
    """int: Maximum number of characters allowed for simple description fields."""

    # VALUE AND LEGEND
    LABEL_DATA_UNAVAILABLE = "Dado indisponível"
    """str: Label used for unavailable data in reports."""
    VALUE_DATA_UNAVAILABLE = "DI"
    """str: Value used to represent unavailable data in datasets."""

    # REPORT
    REPORT_LIMIT_N_MESSAGES = 20
    """int: Maximum number of error messages to display per validation type in reports."""
    REPORT_OUTPUT_REPORT_HTML = "_report.html"
    """str: Suffix for generated HTML report files."""

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
        language_manager: LanguageManager | None = None,
    ):
        """
        Initializes the ApplicationConfig instance.

        Sets up the LanguageManager for handling localized strings throughout the application,
        and computes `CURRENT_YEAR`/`DATE_NOW` from the given (or default) clock at construction
        time, instead of once at import time (BUG-011).

        Args:
            clock (Callable[[], datetime] | None): Zero-argument callable returning the current
                `datetime`, used to compute `CURRENT_YEAR` and `DATE_NOW`. Defaults to
                `datetime.now` when not provided; injectable for testing/determinism.
            language_manager (LanguageManager | None): Shared `LanguageManager` instance
                (ARC-002/BUG-004/BUG-023: a single locale source of truth). When not given,
                builds its own with `locale=None` (backwards compatible default behaviour).
        """
        self._clock = clock or datetime.now

        # DATE AND TIME
        self.CURRENT_YEAR = self._clock().year
        """int: The current year."""
        self.DATE_NOW = self._clock().strftime("%d/%m/%Y %H:%M:%S")
        """str: The current date and time formatted as 'dd/mm/yyyy HH:MM:SS'."""

        self.language_manager: LanguageManager = language_manager or LanguageManager()
        self.spreadsheet_info = SpreadsheetInfo()
        self.names_enum = NamesEnum
        self._verify_names_cache: MappingProxyType | None = None

    def get_verify_names(self):
        """
        Retrieves a dictionary of verification names with localized text.

        The method iterates over `NamesEnum` members and retrieves their localized
        string representation using the `LanguageManager`. For specific verifications
        like `TITLES_N` and `SIMP_DESC_N`, it formats the message with dynamic values
        from configuration constants.

        The result is computed once and cached on the instance (PERF-004): this method
        is called once per validator (`BaseValidator.__init__`) plus twice more in
        `FileReportGenerator`, so without caching every run repeats the same 34 catalog
        lookups a dozen-plus times.

        Returns:
            MappingProxyType: A read-only dictionary mapping verification keys (from `NamesEnum`)
            to their localized text descriptions.
        """
        if self._verify_names_cache is not None:
            return self._verify_names_cache

        keys = [element for element in NamesEnum]
        values = [
            (
                self.language_manager.text(
                    str(element.value),
                    value=(
                        self.TITLE_OVER_N_CHARS
                        if element == NamesEnum.TITLES_N
                        else (self.SIMPLE_DESCRIPTIONS_OVER_N_CHARS if element == NamesEnum.SIMP_DESC_N else None)
                    ),
                )
                if element in (NamesEnum.TITLES_N, NamesEnum.SIMP_DESC_N)
                else self.language_manager.text(str(element.value))
            )
            for element in keys
        ]
        self._verify_names_cache = MappingProxyType(dict(zip([e.value for e in keys], values)))
        return self._verify_names_cache
