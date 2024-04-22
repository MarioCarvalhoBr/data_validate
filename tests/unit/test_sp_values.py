from src.myparser.sp_values import verify_ids_sp_description_values, verify_combination_sp_description_values_scenario_temporal_reference

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_scenario_gt, df_sp_temporal_reference_gt, df_sp_description_gt, df_sp_values_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01, df_sp_values_errors_01

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04, df_sp_values_errors_04
    
# Testes: verify_ids_sp_description_values
def test_true_verify_ids_sp_description_values_gt():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_gt, df_sp_values_gt)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_ids_sp_description_values_data_errors_01():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_01, df_sp_values_errors_01)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

def test_count_errors_verify_ids_sp_description_values_data_errors_04():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_04, df_sp_values_errors_04)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: Códigos inválidos: ['5000.954', '5001,9483']."
    assert errors[1] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5000]."

# Testes: verify_combination_sp_description_values_scenario_temporal_reference
def test_true_verify_combination_sp_description_values_scenario_temporal_reference_gt():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_gt, df_sp_values_gt, df_sp_scenario_gt, df_sp_temporal_reference_gt)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_errors_verify_combination_sp_description_values_scenario_temporal_reference_data_errors_01():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0
    assert errors == ['valores.xlsx: A coluna \'2-2015\' é obrigatória.', 'valores.xlsx: A coluna \'5000-2030-O\' é obrigatória.', 'valores.xlsx: A coluna \'5000-2080-M\' é desnecessária.']
