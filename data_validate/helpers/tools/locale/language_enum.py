#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

"""
Language Enum

This module defines the `Language` enum, which represents supported language codes.

Classes:
    LanguageEnum: An enumeration of supported languages.

Methods:
    list_supported_languages(): Returns a list of supported language codes.
    default_language(): Returns the default language code.

Usage Example:
    >>> print(LanguageEnum.list_supported_languages())
    ['pt_BR', 'en_US']
    >>> print(LanguageEnum.default_language())
    'pt_BR'
"""

import enum


class LanguageEnum(enum.Enum):
    """
    An enumeration of supported languages.

    Attributes:
        PT_BR (str): Represents the Brazilian Portuguese language code ('pt_BR').
        EN_US (str): Represents the American English language code ('en_US').
    """

    PT_BR = "pt_BR"
    EN_US = "en_US"
    DEFAULT_LANGUAGE = "pt_BR"

    @classmethod
    def list_supported_languages(cls):
        """
        Returns a list of supported language codes.

        Returns:
            list: A list of strings representing the supported language codes.
        """
        return [lang.value for lang in cls]

    @classmethod
    def default_language(cls):
        """
        Returns the default language code.

        Returns:
            str: The default language code ('pt_BR').
        """
        return cls.PT_BR.value


if __name__ == "__main__":
    # Example usage
    print("Supported languages:", LanguageEnum.list_supported_languages())
    print("Default language:", LanguageEnum.default_language())
