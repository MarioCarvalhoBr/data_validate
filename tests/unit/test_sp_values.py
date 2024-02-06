from src.myparser.sp_values import verify_ids_sp_description_values

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors


# Testes: Relações entre indicadores da planilha de valores
def test_true_verify_ids_sp_description_values(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_ground_truth + "/8_valores/valores.xlsx"
    result_test,__,__ = verify_ids_sp_description_values(planilha_04_descricao, planilha_08_valores)
    assert result_test is True
def test_false_verify_ids_sp_description_values(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_errors + "/8_valores/valores.xlsx"
    result_test,__,__ = verify_ids_sp_description_values(planilha_04_descricao, planilha_08_valores)
    assert result_test is False
def test_count_errors_verify_ids_sp_description_values(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_errors + "/8_valores/valores.xlsx"
    is_correct, errors, warnings = verify_ids_sp_description_values(planilha_04_descricao, planilha_08_valores)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0