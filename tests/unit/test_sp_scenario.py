from src.myparser.sp_scenario import verify_sp_scenario_punctuation, verify_sp_scenario_unique_values

from src.myparser.structures_files import SP_SCENARIO_COLUMNS 

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_scenario_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01

# DATA FRAMES - ERROS 02

# DATA FRAMES - ERROS 03

def test_true_verify_sp_scenario_punctuation_gt(): # Teste true
    is_correct, errors, warnings = verify_sp_scenario_punctuation(df_sp_scenario_gt, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_scenario_punctuation_errors_01(): # Teste false
    is_correct, errors, warnings = verify_sp_scenario_punctuation(df_sp_scenario_errors_01, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_scenario_punctuation_errors_01(): # Teste false
    _, errors, warnings = verify_sp_scenario_punctuation(df_sp_scenario_errors_01, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

def test_verify_sp_scenario_unique_values_true_gt(): # Teste true
    is_correct, errors, warnings = verify_sp_scenario_unique_values(df_sp_scenario_gt, columns_uniques=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_verify_sp_scenario_unique_values_false_errors_01(): # Teste false
    is_correct, errors, warnings = verify_sp_scenario_unique_values(df_sp_scenario_errors_01, columns_uniques=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO])
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0


def test_count_errors_verify_sp_scenario_unique_values_errors_01(): # Teste false
    _, errors, warnings = verify_sp_scenario_unique_values(df_sp_scenario_errors_01, columns_uniques=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO])
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
