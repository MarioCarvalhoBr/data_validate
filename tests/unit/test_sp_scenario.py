from src.myparser.sp_scenario import verify_sp_scenario_punctuation, verify_sp_scenario_unique_values

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_SCENARIO_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01

# Teste: verify_sp_scenario_punctuation
def test_true_verify_sp_scenario_punctuation_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_scenario_punctuation(df_sp_scenario_data_ground_truth_01, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_scenario_punctuation_data_errors_01():
    is_correct, errors, warnings = verify_sp_scenario_punctuation(df_sp_scenario_errors_01, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 2

# Teste: verify_sp_scenario_unique_values
def test_verify_sp_scenario_unique_values_true_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_scenario_unique_values(df_sp_scenario_data_ground_truth_01, columns_uniques=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_scenario_unique_values_data_errors_01():
    is_correct, errors, warnings = verify_sp_scenario_unique_values(df_sp_scenario_errors_01, columns_uniques=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO])
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
