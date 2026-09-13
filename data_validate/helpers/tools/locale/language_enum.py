#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

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
        DEFAULT_LANGUAGE (str): Deliberate alias of `PT_BR` (same value, `"pt_BR"`).
            `enum.Enum` deduplicates members with equal values, so
            `DEFAULT_LANGUAGE is PT_BR` and iterating `LanguageEnum` yields only
            two members; this lets call sites write `LanguageEnum.DEFAULT_LANGUAGE.value`
            without needing a separate constant. See BUG-012 in
            `.specs/quality/backlog/01-bugs.md` (won't-fix: pinned by tests,
            folds into the ARC-002/BUG-004 locale refactor instead).
    """

    PT_BR = "pt_BR"
    EN_US = "en_US"
    DEFAULT_LANGUAGE = "pt_BR"

    @classmethod
    def list_supported_languages(cls) -> list[str]:
        """
        Returns a list of supported language codes.

        Returns:
            list: A list of strings representing the supported language codes.
        """
        return [lang.value for lang in cls]

    @classmethod
    def default_language(cls) -> str:
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
