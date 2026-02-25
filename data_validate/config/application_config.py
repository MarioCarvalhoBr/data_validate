"""
Configuration module for the Data Validate application.

This module defines the configuration settings, constants, and enumerations used throughout
the application. It includes the `NamesEnum` for verification names and the `ApplicationConfig` class
for managing application-wide settings such as limits, date formats, and report templates.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from datetime import datetime
from types import MappingProxyType

from data_validate.config.names_enum import NamesEnum
from data_validate.config.spreadsheet_info import SpreadsheetInfo
from data_validate.helpers.tools.locale.language_manager import LanguageManager


class ApplicationConfig:
    """
    Configuration class for Data Validate application.

    This class holds all the configuration constants and settings for the application.
    It includes settings for numeric precision, text limits, date/time formats,
    value representations, report generation settings, and file extensions.

    Attributes:
        language_manager (LanguageManager): Manager for handling localized text.
        spreadsheet_info (SpreadsheetInfo): Information about the spreadsheets used in the application.
        names_enum (NamesEnum): Enumeration of verification names used in the application.
    """

    # NUMBERS
    PRECISION_DECIMAL_PLACE_TRUNCATE = 3
    """int: The number of decimal places to truncate numbers to."""

    # DESCRIPTION LIMITS
    TITLE_OVER_N_CHARS = 40
    """int: Maximum number of characters allowed for titles."""
    SIMPLE_DESCRIPTIONS_OVER_N_CHARS = 150
    """int: Maximum number of characters allowed for simple description fields."""

    # DATE AND TIME
    CURRENT_YEAR = datetime.now().year
    """int: The current year."""
    DATE_NOW = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    """str: The current date and time formatted as 'dd/mm/yyyy HH:MM:SS'."""

    # VALUE AND LEGEND
    LABEL_DATA_UNAVAILABLE = "Dado indisponível"
    """str: Label used for unavailable data in reports."""
    VALUE_DATA_UNAVAILABLE = "DI"
    """str: Value used to represent unavailable data in datasets."""

    # REPORT
    REPORT_LIMIT_N_MESSAGES = 20
    """int: Maximum number of error messages to display per validation type in reports."""
    REPORT_OUTPUT_DEFAULT_HTML = "default.html"
    """str: Filename for the default HTML report output."""
    REPORT_OUTPUT_REPORT_HTML = "_report.html"
    """str: Suffix for generated HTML report files."""
    REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS = """
                                <!DOCTYPE html>
                                <html lang="pt-br">
                                <head>
                                    <meta charset="UTF-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                                    <title>Canoa Report</title>
                                </head>
                                <body>
                                    <h1 style="color:#FF0000;">Relat&oacute;rio gerando com o template padr&atilde;o de erro</h1>
                                    <p>Esse relat&oacute;rio foi gerado com o template padr&atilde;o de erro, pois o template personalizado n&atilde;o foi encontrado ou est&aacute; faltando vari&aacute;veis obrigat&oacute;rias.</p>
                                    <p>Entre em contato com o administrador do sistema para corrigir o problema.</p>
                                    <p>RELAT&Oacute;RIO</p>
                                    {{ name }}
                                    Relat&oacute;rio de Valida&ccedil;&atilde;o de Dados
                                    Informa&ccedil;&otilde;es: 
                                    {{ text_display_user }}
                                    {{ text_display_sector }}
                                    {{ text_display_protocol }}
                                    {{ text_display_date }}
                                    {{ text_display_version_and_os_info }}
                                    {{ text_display_file }}
                                    Resumo da validação
                                    N&uacute;mero de Erros: {{ num_errors }}
                                    N&uacute;mero de Avisos: {{ num_warnings }}
                                    N&uacute;mero de testes executados: {{ number_tests }}
                                    Testes n&atilde;o executados: {{ tests_not_executed }}
                                    Mostrar erros n&atilde;o executados: {{ display_tests_not_executed }}
                                    Erros
                                    {{ errors }}
                                    Avisos
                                    {{ warnings }}
                                </body>
                                </html>
                                """
    """str: Default HTML template for reports when the custom template cannot be loaded."""

    def __init__(self):
        """
        Initializes the ApplicationConfig instance.

        Sets up the LanguageManager for handling localized strings throughout the application.
        """
        self.language_manager: LanguageManager = LanguageManager()
        self.spreadsheet_info = SpreadsheetInfo()
        self.names_enum = NamesEnum

    def get_verify_names(self):
        """
        Retrieves a dictionary of verification names with localized text.

        The method iterates over `NamesEnum` members and retrieves their localized
        string representation using the `LanguageManager`. For specific verifications
        like `TITLES_N` and `SIMP_DESC_N`, it formats the message with dynamic values
        from configuration constants.

        Returns:
            MappingProxyType: A read-only dictionary mapping verification keys (from `NamesEnum`)
            to their localized text descriptions.
        """
        keys = [element for element in NamesEnum]
        values = [
            (
                self.language_manager.text(
                    str(element.value),
                    value=(
                        self.TITLE_OVER_N_CHARS
                        if element == NamesEnum.TITLES_N
                        else (self.SIMPLE_DESCRIPTIONS_OVER_N_CHARS if element == NamesEnum.SIMP_DESC_N else None)
                    ),
                )
                if element in (NamesEnum.TITLES_N, NamesEnum.SIMP_DESC_N)
                else self.language_manager.text(str(element.value))
            )
            for element in keys
        ]
        return MappingProxyType(dict(zip([e.value for e in keys], values)))
