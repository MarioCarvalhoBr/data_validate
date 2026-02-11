"""
Configuration module for the Data Validate application.

This module defines the configuration settings, constants, and enumerations used throughout
the application. It includes the `NamesEnum` for verification names and the `Config` class
for managing application-wide settings such as limits, date formats, and report templates.
"""

from datetime import datetime
from enum import Enum
from types import MappingProxyType

from data_validate.helpers.tools.locale.language_manager import LanguageManager


class NamesEnum(Enum):
    """
    Enumeration for verification names used in validation reports.

    Each member represents a specific type of verification or validation rule applied
    to the data. These keys are used to look up localized messages and aggregate errors.
    """

    FS = "verification_name_file_structure"
    FC = "verification_name_file_cleaning"
    IR = "verification_name_indicator_relations"
    TH = "verification_name_tree_hierarchy"
    IL = "verification_name_indicator_levels"
    CO_UN = "verification_name_code_uniqueness"
    HTML_DESC = "verification_name_html_codes_in_descriptions"
    SPELL = "verification_name_spelling"
    UT = "verification_name_unique_titles"
    SC = "verification_name_sequential_codes"
    EF = "verification_name_empty_fields"
    INP = "verification_name_indicator_name_pattern"
    TITLES_N = "verification_name_titles_over_n_chars"
    SIMP_DESC_N = "verification_name_simple_descriptions_over_n_chars"
    MAND_PUNC_DESC = "verification_name_mandatory_and_prohibited_punctuation_in_descriptions"
    MAND_PUNC_SCEN = "verification_name_mandatory_and_prohibited_punctuation_in_scenarios"
    MAND_PUNC_TEMP = "verification_name_mandatory_and_prohibited_punctuation_in_temporal_reference"
    UVR_SCEN = "verification_name_unique_value_relations_in_scenarios"
    UVR_TEMP = "verification_name_unique_value_relations_in_temporal_reference"
    VAL_COMB = "verification_name_value_combination_relations"
    UNAV_INV = "verification_name_unavailable_and_invalid_values"
    LB_DESC = "verification_name_line_break_in_description"
    LB_SCEN = "verification_name_line_break_in_scenarios"
    LB_TEMP = "verification_name_line_break_in_temporal_reference"
    YEARS_TEMP = "verification_name_years_in_temporal_reference"
    LEG_RANGE = "verification_name_legend_data_range"
    LEG_OVER = "verification_name_legend_value_overlap"
    LEG_REL = "verification_name_legend_relations"
    SUM_PROP = "verification_name_sum_properties_in_influencing_factors"
    REP_IND_PROP = "verification_name_repeated_indicators_in_proportionalities"
    IR_PROP = "verification_name_indicator_relations_in_proportionalities"
    IND_VAL_PROP = "verification_name_indicators_in_values_and_proportionalities"
    LEAF_NO_DATA = "verification_name_leaf_indicators_without_associated_data"
    CHILD_LVL = "verification_name_child_indicator_levels"


class Config:
    """
    Configuration class for Data Validate application.

    This class holds all the configuration constants and settings for the application.
    It includes settings for numeric precision, text limits, date/time formats,
    value representations, report generation settings, and file extensions.

    Attributes:
        lm (LanguageManager): Manager for handling localized text.
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

    # Expected and optional files with their respective extensions
    # Improve this logic in the future to allow more flexibility
    EXPECTED_FILES = {
        "descricao": [".csv", ".xlsx"],
        "composicao": [".csv", ".xlsx"],
        "valores": [".csv", ".xlsx"],
        "referencia_temporal": [".csv", ".xlsx"],
    }
    """dict: Dictionary of expected file identifiers and their allowed extensions."""

    OPTIONAL_FILES = {
        "proporcionalidades": [".csv", ".xlsx"],
        "cenarios": [".csv", ".xlsx"],
        "legenda": [".csv", ".xlsx"],
        "dicionario": [".csv", ".xlsx"],
    }
    """dict: Dictionary of optional file identifiers and their allowed extensions."""

    def __init__(self):
        """
        Initializes the Config instance.

        Sets up the LanguageManager for handling localized strings throughout the application.
        """
        self.lm: LanguageManager = LanguageManager()

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
                self.lm.text(
                    str(element.value),
                    value=(
                        self.TITLE_OVER_N_CHARS
                        if element == NamesEnum.TITLES_N
                        else (self.SIMPLE_DESCRIPTIONS_OVER_N_CHARS if element == NamesEnum.SIMP_DESC_N else None)
                    ),
                )
                if element in (NamesEnum.TITLES_N, NamesEnum.SIMP_DESC_N)
                else self.lm.text(str(element.value))
            )
            for element in keys
        ]
        return MappingProxyType(dict(zip([e.value for e in keys], values)))
