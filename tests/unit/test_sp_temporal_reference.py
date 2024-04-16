from src.myparser.sp_temporal_reference import verify_sp_temporal_reference_punctuation, verify_sp_temporal_reference_unique_values

from src.myparser.structures_files import SP_TEMPORAL_REFERENCE_COLUMNS 

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_temporal_reference_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_temporal_reference_errors_01

# DATA FRAMES - ERROS 02

# DATA FRAMES - ERROS 03
    

# Testes: Pontuações obrigatórias e proibidas: verify_sp_temporal_reference_punctuation
def test_true_verify_sp_temporal_reference_punctuation_gt(): # Teste true
    is_correct, errors, warnings = verify_sp_temporal_reference_punctuation(df_sp_temporal_reference_gt, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_temporal_reference_punctuation_errors_01(): # Teste false
    is_correct, errors, warnings = verify_sp_temporal_reference_punctuation(df_sp_temporal_reference_errors_01, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_temporal_reference_punctuation_errors_01(): # Teste false
    _, errors, warnings = verify_sp_temporal_reference_punctuation(df_sp_temporal_reference_errors_01, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 1
    assert len(warnings) == 1

# verify_sp_temporal_reference_unique_values
def test_verify_sp_temporal_reference_unique_values_true_gt(): # Teste true
    is_correct, errors, warnings = verify_sp_temporal_reference_unique_values(df_sp_temporal_reference_gt, columns_uniques=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_verify_sp_temporal_reference_unique_values_false_errors_01(): # Teste false
    is_correct, errors, warnings = verify_sp_temporal_reference_unique_values(df_sp_temporal_reference_errors_01, columns_uniques=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_temporal_reference_unique_values_errors_01(): # Teste false
    _, errors, warnings = verify_sp_temporal_reference_unique_values(df_sp_temporal_reference_errors_01, columns_uniques=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])
    # Numero de erros esperado == 1
    assert len(errors) == 1
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
