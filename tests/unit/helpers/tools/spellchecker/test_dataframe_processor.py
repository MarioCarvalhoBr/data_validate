"""
Unit tests for dataframe_processor.py module.

This module tests the DataFrameProcessor class functionality including
DataFrame validation, column processing, and spell checking integration.
"""

import pandas as pd
import pytest

from data_validate.helpers.tools.spellchecker.dataframe_processor import DataFrameProcessor
from data_validate.helpers.tools.spellchecker.spellchecker_controller import SpellCheckerController


class TestDataFrameProcessor:
    """Test suite for DataFrameProcessor core functionality."""

    @pytest.fixture
    def mock_spell_checker(self, mocker):
        """Create a mock SpellCheckerController for testing."""
        mock_controller = mocker.MagicMock(spec=SpellCheckerController)
        mock_controller.check_text_quality.return_value = []
        return mock_controller

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'text_column': ['Hello World', 'Test Text', 'Another Test'],
            'number_column': [1, 2, 3],
            'empty_column': ['', None, 'Valid Text']
        })

    @pytest.fixture
    def dataframe_processor(self, mock_spell_checker) -> DataFrameProcessor:
        """Create DataFrameProcessor instance for testing."""
        return DataFrameProcessor(mock_spell_checker)

    def test_validate_columns_all_exist(self, dataframe_processor, sample_dataframe) -> None:
        """Test column validation when all columns exist."""
        columns = ['text_column', 'number_column']
        valid_columns, warnings = dataframe_processor.validate_columns(
            sample_dataframe, columns, "test_file.xlsx"
        )
        
        assert set(valid_columns) == {'text_column', 'number_column'}
        assert warnings == []

    def test_validate_columns_some_missing(self, dataframe_processor, sample_dataframe) -> None:
        """Test column validation when some columns are missing."""
        columns = ['text_column', 'missing_column', 'another_missing']
        valid_columns, warnings = dataframe_processor.validate_columns(
            sample_dataframe, columns, "test_file.xlsx"
        )
        
        assert valid_columns == ['text_column']
        assert len(warnings) == 1
        assert "missing_column" in warnings[0]
        assert "another_missing" in warnings[0]
        assert "test_file.xlsx" in warnings[0]

    def test_validate_columns_all_missing(self, dataframe_processor, sample_dataframe) -> None:
        """Test column validation when all columns are missing."""
        columns = ['missing1', 'missing2']
        valid_columns, warnings = dataframe_processor.validate_columns(
            sample_dataframe, columns, "test_file.xlsx"
        )
        
        assert valid_columns == []
        assert len(warnings) == 1
        assert "missing1" in warnings[0]
        assert "missing2" in warnings[0]

    def test_validate_columns_empty_list(self, dataframe_processor, sample_dataframe) -> None:
        """Test column validation with empty column list."""
        columns = []
        valid_columns, warnings = dataframe_processor.validate_columns(
            sample_dataframe, columns, "test_file.xlsx"
        )
        
        assert valid_columns == []
        assert warnings == []

    def test_process_dataframe_with_valid_data(self, dataframe_processor, sample_dataframe, mock_spell_checker) -> None:
        """Test DataFrame processing with valid data."""
        columns = ['text_column']
        mock_spell_checker.check_text_quality.return_value = ['Warning 1', 'Warning 2']
        
        warnings = dataframe_processor.process_dataframe(sample_dataframe, columns, "Sheet1")
        
        assert len(warnings) == 6  # 3 rows * 2 warnings each
        assert mock_spell_checker.check_text_quality.call_count == 3
        mock_spell_checker.check_text_quality.assert_any_call('Hello World', 'text_column', 0, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Test Text', 'text_column', 1, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Another Test', 'text_column', 2, 'Sheet1')

    def test_process_dataframe_with_empty_cells(self, dataframe_processor, sample_dataframe, mock_spell_checker) -> None:
        """Test DataFrame processing with empty cells."""
        columns = ['empty_column']
        mock_spell_checker.check_text_quality.return_value = []
        
        warnings = dataframe_processor.process_dataframe(sample_dataframe, columns, "Sheet1")
        
        # Should only process the non-empty cell (index 2)
        assert mock_spell_checker.check_text_quality.call_count == 1
        mock_spell_checker.check_text_quality.assert_called_with('Valid Text', 'empty_column', 2, 'Sheet1')

    def test_process_dataframe_multiple_columns(self, dataframe_processor, sample_dataframe, mock_spell_checker) -> None:
        """Test DataFrame processing with multiple columns."""
        columns = ['text_column', 'empty_column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(sample_dataframe, columns, "Sheet1")
        
        # text_column: 3 calls, empty_column: 1 call (only non-empty cell)
        assert mock_spell_checker.check_text_quality.call_count == 4
        assert len(warnings) == 4

    def test_process_dataframe_empty_dataframe(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with empty DataFrame."""
        empty_df = pd.DataFrame({'column': []})
        columns = ['column']
        
        warnings = dataframe_processor.process_dataframe(empty_df, columns, "Sheet1")
        
        assert warnings == []
        mock_spell_checker.check_text_quality.assert_not_called()

    def test_process_dataframe_all_empty_cells(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing when all cells are empty."""
        df = pd.DataFrame({
            'column1': ['', None, ''],
            'column2': [None, '', None]
        })
        columns = ['column1', 'column2']
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        assert warnings == []
        mock_spell_checker.check_text_quality.assert_not_called()

    def test_process_dataframe_none_values(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with None values."""
        df = pd.DataFrame({
            'column': [None, 'Valid Text', None]
        })
        columns = ['column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        # Should only process the non-None cell
        assert mock_spell_checker.check_text_quality.call_count == 1
        mock_spell_checker.check_text_quality.assert_called_with('Valid Text', 'column', 1, 'Sheet1')
        assert len(warnings) == 1

    def test_process_dataframe_numeric_values(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with numeric values."""
        df = pd.DataFrame({
            'column': [123, 'Text', 456.78]
        })
        columns = ['column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        # Should process all values (converted to strings)
        assert mock_spell_checker.check_text_quality.call_count == 3
        mock_spell_checker.check_text_quality.assert_any_call('123', 'column', 0, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Text', 'column', 1, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('456.78', 'column', 2, 'Sheet1')
        assert len(warnings) == 3


class TestDataFrameProcessorEdgeCases:
    """Edge cases and boundary conditions for DataFrameProcessor."""

    @pytest.fixture
    def mock_spell_checker(self, mocker):
        """Create a mock SpellCheckerController for testing."""
        mock_controller = mocker.MagicMock(spec=SpellCheckerController)
        mock_controller.check_text_quality.return_value = []
        return mock_controller

    @pytest.fixture
    def dataframe_processor(self, mock_spell_checker) -> DataFrameProcessor:
        """Create DataFrameProcessor instance for testing."""
        return DataFrameProcessor(mock_spell_checker)

    def test_validate_columns_case_sensitivity(self, dataframe_processor) -> None:
        """Test column validation with case sensitivity."""
        df = pd.DataFrame({'Column1': [1, 2], 'column2': [3, 4]})
        columns = ['column1', 'Column2']  # Different case
        
        valid_columns, warnings = dataframe_processor.validate_columns(df, columns, "test.xlsx")
        
        assert valid_columns == []  # No matches due to case sensitivity
        assert len(warnings) == 1

    def test_validate_columns_duplicate_columns(self, dataframe_processor) -> None:
        """Test column validation with duplicate column names."""
        df = pd.DataFrame({'column': [1, 2]})
        columns = ['column', 'column']  # Duplicate column names
        
        valid_columns, warnings = dataframe_processor.validate_columns(df, columns, "test.xlsx")
        
        assert valid_columns == ['column']  # Should deduplicate
        assert warnings == []

    def test_process_dataframe_large_dataframe(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with large DataFrame."""
        # Create a large DataFrame
        large_df = pd.DataFrame({
            'column': [f'Text {i}' for i in range(1000)]
        })
        columns = ['column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(large_df, columns, "Sheet1")
        
        assert mock_spell_checker.check_text_quality.call_count == 1000
        assert len(warnings) == 1000

    def test_process_dataframe_special_characters(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with special characters."""
        df = pd.DataFrame({
            'column': ['Text with émojis 🎉', 'Special chars: !@#$%', 'Unicode: ñáéíóú']
        })
        columns = ['column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        assert mock_spell_checker.check_text_quality.call_count == 3
        mock_spell_checker.check_text_quality.assert_any_call('Text with émojis 🎉', 'column', 0, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Special chars: !@#$%', 'column', 1, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Unicode: ñáéíóú', 'column', 2, 'Sheet1')

    def test_process_dataframe_boolean_values(self, dataframe_processor, mock_spell_checker) -> None:
        """Test DataFrame processing with boolean values."""
        df = pd.DataFrame({
            'column': [True, False, 'Text']
        })
        columns = ['column']
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        assert mock_spell_checker.check_text_quality.call_count == 3
        mock_spell_checker.check_text_quality.assert_any_call('True', 'column', 0, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('False', 'column', 1, 'Sheet1')
        mock_spell_checker.check_text_quality.assert_any_call('Text', 'column', 2, 'Sheet1')


class TestDataFrameProcessorIntegration:
    """Integration tests for DataFrameProcessor."""

    @pytest.fixture
    def mock_spell_checker(self, mocker):
        """Create a mock SpellCheckerController for testing."""
        mock_controller = mocker.MagicMock(spec=SpellCheckerController)
        return mock_controller

    @pytest.fixture
    def dataframe_processor(self, mock_spell_checker) -> DataFrameProcessor:
        """Create DataFrameProcessor instance for testing."""
        return DataFrameProcessor(mock_spell_checker)

    def test_validate_and_process_workflow(self, dataframe_processor, mock_spell_checker) -> None:
        """Test complete workflow of validate_columns and process_dataframe."""
        df = pd.DataFrame({
            'valid_column': ['Text 1', 'Text 2'],
            'another_valid': ['Text 3', 'Text 4']
        })
        columns = ['valid_column', 'invalid_column', 'another_valid']
        
        # Step 1: Validate columns
        valid_columns, warnings = dataframe_processor.validate_columns(df, columns, "test.xlsx")
        
        assert set(valid_columns) == {'another_valid', 'valid_column'}
        assert len(warnings) == 1
        assert 'invalid_column' in warnings[0]
        
        # Step 2: Process DataFrame
        mock_spell_checker.check_text_quality.return_value = ['Warning']
        processing_warnings = dataframe_processor.process_dataframe(df, valid_columns, "Sheet1")
        
        assert mock_spell_checker.check_text_quality.call_count == 4  # 2 columns * 2 rows
        assert len(processing_warnings) == 4

    def test_spell_checker_integration(self, dataframe_processor, mock_spell_checker) -> None:
        """Test integration with SpellCheckerController."""
        df = pd.DataFrame({
            'text': ['Hello World', 'Test Text']
        })
        columns = ['text']
        
        # Mock different responses for different texts
        def mock_check_text_quality(text, column, row_index, sheet_name):
            if 'Hello' in text:
                return ['Spelling error in Hello']
            return []
        
        mock_spell_checker.check_text_quality.side_effect = mock_check_text_quality
        
        warnings = dataframe_processor.process_dataframe(df, columns, "Sheet1")
        
        assert len(warnings) == 1
        assert 'Spelling error in Hello' in warnings[0]
        assert mock_spell_checker.check_text_quality.call_count == 2

    def test_error_handling_in_spell_checker(self, dataframe_processor, mock_spell_checker) -> None:
        """Test error handling when spell checker raises exceptions."""
        df = pd.DataFrame({
            'text': ['Test Text']
        })
        columns = ['text']
        
        # Mock spell checker to raise exception
        mock_spell_checker.check_text_quality.side_effect = Exception("Spell checker error")
        
        # The method should handle the exception gracefully
        # (The actual implementation doesn't have try-catch, so this would raise)
        # This test documents the current behavior
        with pytest.raises(Exception, match="Spell checker error"):
            dataframe_processor.process_dataframe(df, columns, "Sheet1")
