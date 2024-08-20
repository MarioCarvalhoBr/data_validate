import pandas as pd
from src.myparser.sp_values import verify_ids_sp_description_values, verify_combination_sp_description_values_scenario_temporal_reference, verify_unavailable_values, extract_ids_from_list_from_values

# DATA FRAMES - GROUND TRUTH 01
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_01, df_sp_temporal_reference_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_values_data_ground_truth_01

# DATA FRAMES - GROUND TRUTH 02
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_02_no_scenario, df_sp_temporal_reference_data_ground_truth_02_no_scenario, df_sp_description_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01, df_sp_values_errors_01

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04, df_sp_values_errors_04, df_sp_scenario_errors_04

# DATA FRAMES - ERROS 05
from tests.unit.test_constants import df_sp_scenario_errors_05, df_sp_temporal_reference_errors_05, df_sp_description_errors_05, df_sp_values_errors_05

# DATA FRAMES - ERROS 07
from tests.unit.test_constants import df_sp_values_errors_07, df_sp_scenario_errors_07

# DATA FRAMES - ERROS 11
from tests.unit.test_constants import df_sp_description_errors_11, df_sp_values_errors_11, df_sp_scenario_errors_11


# Import SP_VALUES_COLUMNS
from tests.unit.test_constants import SP_DESCRIPTION_COLUMNS

def test_verify_ids_sp_description_values_column_missing():
    df_description = pd.DataFrame({
        'other_column': ['a', 'b', 'c']
    })
    df_values = pd.DataFrame({
        '1-2020': ['1', '1', '1']
    })
    df_scenario = pd.DataFrame({
        'nome': ['Otimista', 'Pessimista'],
        'descricao': ['Este cenário representa uma visão mais otimista, sendo baseado em um menor crescimento populacional, menor desmatamento, menor consumo, etc.', 'Este cenário representa uma visão mais pessimista, sendo baseado em um maior crescimento populacional, maior desmatamento, maior consumo etc.'],
        'simbolo': ['O', 'P']
    })
    
    errors = []
    warnings = []

    result, errors, warnings = verify_ids_sp_description_values(df_description, df_values, df_scenario)

    expected_error = f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos de indicadores foi abortada porque a coluna 'codigo' está ausente."
    
    assert result is False
    assert errors == [expected_error]
    assert warnings == []

# Testes para: verify_unavailable_values
def test_true_verify_unavailable_values_data_ground_truth_01():
    is_correct, errors, warnings = verify_unavailable_values(df_sp_values_data_ground_truth_01, df_sp_scenario_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_unavailable_values_data_errors_07():
    is_correct, errors, warnings = verify_unavailable_values(df_sp_values_errors_07, df_sp_scenario_errors_07)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
    
    assert errors[0] == "valores.xlsx, linha 11: O valor não é um número válido e nem DI (Dado Indisponível) para a coluna '2-2030-O'."
    assert errors[1] == "valores.xlsx: 3 valores que não são número válido nem DI (Dado Indisponível) para a coluna '2-2050-O', entre as linhas 12 e 14."

# Testes: verify_ids_sp_description_values
def test_true_verify_ids_sp_description_values_data_ground_truth_01():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_scenario_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_sp_description_values_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario, df_sp_scenario_data_ground_truth_02_no_scenario)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_ids_sp_description_values_data_errors_01():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_01, df_sp_values_errors_01, df_sp_scenario_errors_01)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
    assert errors[0] == "valores.xlsx: Colunas inválidas: ['5000-2080-M']."
    assert errors[1] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5008, 5009, 5010, 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018]."

def test_count_errors_verify_ids_sp_description_values_data_errors_04():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_04, df_sp_values_errors_04, df_sp_scenario_errors_04)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: Colunas inválidas: ['5000.954-2015', '5001,9483-2015', 'Unnamed: 18']."
    assert errors[1] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5000]."


def test_count_errors_verify_ids_sp_description_values_data_errors_11():
    is_correct, errors, warnings = verify_ids_sp_description_values(df_sp_description_errors_11, df_sp_values_errors_11, df_sp_scenario_errors_11)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: Colunas inválidas: ['HTML-2030-P', 'PHP']."
    assert errors[1] == "descricao.xlsx: Códigos dos indicadores ausentes em valores.xlsx: [3, 4]."
    assert errors[2] == "valores.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [88, 777]."

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

# Test for extract_ids_from_list_from_values function
def test_extract_ids_with_valid_and_invalid_ids():
    codes_level_to_remove = ['1']
    list_values = ['1-2020', '2-2020', '3-2020', 'invalid', '4-2020']
    expected_ids_valids = {2, 3, 4}
    expected_extras_columns = ['invalid']
    ids_valids, extras_columns = extract_ids_from_list_from_values(codes_level_to_remove, list_values, [])
    assert ids_valids == expected_ids_valids
    assert extras_columns == expected_extras_columns

def test_extract_ids_with_all_valid_ids():
    codes_level_to_remove = ['1']
    list_values = ['2-2020', '3-2020', '4-2020']
    expected_ids_valids = {2, 3, 4}
    expected_extras_columns = []
    ids_valids, extras_columns = extract_ids_from_list_from_values(codes_level_to_remove, list_values, [])
    assert ids_valids == expected_ids_valids
    assert extras_columns == expected_extras_columns

def test_extract_ids_with_empty_list_values():
    codes_level_to_remove = ['1']
    list_values = []
    expected_ids_valids = set()
    expected_extras_columns = []
    ids_valids, extras_columns = extract_ids_from_list_from_values(codes_level_to_remove, list_values, [])
    assert ids_valids == expected_ids_valids
    assert extras_columns == expected_extras_columns

def test_extract_ids_with_all_ids_to_remove():
    codes_level_to_remove = ['2', '3', '4']
    list_values = ['2-2020', '3-2020', '4-2020']
    expected_ids_valids = set()
    expected_extras_columns = []
    ids_valids, extras_columns = extract_ids_from_list_from_values(codes_level_to_remove, list_values, [])
    assert ids_valids == expected_ids_valids
    assert extras_columns == expected_extras_columns
