import os
from concurrent.futures import ThreadPoolExecutor
from data_validate.helpers.tools.locale.language_enum import LanguageEnum
from helpers.base.data_args import DataArgs


class Bootstrap:
    def __init__(self, data_args: DataArgs = None):
        """
        Initializes the Bootstrap class with default configurations.
        """
        self.config_dir = os.path.expanduser(".config")
        self.locale_file = os.path.join(self.config_dir, "store.locale")
        self.default_locale = LanguageEnum.DEFAULT_LANGUAGE.value

        # Run the argument parser
        self.run(data_args)

    def _check_and_set_locale(self, locale: str):
        """
        Checks and configures the `store.locale` file.

        Args:
            locale (str): The locale to set.
        """
        os.makedirs(self.config_dir, exist_ok=True)

        if locale:
            if locale in LanguageEnum.list_supported_languages():
                with open(self.locale_file, "w", encoding="utf-8") as f:
                    f.write(locale)
                return
            else:
                raise ValueError(f"Invalid locale: {locale}. Use '{LanguageEnum.DEFAULT_LANGUAGE.value}' or 'en_US'.")

        if os.path.exists(self.locale_file):
            with open(self.locale_file, "r", encoding="utf-8") as f:
                current_locale = f.read().strip()
                if current_locale in ["pt_BR", "en_US"]:
                    print(f"Locale configured: {current_locale}")
                    return
                else:
                    print(f"Invalid locale found: {current_locale}. Using default '{self.default_locale}'.")
        else:
            print(f"File 'store.locale' not found. Creating with default locale '{self.default_locale}'.")

        with open(self.locale_file, "w", encoding="utf-8") as f:
            f.write(self.default_locale)

    def run(self, args: DataArgs):
        """
        Executes tasks in parallel using the provided DataArgs object.

        Args:
            args (DataArgs): An instance of the DataArgs class.

        Raises:
            TypeError: If the provided argument is not an instance of DataArgs.
            ValueError: If the provided argument is None.
        """
        if not isinstance(args, DataArgs):
            raise TypeError("The 'args' parameter must be an instance of the DataArgs class.")
        if args is None:
            raise ValueError("The 'args' parameter cannot be None.")

        with ThreadPoolExecutor() as executor:
            tasks = [
                executor.submit(self._check_and_set_locale, args.data_file.locale),
            ]
            for task in tasks:
                task.result()  # Wait for each task to complete