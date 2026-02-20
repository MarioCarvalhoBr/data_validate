#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module for bootstrapping application configuration and environment settings.

This module defines the `Bootstrap` class, which handles initial setup tasks
such as locale configuration and environment validation before the main
application logic executes. It supports concurrent execution of setup tasks.
"""

import os
from concurrent.futures import ThreadPoolExecutor

from data_validate.helpers.base.data_args import DataArgs
from data_validate.helpers.tools.locale.language_enum import LanguageEnum


class Bootstrap:
    """
    Application bootstrap manager for initial configuration.

    Handles environment setup tasks, specifically locale management validation
    and persistence. It uses thread pooling to execute independent setup tasks
    concurrently during initialization.

    Attributes:
        config_dir (str): Path to the user's configuration directory.
        locale_file (str): Path to the locale configuration file.
        default_locale (str): Default locale to use if none is configured.
    """

    def __init__(self, data_args: DataArgs = None):
        """
        Initialize the Bootstrap class with default configurations.

        Sets up paths for configuration files and triggers the initial
        bootstrapping process via `run`.

        Args:
            data_args (DataArgs, optional): Arguments object containing runtime configuration.
        """
        self.config_dir = os.path.expanduser(".config")
        self.locale_file = os.path.join(self.config_dir, "store.locale")
        self.default_locale = LanguageEnum.DEFAULT_LANGUAGE.value

        # Run the argument parser
        self.run(data_args)

    def _check_and_set_locale(self, locale: str):
        """
        Check and configure the application locale.

        Validates the provided locale against supported languages. If valid,
        persists it to `store.locale`. If not provided, attempts to load
        from file or falls back to default.

        Args:
            locale (str): The locale code to set (e.g., 'pt_BR').

        Raises:
            ValueError: If the provided locale is not supported.
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
        Execute bootstrap tasks concurrently using thread pool.

        Runs independent initialization tasks (like locale setup) in parallel
        threads to speed up startup.

        Args:
            args (DataArgs): Parsed command-line arguments containing configuration.

        Raises:
            TypeError: If `args` is not an instance of `DataArgs`.
            ValueError: If `args` is None.
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
