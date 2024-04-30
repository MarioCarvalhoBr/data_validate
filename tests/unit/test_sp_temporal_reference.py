from src.myparser.sp_temporal_reference import verify_sp_temporal_reference_punctuation, verify_sp_temporal_reference_unique_values

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_TEMPORAL_REFERENCE_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_temporal_reference_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_temporal_reference_errors_01

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
