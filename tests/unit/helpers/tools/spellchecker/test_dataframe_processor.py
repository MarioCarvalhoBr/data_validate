"""
Unit tests for dataframe_processor.py module.

This module tests the DataFrameProcessor class's `find_quality_findings` method: scanning
text columns for quality signals (multiple spaces, spelling errors) and emitting structured
`(row_index, column, kind, payload)` findings (ARC-017 Phase 3 Port 8). `validate_columns` and
`process_dataframe` (the legacy string-formatting path superseded by `find_quality_findings` /
`rules/spell.py`) were removed as dead code; their tests were removed with them.
"""

#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd
import pytest

from data_validate.helpers.tools.spellchecker.dataframe_processor import DataFrameProcessor
from data_validate.helpers.tools.spellchecker.dictionary_manager import DictionaryManager
from data_validate.helpers.tools.spellchecker.spellchecker_controller import SpellCheckerController


class TestDataFrameProcessorFindQualityFindings:
    """Test suite for `DataFrameProcessor.find_quality_findings`."""

    @pytest.fixture
    def mock_spell_checker(self, mocker):
        """Create a mock SpellCheckerController for testing."""
        mock_controller = mocker.MagicMock(spec=SpellCheckerController)
        mock_controller.evaluate_text_quality.return_value = (False, [])
        mock_controller.build_quality_findings.return_value = []
        return mock_controller

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "text_column": ["Hello World", "Test Text", "Another Test"],
                "number_column": [1, 2, 3],
                "empty_column": ["", None, "Valid Text"],
            }
        )

    @pytest.fixture
    def dataframe_processor(self, mock_spell_checker) -> DataFrameProcessor:
        """Create DataFrameProcessor instance for testing."""
        return DataFrameProcessor(mock_spell_checker)

    def test_find_quality_findings_skips_empty_cells(self, dataframe_processor, mock_spell_checker) -> None:
        """Only the non-empty cell is sent to the spell checker."""
        df = pd.DataFrame({"empty_column": ["", None, "Valid Text"]})

        dataframe_processor.find_quality_findings(df, ["empty_column"])

        assert mock_spell_checker.evaluate_text_quality.call_count == 1
        mock_spell_checker.evaluate_text_quality.assert_called_with("Valid Text")

    def test_find_quality_findings_evaluates_each_unique_text_once(
        self, dataframe_processor, mock_spell_checker
    ) -> None:
        """Repeated cell values (PERF-006) are only sent to the spell checker once each."""
        df = pd.DataFrame({"column": ["Repeated text", "Repeated text", "Other text", "Repeated text"]})

        dataframe_processor.find_quality_findings(df, ["column"])

        assert mock_spell_checker.evaluate_text_quality.call_count == 2
        mock_spell_checker.evaluate_text_quality.assert_any_call("Repeated text")
        mock_spell_checker.evaluate_text_quality.assert_any_call("Other text")
        # `build_quality_findings` is still called once per row, so row-specific findings are kept.
        assert mock_spell_checker.build_quality_findings.call_count == 4

    def test_find_quality_findings_skips_columns_with_no_non_empty_cells(
        self, dataframe_processor, mock_spell_checker
    ) -> None:
        """A column that is entirely empty/None never reaches the spell checker."""
        df = pd.DataFrame({"column1": ["", None, ""], "column2": [None, "", None]})

        findings = dataframe_processor.find_quality_findings(df, ["column1", "column2"])

        assert findings == []
        mock_spell_checker.evaluate_text_quality.assert_not_called()
        mock_spell_checker.build_quality_findings.assert_not_called()

    def test_find_quality_findings_coerces_non_string_values_to_str(
        self, dataframe_processor, mock_spell_checker
    ) -> None:
        """Numeric/boolean cell values are converted to text before evaluation."""
        df = pd.DataFrame({"column": [123, "Text", 456.78]})

        dataframe_processor.find_quality_findings(df, ["column"])

        assert mock_spell_checker.evaluate_text_quality.call_count == 3
        mock_spell_checker.evaluate_text_quality.assert_any_call("123")
        mock_spell_checker.evaluate_text_quality.assert_any_call("Text")
        mock_spell_checker.evaluate_text_quality.assert_any_call("456.78")

    def test_find_quality_findings_collects_findings_from_every_row(
        self, dataframe_processor, mock_spell_checker
    ) -> None:
        """Findings returned by `build_quality_findings` for every row are concatenated in order."""
        df = pd.DataFrame({"column": ["a", "b"]})
        mock_spell_checker.build_quality_findings.side_effect = [
            [(0, "column", "multiple_spaces", None)],
            [(1, "column", "misspelled_words", ["b"])],
        ]

        findings = dataframe_processor.find_quality_findings(df, ["column"])

        assert findings == [
            (0, "column", "multiple_spaces", None),
            (1, "column", "misspelled_words", ["b"]),
        ]


class TestDataFrameProcessorFindQualityFindingsIntegration:
    """End-to-end (real `SpellCheckerController`, no mocks) findings-shape tests."""

    def test_find_quality_findings_reports_multiple_spaces_and_misspelled_words(self, mocker) -> None:
        """A row with both signals produces both findings, multiple-spaces first."""

        class AlwaysWrongDict:
            """Fake enchant Dict: every word is considered misspelled."""

            def check(self, word: str) -> bool:
                return False

        mock_dictionary_manager = mocker.MagicMock(spec=DictionaryManager)
        controller = SpellCheckerController(mock_dictionary_manager)
        controller.dictionary = AlwaysWrongDict()
        processor = DataFrameProcessor(controller)

        df = pd.DataFrame({"column": ["Hello  World"]})

        findings = processor.find_quality_findings(df, ["column"])

        assert findings == [
            (0, "column", "multiple_spaces", None),
            (0, "column", "misspelled_words", ["Hello", "World"]),
        ]

    def test_find_quality_findings_maps_cached_result_back_to_every_row(self, mocker) -> None:
        """Each row sharing a repeated text gets its own row index, in order (PERF-006)."""

        class AlwaysCorrectDict:
            """Fake enchant Dict: every word is considered correctly spelled."""

            def check(self, word: str) -> bool:
                return True

        mock_dictionary_manager = mocker.MagicMock(spec=DictionaryManager)
        controller = SpellCheckerController(mock_dictionary_manager)
        controller.dictionary = AlwaysCorrectDict()
        processor = DataFrameProcessor(controller)

        # Row 0 and row 2 share the same (multi-space) text; row 1 differs.
        df = pd.DataFrame({"column": ["Hello  World", "Other text", "Hello  World"]})

        findings = processor.find_quality_findings(df, ["column"])

        assert findings == [
            (0, "column", "multiple_spaces", None),
            (2, "column", "multiple_spaces", None),
        ]
