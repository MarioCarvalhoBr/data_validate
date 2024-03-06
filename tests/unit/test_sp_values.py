from src.myparser.sp_values import verify_ids_sp_description_values, verify_combination_sp_description_values_scenario_temporal_reference

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
    # Numero de erros esperado == 4
    assert len(errors) == 4
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# verify_combination_sp_description_values_scenario_temporal_reference
def test_true_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_ground_truth + "/8_valores/valores.xlsx"
    planilha_03_cenarios_e_referencia_temporal = path_input_data_ground_truth + "/3_cenarios_e_referencia_temporal/cenarios.xlsx"
    planilha_03_cenarios_e_referencia_temporal_referencia_temporal = path_input_data_ground_truth + "/3_cenarios_e_referencia_temporal/referencia_temporal.xlsx"
    result_test,__,__ = verify_combination_sp_description_values_scenario_temporal_reference(planilha_04_descricao, planilha_08_valores, planilha_03_cenarios_e_referencia_temporal, planilha_03_cenarios_e_referencia_temporal_referencia_temporal)
    assert result_test is True
def test_false_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_errors + "/8_valores/valores.xlsx"
    planilha_03_cenarios_e_referencia_temporal = path_input_data_errors + "/3_cenarios_e_referencia_temporal/cenarios.xlsx"
    planilha_03_cenarios_e_referencia_temporal_referencia_temporal = path_input_data_errors + "/3_cenarios_e_referencia_temporal/referencia_temporal.xlsx"
    result_test,__,__ = verify_combination_sp_description_values_scenario_temporal_reference(planilha_04_descricao, planilha_08_valores, planilha_03_cenarios_e_referencia_temporal, planilha_03_cenarios_e_referencia_temporal_referencia_temporal)
    assert result_test is False
def test_count_errors_verify_combination_sp_description_values_scenario_temporal_reference(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_errors + "/8_valores/valores.xlsx"
    planilha_03_cenarios_e_referencia_temporal = path_input_data_errors + "/3_cenarios_e_referencia_temporal/cenarios.xlsx"
    planilha_03_cenarios_e_referencia_temporal_referencia_temporal = path_input_data_errors + "/3_cenarios_e_referencia_temporal/referencia_temporal.xlsx"
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(planilha_04_descricao, planilha_08_valores, planilha_03_cenarios_e_referencia_temporal, planilha_03_cenarios_e_referencia_temporal_referencia_temporal)
    # Numero de erros esperado == 5
    assert len(errors) == 5
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
