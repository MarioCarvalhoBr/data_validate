#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

import pandas as pd
import numpy as np
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing


class TestDataCleaning:
    """Test cases for data cleaning functions."""

    def setup_method(self):
        """Set up test data."""
        self.df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "value": ["10", "20", "invalid", "30", ""],
                "float_val": ["1.5", "2.5", "invalid", "3.5", "4.5"],
                "mixed": [1, "2", 3.0, "invalid", 5],
            }
        )

    def test_clean_column_integer_column_not_found(self):
        """Test cleaning integer column that doesn't exist."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "nonexistent", "test.csv")

        assert len(errors) == 1
        assert "não foi encontrada" in errors[0]
        assert df.equals(self.df)

    def test_clean_column_integer_basic_cleaning(self):
        """Test basic integer column cleaning."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "id", "test.csv")

        assert len(errors) == 0
        assert len(df) == 5
        assert df["id"].dtype == "int64"
        assert list(df["id"]) == [1, 2, 3, 4, 5]

    def test_clean_column_integer_with_invalid_values(self):
        """Test integer column cleaning with invalid values."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "value", "test.csv")

        assert len(errors) == 2  # 'invalid' and empty string are invalid
        assert "valor inválido" in errors[0]
        assert len(df) == 3  # Two rows removed
        assert df["value"].dtype == "int64"

    def test_clean_column_integer_with_min_value(self):
        """Test integer column cleaning with minimum value constraint."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "id", "test.csv", min_value=3)

        assert len(errors) == 2  # IDs 1 and 2 are below minimum
        assert len(df) == 3  # Two rows removed
        assert list(df["id"]) == [3, 4, 5]

    def test_clean_column_integer_allow_empty_true(self):
        """Test integer column cleaning allowing empty values."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "value", "test.csv", allow_empty=True)

        assert len(errors) == 1  # Only 'invalid' is invalid
        assert len(df) == 4  # One row removed
        assert df["value"].dtype == "object"  # Mixed types due to empty values

    def test_clean_column_integer_allow_empty_false(self):
        """Test integer column cleaning not allowing empty values."""
        df, errors = DataCleaningProcessing.clean_column_integer(self.df, "value", "test.csv", allow_empty=False)

        assert len(errors) == 2  # 'invalid' and empty string are invalid
        assert len(df) == 3  # Two rows removed
        assert df["value"].dtype == "int64"

    def test_clean_column_integer_with_comma_decimal(self):
        """Test integer column cleaning with comma decimal separator."""
        df_comma = pd.DataFrame({"value": ["1,0", "2,5", "3,0", "invalid"]})

        df, errors = DataCleaningProcessing.clean_column_integer(df_comma, "value", "test.csv")

        assert len(errors) == 2  # '2,5' and 'invalid' are invalid (2.5 is not integer)
        assert len(df) == 2  # Two rows removed
        assert df["value"].dtype == "int64"

    def test_clean_dataframe_integers_multiple_columns(self):
        """Test cleaning multiple integer columns."""
        df, errors = DataCleaningProcessing.clean_dataframe_integers(self.df, "test.csv", ["id", "value"])

        assert len(errors) == 2  # Two errors from 'value' column
        assert len(df) == 3  # Two rows removed
        assert df["id"].dtype == "int64"
        assert df["value"].dtype == "int64"

    def test_clean_column_integer_with_nan_values(self):
        """Test integer column cleaning with NaN values."""
        df_nan = pd.DataFrame({"value": [1, 2, np.nan, 4, 5]})

        df, errors = DataCleaningProcessing.clean_column_integer(df_nan, "value", "test.csv", allow_empty=True)

        assert len(errors) == 0
        assert len(df) == 5
        assert df["value"].dtype == "float64"  # pandas converts NaN to float

    def test_clean_column_integer_with_nan_values_not_allowed(self):
        """Test integer column cleaning with NaN values not allowed."""
        df_nan = pd.DataFrame({"value": [1, 2, np.nan, 4, 5]})

        df, errors = DataCleaningProcessing.clean_column_integer(df_nan, "value", "test.csv", allow_empty=False)

        assert len(errors) == 1  # NaN is invalid
        assert len(df) == 4  # One row removed
        assert df["value"].dtype == "int64"
