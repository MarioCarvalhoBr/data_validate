from src.myparser.sp_values import verify_ids_sp_description_values, verify_combination_sp_description_values_scenario_temporal_reference


# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_scenario_gt, df_sp_temporal_reference_gt, df_sp_description_gt, df_sp_values_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01, df_sp_values_errors_01

# DATA FRAMES - ERROS 02

# DATA FRAMES - ERROS 03
    
# Testes: Relações entre indicadores da planilha de valores
def test_true_verify_ids_sp_description_values(): # Teste true
    result_test, __, __ = verify_ids_sp_description_values(df_sp_description_gt, df_sp_values_gt)
    assert result_test is True

def test_false_verify_ids_sp_description_values(): # Teste false
    result_test, __, __ = verify_ids_sp_description_values(df_sp_description_errors_01, df_sp_values_errors_01)
    assert result_test is False

def test_count_errors_verify_ids_sp_description_values(): # Teste false
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_01, df_sp_values_errors_01)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# verify_combination_sp_description_values_scenario_temporal_reference
def test_true_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste true
    result_test, __, __ = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_gt, df_sp_values_gt, df_sp_scenario_gt, df_sp_temporal_reference_gt)
    assert result_test is True

def test_false_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste false
    result_test, __, __ = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01)
    assert result_test is False

def test_count_errors_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste false
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01)
    # Numero de erros esperado == 3
    assert len(errors) == 3
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

def test_errors_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste false
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01)
    # Numero de erros esperado == 3
    assert errors == ['valores.xlsx: A coluna \'2-2015\' é obrigatória.', 'valores.xlsx: A coluna \'5000-2030-O\' é obrigatória.', 'valores.xlsx: A coluna \'5000-2080-M\' é desnecessária.']
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
