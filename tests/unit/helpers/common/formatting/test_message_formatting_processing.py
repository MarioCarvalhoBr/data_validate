#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.


import pytest

from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing


class TestErrorFormatting:
    """Test cases for error formatting functions."""

    def test_format_errors_and_warnings_success(self):
        """Test successful formatting of errors and warnings."""
        file_name = "test_file.csv"
        missing_columns = ["col1", "col2"]
        extra_columns = ["extra1", "extra2"]

        errors, warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            file_name, missing_columns, extra_columns
        )

        expected_errors = [
            "test_file.csv: Coluna 'col1' esperada mas não foi encontrada.",
            "test_file.csv: Coluna 'col2' esperada mas não foi encontrada.",
        ]
        expected_warnings = [
            "test_file.csv: Coluna 'extra1' será ignorada pois não está na especificação.",
            "test_file.csv: Coluna 'extra2' será ignorada pois não está na especificação.",
        ]

        assert errors == expected_errors
        assert warnings == expected_warnings

    def test_format_errors_and_warnings_empty_lists(self):
        """Test formatting with empty lists."""
        file_name = "test_file.csv"
        missing_columns = []
        extra_columns = []

        errors, warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            file_name, missing_columns, extra_columns
        )

        assert errors == []
        assert warnings == []

    def test_format_errors_and_warnings_mixed_content(self):
        """Test formatting with mixed content - some missing, some extra."""
        file_name = "data.xlsx"
        missing_columns = ["required_col"]
        extra_columns = []

        errors, warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            file_name, missing_columns, extra_columns
        )

        expected_errors = ["data.xlsx: Coluna 'required_col' esperada mas não foi encontrada."]
        expected_warnings = []

        assert errors == expected_errors
        assert warnings == expected_warnings

    def test_format_errors_and_warnings_special_characters(self):
        """Test formatting with special characters in file name and column names."""
        file_name = "arquivo_com_acentos_é_ção.csv"
        missing_columns = ["coluna_com_ção"]
        extra_columns = ["coluna_extra_é"]

        errors, warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            file_name, missing_columns, extra_columns
        )

        expected_errors = ["arquivo_com_acentos_é_ção.csv: Coluna 'coluna_com_ção' esperada mas não foi encontrada."]
        expected_warnings = [
            "arquivo_com_acentos_é_ção.csv: Coluna 'coluna_extra_é' será ignorada pois não está na especificação."
        ]

        assert errors == expected_errors
        assert warnings == expected_warnings

    def test_format_errors_and_warnings_unexpected_error_propagates(self):
        """SEC-004: a genuine failure propagates instead of being downgraded to a
        data-quality message — there is no plausible failure mode in this pure
        string-formatting code worth reporting as one more "column" error."""

        class ExceptionList:
            def __init__(self, items):
                self.items = items

            def __iter__(self):
                raise RuntimeError("Simulated iteration error")

        file_name = "test_file.csv"
        missing_columns = ExceptionList(["col1"])
        extra_columns = ["extra1"]

        with pytest.raises(RuntimeError, match="Simulated iteration error"):
            MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
                file_name, missing_columns, extra_columns
            )
