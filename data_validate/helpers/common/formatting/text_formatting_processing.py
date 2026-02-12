#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing text formatting utilities for string manipulation.

This module defines the `TextFormattingProcessing` class, which offers methods
for identifying acronyms and applying specific capitalization rules to text strings,
preserving acronyms where appropriate.
"""


class TextFormattingProcessing:
    """
    Utility class for text string manipulation and formatting.

    Provides static methods to handle specific text capitalization requirements,
    such as identifying potential acronyms and ensuring they remain uppercase
    while standardizing the rest of the text.
    """

    def __init__(self) -> None:
        """Initialize the TextFormattingProcessing class."""
        pass

    @staticmethod
    def is_acronym(text: str) -> bool:
        """
        Check if the given text is an acronym.

        An acronym is defined here as a string that is fully uppercase and has
        more than one character.

        Args:
            text (str): The text string to evaluate.

        Returns:
            bool: True if the text is an acronym, False otherwise.
        """
        is_uppercase = text.isupper()
        has_multiple_characters = len(text) > 1

        return is_uppercase and has_multiple_characters

    @staticmethod
    def capitalize_text_keep_acronyms(text: str) -> str:
        """
        Capitalize the first word of the text while preserving acronyms.

        Converts the first word to title case (unless it's an acronym).
        All subsequent words are converted to lowercase, unless identified as acronyms,
        in which case they remain uppercase.

        Args:
            text (str): The input text string to format.

        Returns:
            str: The formatted text with proper capitalization and preserved acronyms.
        """
        words = text.split()
        capitalized_words = []

        for i, word in enumerate(words):
            if TextFormattingProcessing.is_acronym(word):
                capitalized_words.append(word)
            elif i == 0:
                capitalized_words.append(word.capitalize())
            else:
                capitalized_words.append(word.lower())

        return " ".join(capitalized_words)
