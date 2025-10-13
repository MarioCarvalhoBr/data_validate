#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re


class TextProcessor:
    """Text processor for cleaning and preprocessing."""

    @staticmethod
    def is_acronym(text: str) -> bool:
        """
        Check if the text is an acronym.

        Args:
            text: Input string.

        Returns:
            True if text is an acronym, False otherwise.
        """
        return text.isupper() and len(text) > 1

    @staticmethod
    def has_multiple_spaces(text: str) -> bool:
        """
        Check if there are two or more consecutive spaces.

        Args:
            text: Input string.

        Returns:
            True if multiple consecutive spaces exist, False otherwise.
        """
        return bool(re.search(r"[ \t\f\v]{2,}", text))

    @staticmethod
    def clean_text_html(text: str) -> str:
        """
        Remove HTML tags from a string, replacing them with a space.

        Args:
            text: Input string.

        Returns:
            String without HTML tags.
        """
        return re.sub(r"<.*?>", " ", text)

    @staticmethod
    def clean_text_parentheses_punctuation_numbers(text: str) -> str:
        """
        Remove content inside parentheses, punctuation, and numbers from a string.

        Args:
            text: Input string.

        Returns:
            String without parentheses, punctuation, and numbers.
        """
        return re.sub(r"\(.*?\)|[^\w\s]|\d+", " ", text)

    @staticmethod
    def remove_text_urls(text: str) -> str:
        """
        Remove URLs from text.

        Args:
            text: Input string.

        Returns:
            String without URLs.
        """
        url_pattern = re.compile(r"((?:(?:https?|ftp):\/\/|www\.)[\w\S]+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[\w\S]*)?)")
        cleaned_text = url_pattern.sub("", text)
        cleaned_text = cleaned_text.replace("()", "")
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text

    @staticmethod
    def remove_text_emails(text: str) -> str:
        """
        Remove email addresses from text.

        Args:
            text: Input string.

        Returns:
            String without email addresses.
        """
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        cleaned_text = email_pattern.sub("", text)
        return cleaned_text

    @staticmethod
    def clean_text_sources(text: str) -> str:
        """
        Remove text after "Fontes:" or "Fonte:".

        Args:
            text: Input string.

        Returns:
            String without source references.
        """
        text = re.split("Fontes:|Fonte:", text)[0]
        return text

    @staticmethod
    def clean_text_extra_spaces(text: str) -> str:
        """
        Remove extra spaces from text.

        Args:
            text: Input string.

        Returns:
            String with normalized spaces.
        """
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Orchestrate the text cleaning process.

        Args:
            text: Input string.

        Returns:
            Fully sanitized text.
        """
        text = TextProcessor.clean_text_sources(text)
        text = TextProcessor.clean_text_html(text)
        text = TextProcessor.remove_text_emails(text)
        text = TextProcessor.remove_text_urls(text)
        text = TextProcessor.clean_text_parentheses_punctuation_numbers(text)
        text = TextProcessor.clean_text_extra_spaces(text)

        return text
