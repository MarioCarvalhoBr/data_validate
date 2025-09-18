import os
import chardet
from typing import Tuple, List
from pathlib import Path

from src.helpers.tools.locale.language_manager import LanguageManager


class FileSystemUtils:
    """
    A class to provide file system utilities with localized messages.
    """

    def __init__(self):
        """
        Initializes the FileSystemUtils with a LocaleManager instance.

        Atributes:
            lm (LanguageManager): An instance of LanguageManager for localization.
        """
        self.lm: LanguageManager = LanguageManager()

    def detect_encoding(self, file_path: str, num_bytes: int = 1024) -> Tuple[bool, str]:
        """
        Detects the encoding of a file by reading a specified number of bytes.

        Args:
            file_path (str): The path to the file.
            num_bytes (int): The number of bytes to read for encoding detection. Default is 1024.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure
                              and the detected encoding or a translated error message.
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
        return Path(path).name

    def remove_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Removes a file at the given path if it exists.

        Args:
            file_path (str): The path to the file to remove.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure
                              and a translated message describing the result.
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
        Creates a directory with the given name if it does not already exist.

        Args:
            dir_name (str): The name of the directory to create.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure
                              and a translated message describing the result.
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
        Checks if a file exists at the given path.

        Args:
            file_path (str): The path to the file.

        Returns:
            Tuple[bool, List[str]]: A tuple containing a boolean indicating if the file exists
                                    and a list containing a single translated error message if it does not.
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
        Checks if a directory exists at the given path.

        Args:
            dir_path (str): The path to the directory.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating if the directory exists
                              and a translated error message if it does not.
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
        Checks if a directory is empty.

        Args:
            dir_path (str): The path to the directory.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating if the directory is empty
                              and a translated message describing the result.
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
