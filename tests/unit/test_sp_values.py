from src.myparser.sp_values import verify_ids_sp_description_values, verify_combination_sp_description_values_scenario_temporal_reference

# DATA FRAMES - GROUND TRUTH 01
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_01, df_sp_temporal_reference_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_values_data_ground_truth_01

# DATA FRAMES - GROUND TRUTH 02
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_02_no_scenario, df_sp_temporal_reference_data_ground_truth_02_no_scenario, df_sp_description_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01, df_sp_values_errors_01

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04, df_sp_values_errors_04

# DATA FRAMES - ERROS 05
from tests.unit.test_constants import df_sp_scenario_errors_05, df_sp_temporal_reference_errors_05, df_sp_description_errors_05, df_sp_values_errors_05
    
# Testes: verify_ids_sp_description_values
def test_true_verify_ids_sp_description_values_data_ground_truth_01():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_data_ground_truth_01, df_sp_values_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_sp_description_values_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_ids_sp_description_values_data_errors_01():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_01, df_sp_values_errors_01)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert errors[0] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5008, 5009, 5010, 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018]."

def test_count_errors_verify_ids_sp_description_values_data_errors_04():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_04, df_sp_values_errors_04)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: Códigos inválidos: ['5000.954', '5001,9483', 'Unnamed: 19']."
    assert errors[1] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5000]."

# Testes: verify_combination_sp_description_values_scenario_temporal_reference
def test_true_verify_combination_sp_description_values_scenario_temporal_reference_data_ground_truth_01():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_scenario_data_ground_truth_01, df_sp_temporal_reference_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_combination_sp_description_values_scenario_temporal_reference_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario, df_sp_scenario_data_ground_truth_02_no_scenario, df_sp_temporal_reference_data_ground_truth_02_no_scenario)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_errors_verify_combination_sp_description_values_scenario_temporal_reference_data_errors_01():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
    assert errors == ['valores.xlsx: A coluna \'5000-2030-O\' é obrigatória.', 'valores.xlsx: A coluna \'5000-2080-M\' é desnecessária.']

def test_errors_verify_combination_sp_description_values_scenario_temporal_reference_data_errors_05():
    is_correct, errors, warnings = verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description_errors_05, df_sp_values_errors_05, df_sp_scenario_errors_05, df_sp_temporal_reference_errors_05)
    assert is_correct is False
    assert len(errors) == 9
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: A coluna '2-2015' é desnecessária para o indicador de nível 1."
    assert errors[1] == "valores.xlsx: A coluna '5000-2030-O' é desnecessária."
    assert errors[2] == "valores.xlsx: A coluna '5000-2050-O' é desnecessária."
    assert errors[3] == "valores.xlsx: A coluna '5000-2030-P' é desnecessária."
    assert errors[4] == "valores.xlsx: A coluna '5000-2050-P' é desnecessária."
    assert errors[5] == "valores.xlsx: A coluna '5003-2030-O' é desnecessária."
    assert errors[6] == "valores.xlsx: A coluna '5003-2050-O' é desnecessária."
    assert errors[7] == "valores.xlsx: A coluna '5003-2030-P' é desnecessária."
    assert errors[8] == "valores.xlsx: A coluna '5003-2050-P' é desnecessária."


