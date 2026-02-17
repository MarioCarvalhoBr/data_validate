import json
import os
from pathlib import Path

from data_validate.helpers.tools.locale.language_enum import LanguageEnum


class LanguageManager:
    """
    A class to manage localization and translations for the application.
    """

    def __init__(self, path_locale_dir=None):
        """
        Initializes the LanguageManager with the given locale directory and default language.

        Args:
            path_locale_dir (str): Path to the directory containing locale files.
        """
        self.path_locale_dir = path_locale_dir or Path(__file__).resolve().parents[3] / "static" / "locales"

        self.default_language = LanguageEnum.DEFAULT_LANGUAGE.value
        self.current_language = None
        self.translations = {}

        # Pipiline to configure the language
        self._congifure_language()
        self.supported_languages = LanguageEnum.list_supported_languages()
        self._load_translations(self.current_language)

    def _congifure_language(self):
        store_locale_path = Path(__file__).resolve().parents[4] / ".config" / "store.locale"

        # Check if the store.locale file exists
        if not store_locale_path.exists():
            print(f"store.locale not found. Falling back to default language '{self.default_language}'.")
            self.current_language = self.default_language

            # Create the store.locale file with the default language
            store_locale_path.parent.mkdir(parents=True, exist_ok=True)
            with store_locale_path.open("w", encoding="utf-8") as f:
                f.write(self.default_language)
            return

        with store_locale_path.open("r", encoding="utf-8") as f:
            self.current_language = f.read().strip()
            if self.current_language not in LanguageEnum.list_supported_languages():
                print(f"Invalid current language '{self.current_language}' in store.locale. Falling back to '{LanguageEnum.DEFAULT_LANGUAGE.value}'.")
                self.current_language = self.default_language

    def _load_translations(self, lang_code):
        """Loads translations from the JSON file for a given language."""
        filepath = os.path.join(self.path_locale_dir, lang_code, "messages.json")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            return True
        except FileNotFoundError:
            print(f"WARNING: Translation file not found for language '{lang_code}': {filepath}")
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON for language '{lang_code}': {filepath}")
        except Exception as e:
            print(f"ERROR: Unexpected error loading language '{lang_code}': {e}")
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
                print(
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
            print(self.text("invalid_language", default_lang=self.default_language))
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
            print(f"Warning: Formatting error for key '{key}'. Missing placeholder: {e}")
            return text
        except Exception as format_exc:
            print(f"Warning: Generic formatting error for key '{key}': {format_exc}")
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
        return f"LanguageManager(current_language={self.current_language}, supported_languages={self.supported_languages})"
