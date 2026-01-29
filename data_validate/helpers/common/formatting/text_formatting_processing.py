#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).


class TextFormattingProcessing:

    def __init__(self) -> None:
        pass

    @staticmethod
    def is_acronym(text: str) -> bool:
        """
        Checks if the given text is an acronym (all uppercase and length > 1).

        Args:
            text (str): The text to check.
        Returns:
            bool: True if the text is an acronym, False otherwise.
        """
        is_uppercase = text.isupper()
        has_multiple_characters = len(text) > 1

        return is_uppercase and has_multiple_characters

    @staticmethod
    def capitalize_text_keep_acronyms(text: str) -> str:
        """
        Capitalizes the first word of the text and keeps acronyms unchanged.
        All other words are converted to lowercase unless they are acronyms.

        Args:
            text (str): The input text to format.
        Returns:
            str: The formatted text with acronyms preserved.
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
