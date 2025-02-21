import datetime
import pandas as pd

from src.myparser.sp_temporal_reference import verify_sp_temporal_reference_punctuation, verify_sp_temporal_reference_unique_values, verify_sp_temporal_reference_years

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_TEMPORAL_REFERENCE_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_temporal_reference_data_ground_truth_01, df_sp_temporal_reference_data_ground_truth_04_csv_xlsx

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_temporal_reference_errors_01, df_sp_temporal_reference_errors_16

# Testes: verify_sp_temporal_reference_punctuation
def test_true_verify_sp_temporal_reference_punctuation_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_temporal_reference_punctuation(df_sp_temporal_reference_data_ground_truth_01, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_temporal_reference_punctuation_data_errors_01():
    is_correct, errors, warnings = verify_sp_temporal_reference_punctuation(df_sp_temporal_reference_errors_01, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1
    
# Testes: verify_sp_temporal_reference_unique_values
def test_verify_sp_temporal_reference_unique_values_true_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_temporal_reference_unique_values(df_sp_temporal_reference_data_ground_truth_01, columns_uniques=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_temporal_reference_unique_values_data_errors_01():
    is_correct, errors, warnings = verify_sp_temporal_reference_unique_values(df_sp_temporal_reference_errors_01, columns_uniques=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

# Testes para verify_sp_temporal_reference_years
def test_verify_sp_temporal_reference_years_true_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df_sp_temporal_reference_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0


def test_verify_sp_temporal_reference_years_true_data_ground_truth_04_csv_xlsx():
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df_sp_temporal_reference_data_ground_truth_04_csv_xlsx)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_verify_sp_temporal_reference_years_errors_16():
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df_sp_temporal_reference_errors_16)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert errors[0] == "referencia_temporal.xlsx: O ano 2025 não pode estar associado a cenários por não ser um ano futuro."



# Test when the dataframe is empty.
def test_verify_sp_temporal_reference_years_empty_dataframe():
    df = pd.DataFrame()
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is True
    assert errors == []
    assert warnings == []

# Test when the required SIMBOLO column is missing.
def test_verify_sp_temporal_reference_years_missing_simbolo():
    df = pd.DataFrame({'other': ["Dummy", 2022, 2023]})
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is True
    assert errors == []
    assert warnings == []

# Test with all future years (valid scenario).
def test_verify_sp_temporal_reference_years_all_future_years():
    current_year = datetime.datetime.now().year
    data = {
        SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO: ["Dummy", current_year + 1, current_year + 5]
    }
    df = pd.DataFrame(data)
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is True
    assert errors == []
    assert warnings == []

# Test with a past/current year which should trigger an error.
def test_verify_sp_temporal_reference_years_with_past_year():
    current_year = datetime.datetime.now().year
    data = {
        SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO: ["Dummy", current_year, current_year + 10]
    }
    df = pd.DataFrame(data)
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert errors[0] == f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O ano {current_year} não pode estar associado a cenários por não ser um ano futuro."
    
# Test with a non-integer value in the year column.
def test_verify_sp_temporal_reference_years_with_non_integer_value():
    data = {
        SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO: ["Dummy", "notayear", 3000]
    }
    df = pd.DataFrame(data)
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is False
    assert errors[0] == f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O valor notayear não é um número inteiro válido."
    assert warnings == []

# Test with multiple errors: a non-integer value and a past/current year.
def test_verify_sp_temporal_reference_years_with_multiple_errors():
    current_year = datetime.datetime.now().year
    data = {
        SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO: ["Dummy", "notayear", current_year, current_year + 15]
    }
    df = pd.DataFrame(data)
    is_correct, errors, warnings = verify_sp_temporal_reference_years(df)
    assert is_correct is False
    # Expect at least two errors: one for non-integer and one for the past/current year.
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O valor notayear não é um número inteiro válido."
    assert errors[1] == f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O ano {current_year} não pode estar associado a cenários por não ser um ano futuro."
