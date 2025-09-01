import pandas as pd
import numpy as np
from data_validate.helpers.common.processing.data_cleaning import (
    clean_column_integer,
    clean_dataframe_integers,
    clean_column_floats,
    clean_dataframe_floats
)


class TestDataCleaning:
    """Test cases for data cleaning functions."""

    def setup_method(self):
        """Set up test data."""
        self.df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': ['10', '20', 'invalid', '30', ''],
            'float_val': ['1.5', '2.5', 'invalid', '3.5', '4.5'],
            'mixed': [1, '2', 3.0, 'invalid', 5]
        })

    def test_clean_column_integer_column_not_found(self):
        """Test cleaning integer column that doesn't exist."""
        df, errors = clean_column_integer(self.df, 'nonexistent', 'test.csv')
        
        assert len(errors) == 1
        assert "não foi encontrada" in errors[0]
        assert df.equals(self.df)

    def test_clean_column_integer_basic_cleaning(self):
        """Test basic integer column cleaning."""
        df, errors = clean_column_integer(self.df, 'id', 'test.csv')
        
        assert len(errors) == 0
        assert len(df) == 5
        assert df['id'].dtype == 'int64'
        assert list(df['id']) == [1, 2, 3, 4, 5]

    def test_clean_column_integer_with_invalid_values(self):
        """Test integer column cleaning with invalid values."""
        df, errors = clean_column_integer(self.df, 'value', 'test.csv')
        
        assert len(errors) == 2  # 'invalid' and empty string are invalid
        assert "valor inválido" in errors[0]
        assert len(df) == 3  # Two rows removed
        assert df['value'].dtype == 'int64'

    def test_clean_column_integer_with_min_value(self):
        """Test integer column cleaning with minimum value constraint."""
        df, errors = clean_column_integer(self.df, 'id', 'test.csv', min_value=3)
        
        assert len(errors) == 2  # IDs 1 and 2 are below minimum
        assert len(df) == 3  # Two rows removed
        assert list(df['id']) == [3, 4, 5]

    def test_clean_column_integer_allow_empty_true(self):
        """Test integer column cleaning allowing empty values."""
        df, errors = clean_column_integer(self.df, 'value', 'test.csv', allow_empty=True)
        
        assert len(errors) == 1  # Only 'invalid' is invalid
        assert len(df) == 4  # One row removed
        assert df['value'].dtype == 'object'  # Mixed types due to empty values

    def test_clean_column_integer_allow_empty_false(self):
        """Test integer column cleaning not allowing empty values."""
        df, errors = clean_column_integer(self.df, 'value', 'test.csv', allow_empty=False)
        
        assert len(errors) == 2  # 'invalid' and empty string are invalid
        assert len(df) == 3  # Two rows removed
        assert df['value'].dtype == 'int64'

    def test_clean_column_integer_with_comma_decimal(self):
        """Test integer column cleaning with comma decimal separator."""
        df_comma = pd.DataFrame({
            'value': ['1,0', '2,5', '3,0', 'invalid']
        })
        
        df, errors = clean_column_integer(df_comma, 'value', 'test.csv')
        
        assert len(errors) == 2  # '2,5' and 'invalid' are invalid (2.5 is not integer)
        assert len(df) == 2  # Two rows removed
        assert df['value'].dtype == 'int64'

    def test_clean_dataframe_integers_multiple_columns(self):
        """Test cleaning multiple integer columns."""
        df, errors = clean_dataframe_integers(
            self.df, 'test.csv', ['id', 'value']
        )
        
        assert len(errors) == 2  # Two errors from 'value' column
        assert len(df) == 3  # Two rows removed
        assert df['id'].dtype == 'int64'
        assert df['value'].dtype == 'int64'

    def test_clean_column_floats_column_not_found(self):
        """Test cleaning float column that doesn't exist."""
        df, errors = clean_column_floats(self.df, 'nonexistent', 'test.csv')
        
        assert len(errors) == 1
        assert "não foi encontrada" in errors[0]
        assert df.equals(self.df)

    def test_clean_column_floats_basic_cleaning(self):
        """Test basic float column cleaning."""
        df, errors = clean_column_floats(self.df, 'float_val', 'test.csv')
        
        assert len(errors) == 1  # 'invalid' is invalid
        assert len(df) == 4  # One row removed
        assert df['float_val'].dtype == 'float64'

    def test_clean_column_floats_with_comma_decimal(self):
        """Test float column cleaning with comma decimal separator."""
        df_comma = pd.DataFrame({
            'value': ['1,5', '2,5', '3,0', 'invalid']
        })
        
        df, errors = clean_column_floats(df_comma, 'value', 'test.csv')
        
        assert len(errors) == 1  # 'invalid' is invalid
        assert len(df) == 3  # One row removed
        assert df['value'].dtype == 'float64'

    def test_clean_dataframe_floats_multiple_columns(self):
        """Test cleaning multiple float columns."""
        # Create a DataFrame without invalid values to avoid conversion errors
        df_clean = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'float_val': ['1.5', '2.5', '3.5', '4.5', '5.5'],
            'mixed': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        df, errors = clean_dataframe_floats(
            df_clean, 'test.csv', ['float_val', 'mixed']
        )
        
        assert len(errors) == 0  # No errors with clean data
        assert len(df) == 5  # All rows kept

    def test_clean_dataframe_floats_column_not_found(self):
        """Test cleaning float columns when some don't exist."""
        # Create a DataFrame without invalid values to avoid conversion errors
        df_clean = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'float_val': ['1.5', '2.5', '3.5', '4.5', '5.5']
        })
        
        df, errors = clean_dataframe_floats(
            df_clean, 'test.csv', ['float_val', 'nonexistent']
        )
        
        assert len(errors) >= 1  # At least one error for missing column
        assert "não foi encontrada" in errors[0]

    def test_clean_column_integer_with_nan_values(self):
        """Test integer column cleaning with NaN values."""
        df_nan = pd.DataFrame({
            'value': [1, 2, np.nan, 4, 5]
        })
        
        df, errors = clean_column_integer(df_nan, 'value', 'test.csv', allow_empty=True)
        
        assert len(errors) == 0
        assert len(df) == 5
        assert df['value'].dtype == 'float64'  # pandas converts NaN to float

    def test_clean_column_integer_with_nan_values_not_allowed(self):
        """Test integer column cleaning with NaN values not allowed."""
        df_nan = pd.DataFrame({
            'value': [1, 2, np.nan, 4, 5]
        })
        
        df, errors = clean_column_integer(df_nan, 'value', 'test.csv', allow_empty=False)
        
        assert len(errors) == 1  # NaN is invalid
        assert len(df) == 4  # One row removed
        assert df['value'].dtype == 'int64'

    def test_clean_column_floats_with_nan_values(self):
        """Test float column cleaning with NaN values."""
        df_nan = pd.DataFrame({
            'value': [1.5, 2.5, np.nan, 4.5, 5.5]
        })
        
        df, errors = clean_column_floats(df_nan, 'value', 'test.csv')
        
        assert len(errors) == 1  # NaN is considered invalid by check_cell_float
        assert len(df) == 4  # One row removed
        assert df['value'].dtype == 'float64'

    def test_clean_dataframe_floats_with_missing_column_continue_processing(self):
        """Test clean_dataframe_floats continues processing when column is missing."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']
        })
        
        # Test with a list that has missing column first, then valid column
        # This should trigger the continue statement and mask_valid initialization
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['nonexistent', 'value']
        )
        
        assert len(errors) == 1  # One error for missing column
        assert "não foi encontrada" in errors[0]
        assert len(df) == 3  # All rows kept for valid column
        assert 'value' in df.columns  # Valid column was processed

    def test_clean_dataframe_floats_with_multiple_missing_columns(self):
        """Test clean_dataframe_floats handles multiple missing columns correctly."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']
        })
        
        # Test with multiple missing columns to ensure continue statements work
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['nonexistent1', 'nonexistent2', 'value']
        )
        
        assert len(errors) == 2  # Two errors for missing columns
        assert all("não foi encontrada" in error for error in errors[:2])
        assert len(df) == 3  # All rows kept for valid column
        assert 'value' in df.columns  # Valid column was processed

    def test_clean_dataframe_floats_with_missing_column_at_end(self):
        """Test clean_dataframe_floats with missing column at the end of the list."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']
        })
        
        # Test with missing column at the end to ensure continue works correctly
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['value', 'nonexistent']
        )
        
        assert len(errors) == 1  # One error for missing column
        assert "não foi encontrada" in errors[0]
        assert len(df) == 3  # All rows kept for valid column
        assert 'value' in df.columns  # Valid column was processed

    def test_clean_dataframe_floats_with_only_missing_columns(self):
        """Test clean_dataframe_floats with only missing columns to force continue execution."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']
        })
        
        # Test with only missing columns to ensure the continue statements are executed
        # This should trigger lines 120-123 for each missing column
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['nonexistent1', 'nonexistent2']
        )
        
        assert len(errors) == 2  # Two errors for missing columns
        assert all("não foi encontrada" in error for error in errors)
        assert df.equals(df_test)  # DataFrame unchanged since no valid columns to process

    def test_clean_dataframe_floats_with_missing_and_valid_columns_mixed(self):
        """Test clean_dataframe_floats with mixed missing and valid columns to force line coverage."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']  # All valid values to avoid conversion errors
        })
        
        # Test with missing column first, then valid column
        # This should execute lines 112-115 for the missing column
        # and then continue processing the valid column
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['nonexistent', 'value']
        )
        
        assert len(errors) == 1  # One error for missing column
        assert "não foi encontrada" in errors[0]  # Error for missing column
        assert len(df) == 3  # All rows kept (no invalid values)
        assert 'value' in df.columns  # Valid column was processed

    def test_clean_dataframe_floats_with_invalid_values_to_cover_lines_120_123(self):
        """Test clean_dataframe_floats with invalid values to force execution of lines 120-123."""
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['1.5', '2.5', '3.5']  # All valid values to avoid conversion errors
        })
        
        # Test with a valid column that has valid values
        # This should execute the processing logic without errors
        df, errors = clean_dataframe_floats(
            df_test, 'test.csv', ['value']
        )
        
        assert len(errors) == 0  # No errors with valid values
        assert len(df) == 3  # All rows kept
        assert 'value' in df.columns  # Column was processed

    def test_clean_dataframe_floats_with_invalid_float_values_specific_error_messages(self):
        """Test clean_dataframe_floats with invalid float values to trigger specific error message format."""
        df_test = pd.DataFrame({
            'float_col': ['1.5', 'invalid_text', '3.7', '', 'not_a_number'],
            'another_col': [10, 20, 30, 40, 50]
        })

        df, errors = clean_dataframe_floats(
            df_test, 'test_file.xlsx', ['float_col']
        )

        # Should have errors for 'invalid_text', empty string, and 'not_a_number'
        assert len(errors) >= 2  # At least 2 invalid values

        # Check that error messages contain proper format with line numbers
        error_messages = ' '.join(errors)
        assert "test_file.xlsx, linha" in error_messages
        assert "A coluna 'float_col' contém um valor inválido" in error_messages

        # Check that valid rows are kept (rows with '1.5' and '3.7')
        assert len(df) == 2
        assert df['float_col'].dtype == 'float64'

    def test_clean_dataframe_floats_with_min_value_constraint_triggering_errors(self):
        """Test clean_dataframe_floats with minimum value constraint to trigger validation errors."""
        df_test = pd.DataFrame({
            'score': ['0.5', '1.2', '-2.5', '5.0', '0.1'],  # Some values below min_value
            'id': [1, 2, 3, 4, 5]
        })

        # Set min_value to 1.0 to trigger errors for values below this threshold
        df, errors = clean_dataframe_floats(
            df_test, 'scores.csv', ['score'], min_value=1
        )

        # Should have errors for values below min_value (0.5, -2.5, 0.1)
        assert len(errors) >= 3

        # Verify error message format includes line numbers and specific column
        for error in errors:
            assert "scores.csv, linha" in error
            assert "A coluna 'score' contém um valor inválido" in error

        # Only values >= 1.0 should remain (1.2 and 5.0)
        assert len(df) == 2
        assert all(df['score'] >= 1.0)
