from src.myparser.sp_scenario import verify_sp_scenario_punctuation, verify_sp_scenario_unique_values
from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01


# Testes: Pontuações obrigatórias e proibidas: verify_sp_scenario_punctuation
def test_true_verify_sp_scenario_punctuation(): # Teste true
    planilha_03_cenarios = path_input_data_ground_truth + "/cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_03_cenarios, columns_dont_punctuation=['nome'], columns_must_end_with_dot=['descricao'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_scenario_punctuation(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_03_cenarios, columns_dont_punctuation=['nome'], columns_must_end_with_dot=['descricao'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_false_verify_sp_scenario_punctuation_sp_not_found(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/3_cenarios_e_referencia_temporal_cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_03_cenarios, columns_dont_punctuation=['nome'], columns_must_end_with_dot=['descricao'])
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

def test_count_errors_verify_sp_scenario_punctuation(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/cenarios.xlsx"
    _, errors, warnings = verify_sp_scenario_punctuation(planilha_03_cenarios, columns_dont_punctuation=['nome'], columns_must_end_with_dot=['descricao'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

# def verify_sp_scenario_unique_values(path_sp_scenario, columns_uniques):
def test_verify_sp_scenario_unique_values_true(): # Teste true
    planilha_03_cenarios = path_input_data_ground_truth + "/cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_unique_values(planilha_03_cenarios, columns_uniques=['nome', 'simbolo'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0
def test_verify_sp_scenario_unique_values_false(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_unique_values(planilha_03_cenarios, columns_uniques=['nome', 'simbolo'])
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_verify_sp_scenario_unique_values_sp_not_found(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/3_cenarios_e_referencia_temporal_cenarios.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_unique_values(planilha_03_cenarios, columns_uniques=['nome', 'simbolo'])
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

def test_count_errors_verify_sp_scenario_unique_values(): # Teste false
    planilha_03_cenarios = path_input_data_errors_01 + "/cenarios.xlsx"
    _, errors, warnings = verify_sp_scenario_unique_values(planilha_03_cenarios, columns_uniques=['nome', 'simbolo'])
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
