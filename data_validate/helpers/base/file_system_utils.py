#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing file system utility operations with localization support.

This module defines the `FileSystemUtils` class, which offers methods for
common file system tasks such as encoding detection, file/directory checks,
and path manipulation, all returning localized messages managed by `LanguageManager`.
"""

import os
from pathlib import Path
from typing import Tuple, List

import chardet

from data_validate.helpers.tools.locale.language_manager import LanguageManager


class FileSystemUtils:
    """
    Utility class for file system operations with localized messaging.

    Provides a comprehensive set of methods to interact with the file system,
    including file existence checks, directory creation, encoding detection,
    and cleanup. All methods return localized success/error messages.

    Attributes:
        lm (LanguageManager): Instance for handling localized string retrieval.
    """

    def __init__(self):
        """
        Initialize the FileSystemUtils instance.

        Sets up the LanguageManager to provide localized feedback for file system operations.
        """
        self.lm: LanguageManager = LanguageManager()

    def detect_encoding(self, file_path: str, num_bytes: int = 1024) -> Tuple[bool, str]:
        """
        Detect file encoding by reading a sample of bytes.

        Reads the first `num_bytes` of a file and uses `chardet` to guess its
        character encoding.

        Args:
            file_path (str): Absolute or relative path to the file.
            num_bytes (int, optional): Number of bytes to read for detection. Defaults to 1024.

        Returns:
            Tuple[bool, str]:
                - bool: True if detection was successful, False otherwise.
                - str: The detected encoding name (e.g., 'utf-8') or a localized error message.
        """
        try:
            if not file_path:
                return False, self.lm.text("fs_utils_error_file_path_empty")
            if not os.path.exists(file_path):
                return False, self.lm.text(
                    "fs_utils_error_file_not_found",
                    filename=os.path.basename(file_path),
                )
            if not os.path.isfile(file_path):
                return False, self.lm.text("fs_utils_error_path_not_file", path=file_path)

            with open(file_path, "rb") as f:
                raw_data = f.read(num_bytes)
                result = chardet.detect(raw_data)
                encoding = result.get("encoding")
                if not encoding:
                    return False, self.lm.text("fs_utils_error_encoding_failed")
                return True, encoding
        except OSError as e:
            return False, self.lm.text("fs_utils_error_encoding_os", error=str(e))
        except Exception as e:
            return False, self.lm.text("fs_utils_error_unexpected", error=str(e))

    def get_last_directory_name(self, path: str) -> str:
        """
        Extract the last component of a directory path.

        Args:
            path (str): The file system path.

        Returns:
            str: The name of the last directory or file in the path.
        """
        return Path(path).name

    def remove_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Securely remove a file from the filesystem.

        Checks if the file exists and is indeed a file before attempting removal.
        dempotent operation: returns success if the file is already gone.

        Args:
            file_path (str): Path to the file to be removed.

        Returns:
            Tuple[bool, str]:
                - bool: True if removal was successful or file didn't exist.
                - str: Localized message describing the outcome.
        """
        try:
            if not file_path:
                return False, self.lm.text("fs_utils_error_file_path_empty")
            if not os.path.exists(file_path):
                return True, self.lm.text("fs_utils_info_file_not_found", filename=os.path.basename(file_path))
            if not os.path.isfile(file_path):
                return False, self.lm.text("fs_utils_error_path_not_file", path=file_path)
            os.remove(file_path)
            return True, self.lm.text("fs_utils_success_file_removed", filename=os.path.basename(file_path))
        except OSError as e:
            return False, self.lm.text("fs_utils_error_remove_file_os", error=str(e))
        except Exception as e:
            return False, self.lm.text("fs_utils_error_unexpected", error=str(e))

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
                return False, self.lm.text("fs_utils_error_dir_path_empty")
            if os.path.exists(dir_name):
                if os.path.isdir(dir_name):
                    return True, self.lm.text("fs_utils_info_dir_exists", dir_name=dir_name)
                else:
                    return False, self.lm.text("fs_utils_error_path_not_dir", path=dir_name)
            os.makedirs(dir_name)
            return True, self.lm.text("fs_utils_success_dir_created", dir_name=dir_name)
        except OSError as e:
            return False, self.lm.text("fs_utils_error_create_dir_os", error=str(e))
        except Exception as e:
            return False, self.lm.text("fs_utils_error_unexpected", error=str(e))

    def check_file_exists(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Verify if a file exists and is a valid file.

        Args:
            file_path (str): Path to the file.

        Returns:
            Tuple[bool, List[str]]:
                - bool: True if the file exists and is valid.
                - List[str]: List containing a localized error message if check fails, empty otherwise.
        """
        try:
            if not file_path:
                return False, [self.lm.text("fs_utils_error_file_path_empty")]
            if not os.path.exists(file_path):
                return False, [
                    self.lm.text(
                        "fs_utils_error_file_not_found",
                        filename=os.path.basename(file_path),
                    )
                ]
            if not os.path.isfile(file_path):
                return False, [self.lm.text("fs_utils_error_path_not_file", path=file_path)]
            return True, []
        except Exception as e:
            return False, [self.lm.text("fs_utils_error_file_check_fail", error=str(e))]

    def check_directory_exists(self, dir_path: str) -> Tuple[bool, str]:
        """
        Verify if a directory exists and is a valid directory.

        Args:
            dir_path (str): Path to the directory.

        Returns:
            Tuple[bool, str]:
                - bool: True if the directory exists.
                - str: Localized error message if check fails, empty string otherwise.
        """
        try:
            if not dir_path:
                return False, self.lm.text("fs_utils_error_dir_path_empty")
            if not os.path.exists(dir_path):
                return False, self.lm.text("fs_utils_error_dir_not_found", dir_path=dir_path)
            if not os.path.isdir(dir_path):
                return False, self.lm.text("fs_utils_error_path_not_dir", path=dir_path)
            return True, ""
        except Exception as e:
            return False, self.lm.text("fs_utils_error_dir_check_fail", error=str(e))

    def check_directory_is_empty(self, dir_path: str) -> Tuple[bool, str]:
        """
        Check if a directory contains no files or subdirectories.

        Args:
            dir_path (str): Path to the directory.

        Returns:
            Tuple[bool, str]:
                - bool: True if directory is empty.
                - str: Localized message describing the result (e.g., directory not found, or not empty).
        """
        try:
            if not os.path.exists(dir_path):
                return False, self.lm.text("fs_utils_error_dir_not_found", dir_path=dir_path)
            if not os.path.isdir(dir_path):
                return False, self.lm.text("fs_utils_error_path_not_dir", path=dir_path)
            if not os.listdir(dir_path):
                return True, self.lm.text("fs_utils_error_dir_empty", dir_path=dir_path)
            return False, self.lm.text("fs_utils_info_dir_not_empty", dir_path=dir_path)
        except Exception as e:
            return False, self.lm.text("fs_utils_error_dir_check_fail", error=str(e))
