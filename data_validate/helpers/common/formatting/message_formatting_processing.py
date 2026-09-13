#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing text formatting for error and warning messages.

This module defines the `MessageFormattingProcessing` class, which generates
standardized messages for validation issues such as missing or extra columns
in data files.
"""

from typing import Callable, List, Optional, Tuple

from data_validate.helpers.common.default_translate import get_default_translate


class MessageFormattingProcessing:
    """
    Utility class for formatting validation messages.

    Provides static methods to construct user-friendly error and warning messages
    related to data structure validation.
    """

    def __init__(self) -> None:
        """Initialize the MessageFormattingProcessing class."""
        pass

    @staticmethod
    def format_text_to_missing_and_expected_columns(
        file_name: str,
        missing_columns: List[str],
        extra_columns: List[str],
        translate: Optional[Callable[..., str]] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Format error and warning messages for missing and extra columns in a file.

        Constructs lists of localized strings describing structural issues found
        during file validation.

        Args:
            file_name (str): Name of the file being checked.
            missing_columns (List[str]): List of missing column names.
            extra_columns (List[str]): List of extra column names.
            translate (Callable[..., str], optional): Message-catalog renderer
                (`key, **params -> str`). ARC-005: every message is a catalog key
                (`rule.STRUCT-011.error` / `rule.STRUCT-012.warning`), never a
                hardcoded literal; defaults to `get_default_translate()` so existing
                direct callers keep working unchanged.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing:
                - List of error messages for missing columns.
                - List of warning messages for extra (unexpected) columns.
        """
        translate = translate or get_default_translate()
        # SEC-004: this is pure string formatting over two lists of names — there is no
        # plausible failure mode here worth downgrading to a data-quality message, so the
        # previous `except Exception` fallback (and its own hardcoded pt-BR message) is gone;
        # a genuine programming error now propagates instead of being silently reported as one
        # more "column" error, matching `check_dataframe_vertical_bar`/`check_dataframe_unnamed_columns`.
        errors = [translate("rule.STRUCT-011.error", filename=file_name, column=col) for col in missing_columns]
        warnings = [translate("rule.STRUCT-012.warning", filename=file_name, column=col) for col in extra_columns]
        return errors, warnings
