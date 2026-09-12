#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from data_validate.helpers.tools.locale.language_enum import LanguageEnum

logger = logging.getLogger(__name__)


class LanguageManager:
    """
    A class to manage localization and translations for the application.

    BUG-004: the locale is resolved exclusively from the explicit `locale` constructor
    argument (or `LanguageEnum.DEFAULT_LANGUAGE.value` when it is `None` or unsupported).
    No file is read or written to resolve it — there is no more `.config/store.locale`
    persistence, so behaviour no longer depends on the process's current working
    directory or on leftover state from a previous run.
    """

    def __init__(self, locale: str | None = None, path_locale_dir: str | Path | None = None):
        """
        Initializes the LanguageManager with an explicit locale and locale directory.

        Args:
            locale (str | None): The locale code to use (e.g. 'pt_BR', 'en_US'). When
                `None` or not one of `LanguageEnum.list_supported_languages()`, falls
                back to `LanguageEnum.DEFAULT_LANGUAGE.value`. No file is read to
                resolve it.
            path_locale_dir (str | Path | None): Path to the directory containing
                locale files. Defaults to the package's `static/locales` directory.
        """
        self.path_locale_dir = path_locale_dir or Path(__file__).resolve().parents[3] / "static" / "locales"

        self.default_language = LanguageEnum.DEFAULT_LANGUAGE.value
        self.supported_languages = LanguageEnum.list_supported_languages()
        self.translations = {}

        self.current_language = locale if locale in self.supported_languages else self.default_language

        self._load_translations(self.current_language)

    def _load_translations(self, lang_code):
        """Loads translations from the JSON file for a given language."""
        filepath = os.path.join(self.path_locale_dir, lang_code, "messages.json")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            return True
        except FileNotFoundError:
            logger.warning("Translation file not found for language '%s': %s", lang_code, filepath)
        except json.JSONDecodeError:
            logger.error("Could not decode JSON for language '%s': %s", lang_code, filepath)
        except Exception as e:
            logger.error("Unexpected error loading language '%s': %s", lang_code, e)
        return False

    def set_language(self, lang_code):
        """
        Sets the current language and loads the corresponding translations.

        Args:
            lang_code (str): Language code to set.

        Returns:
            bool: True if the language was successfully set, False otherwise.
        """
        if lang_code in self.supported_languages:
            if self._load_translations(lang_code):
                self.current_language = lang_code
                return True
            else:
                logger.warning(
                    self.text(
                        "lang_load_error",
                        lang=lang_code,
                        default_lang=self.default_language,
                    )
                )
                if self._load_translations(self.default_language):
                    self.current_language = self.default_language
                    return False
                return None
        else:
            logger.warning(self.text("invalid_language", default_lang=self.default_language))
            if self.current_language != self.default_language:
                if self._load_translations(self.default_language):
                    self.current_language = self.default_language
            return False

    def text(self, key, **kwargs):
        """
        Retrieves the translated string for the given key in the current language.

        Args:
            key (str): The key of the string to translate.
            **kwargs: Keyword arguments for string formatting.

        Returns:
            str: The translated and formatted string, or a fallback string.
        """
        translation_object = self.translations.get(key)
        if isinstance(translation_object, dict):
            text = translation_object.get("message", f"<Message for '{key}' missing in '{self.current_language}'>")
        else:
            text = f"<'{key}' missing or invalid structure in '{self.current_language}'>"

        try:
            return text.format(**kwargs) if kwargs else text
        except KeyError as e:
            logger.warning("Formatting error for key '%s'. Missing placeholder: %s", key, e)
            return text
        except Exception as format_exc:
            logger.warning("Generic formatting error for key '%s': %s", key, format_exc)
            return text

    def get_supported_languages(self):
        """Returns the list of supported language codes."""
        return self.supported_languages

    def get_current_language(self):
        """Returns the currently selected language code."""
        return self.current_language

    def get_info(self):
        """
        Returns the current language and supported languages.
        """
        return {
            "current_language": self.current_language,
            "supported_languages": self.supported_languages,
        }

    def __str__(self):
        """
        Returns a string representation of the LanguageManager object.
        """
        return (
            f"LanguageManager(current_language={self.current_language}, supported_languages={self.supported_languages})"
        )
