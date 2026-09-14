#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing file system utility operations with localization support.

This module defines the `FileSystemUtils` class, which offers methods for
directory creation and path manipulation, returning localized messages
managed by `LanguageManager`.

SEC-004: every method catches `OSError` only -- the family that `os.path.*`
and `os.makedirs()` can plausibly raise (permission denied, missing/broken
path, I/O failure). A genuinely unexpected exception is no longer converted
into a localized "unexpected error" string; it propagates to `main()`'s
boundary, which reports it as a fatal error and exits with code 2 -- the
designed behaviour for a programming error, per `.claude/rules/security.md`.
"""

import os
from pathlib import Path
from typing import Tuple


from data_validate.helpers.tools.locale.language_manager import LanguageManager


class FileSystemUtils:
    """
    Utility class for file system operations with localized messaging.

    Provides directory creation and path-manipulation helpers. All methods
    return localized success/error messages.

    Attributes:
        language_manager (LanguageManager): Instance for handling localized string retrieval.
    """

    def __init__(self, language_manager: LanguageManager | None = None):
        """
        Initialize the FileSystemUtils instance.

        Args:
            language_manager (LanguageManager | None): Shared `LanguageManager` instance
                (ARC-002/BUG-004/BUG-023: a single locale source of truth). When not given,
                builds its own with `locale=None` (backwards compatible default behaviour).
        """
        self.language_manager: LanguageManager = language_manager or LanguageManager()

    def get_last_directory_name(self, path: str) -> str:
        """
        Extract the last component of a directory path.

        Args:
            path (str): The file system path.

        Returns:
            str: The name of the last directory or file in the path.
        """
        return Path(path).name

    def create_directory(self, dir_name: str) -> Tuple[bool, str]:
        """
        Create a new directory if it does not exist.

        Args:
            dir_name (str): Name or path of the directory to create.

        Returns:
            Tuple[bool, str]:
                - bool: True if created or already exists as a directory.
                - str: Localized message describing the result.
        """
        try:
            if not dir_name:
                return False, self.language_manager.text("fs_utils_error_dir_path_empty")
            if os.path.exists(dir_name):
                if os.path.isdir(dir_name):
                    return True, self.language_manager.text("fs_utils_info_dir_exists", dir_name=dir_name)
                else:
                    return False, self.language_manager.text("fs_utils_error_path_not_dir", path=dir_name)
            os.makedirs(dir_name)
            return True, self.language_manager.text("fs_utils_success_dir_created", dir_name=dir_name)
        except OSError as e:
            return False, self.language_manager.text("fs_utils_error_create_dir_os", error=str(e))
