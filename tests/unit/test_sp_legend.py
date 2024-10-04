import pandas as pd
from io import StringIO

from src.myparser.sp_legend import read_legend_qml_file, verify_values_range_multiple_legend, verify_overlapping_multiple_legend_value 
from src.util.utilities import check_tuple_sequence, check_overlapping
from tests.unit.test_constants import path_input_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_scenario_data_ground_truth_01

from tests.unit.test_constants import path_input_data_errors_01, df_sp_description_errors_01
from tests.unit.test_constants import path_input_data_errors_02, df_sp_description_errors_02
from tests.unit.test_constants import path_input_data_errors_03, df_sp_description_errors_03
from tests.unit.test_constants import path_input_data_errors_04, df_sp_description_errors_04, df_sp_scenario_errors_04, df_sp_values_errors_04
from tests.unit.test_constants import path_input_data_errors_05, df_sp_description_errors_05
from tests.unit.test_constants import path_input_data_errors_06, df_sp_description_errors_06, df_sp_scenario_errors_06, df_sp_values_errors_06

from tests.unit.test_constants import path_input_data_errors_11, df_sp_values_errors_11, df_sp_description_errors_11, df_sp_scenario_errors_11

# Testes para:  verify_overlapping_multiple_legend_value(root_path, df_description)
def test_true_verify_overlapping_multiple_legend_value_data_ground_truth_01():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_ground_truth_01, df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_overlapping_multiple_legend_value_data_errors_01():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_errors_01, df_sp_description_errors_01)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    # PAREI AQUI
    assert errors[0] == "legenda.qml: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos."

    # Arquivo está corrompido. Uma das fatias possui um valor não numérico.
def test_false_verify_overlapping_multiple_legend_value_data_errors_02():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_errors_02, df_sp_description_errors_02)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]


def test_false_verify_overlapping_multiple_legend_value_data_errors_03():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_errors_03, df_sp_description_errors_03)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda." == errors[0]

def test_false_verify_overlapping_multiple_legend_value_data_errors_04():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_errors_04, df_sp_description_errors_04)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert "legenda.qml: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[1]

def test_false_verify_overlapping_multiple_legend_value_data_errors_05():
    is_correct, errors, warnings = verify_overlapping_multiple_legend_value(path_input_data_errors_05, df_sp_description_errors_05)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Valores insuficientes para delimitar as fatias." == errors[1]
    
# Testes: para check_tuple_sequence
def test_check_tuple_sequence_no_overlap():
    value_list = [(0.0, 0.15), (0.16, 0.30), (0.31, 0.46), (0.47, 0.61), (0.62, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 0

def test_check_tuple_sequence_single_overlap():
    value_list = [(0.0, 0.15), (0.18, 0.30), (0.31, 0.46), (0.47, 0.61), (0.62, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_multiple_overlaps():
    value_list = [(0.0, 0.154), (0.155, 0.308), (0.309, 0.462), (0.463, 0.616), (0.617, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 4

def test_check_tuple_sequence_partial_overlap():
    value_list = [(0.0, 0.15), (0.16, 0.30), (0.31, 0.46), (0.48, 0.61), (0.62, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_start_overlap():
    value_list = [(0.0, 0.15), (0.16, 0.30), (0.31, 0.46), (0.47, 0.61), (0.68, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_end_overlap():
    value_list = [(0.0, 0.15), (0.16, 0.30), (0.31, 0.46), (0.47, 0.61), (0.62, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 0


def test_verify_overlapping_multiple_legend_value_overlap_detected():
    data = {
        'lower': ["0.0"," 0.16", "0.31", "0.47", "0.61"],
        'upper': ["0.15", "0.30", "0.46","0.51", "0.77"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda." == errors[0]

def test_verify_overlapping_multiple_legend_value_empty_df():
    df_qml_legend = pd.DataFrame()
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 1
    assert errors[0] == "legenda.qml: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos."

def test_verify_overlapping_multiple_legend_value_non_numeric_values():
    data = {
        'lower': ["0.0"," 0.154", None],
        'upper': ["0.154", "0.308", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 2

    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]
    assert 'legenda.qml: Arquivo está corrompido. Valores insuficientes para delimitar as fatias.' == errors[1]

def test_verify_overlapping_multiple_legend_value_lower_greater_than_upper():
    data = {
        'lower': ["0.0"," 0.154", "0.5"],
        'upper': ["0.154", "0.308", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 2

    assert "legenda.qml: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[1]

def test_verify_overlapping_multiple_legend_value_not_in_order():
    data = {
        'lower': ["0.0"," 0.462", "0.154"],
        'upper': ["0.154", "0.616", "0.308"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." in errors[0]

def test_verify_overlapping_multiple_legend_value_overlapping():
    data = {
        'lower': ["0.0", "0.154", "0.308"],
        'upper': ["0.154", "0.462", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[0]

def test_verify_overlapping_multiple_legend_value_success():
    data = {
        'lower': ["0.0"," 0.16", "0.31", "0.47", "0.52"],
        'upper': ["0.15", "0.30", "0.46","0.51", "0.77"]
    }
    df_qml_legend = pd.DataFrame(data)
    
    is_valid, errors = check_overlapping("legenda.qml", df_qml_legend)
    
    assert is_valid
    assert len(errors) == 0

# Testes: verify_values_range_multiple_legend(root_path, df_values, df_description, df_sp_scenario):
def test_true_verify_values_range_multiple_legend_data_ground_truth_01():
    is_correct, errors, warnings = verify_values_range_multiple_legend(root_path=path_input_data_ground_truth_01, df_values=df_sp_values_data_ground_truth_01, df_description=df_sp_description_data_ground_truth_01, df_sp_scenario=df_sp_scenario_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0


def test_true_verify_values_range_multiple_legend_data_errors_04():
    is_correct, errors, warnings = verify_values_range_multiple_legend(root_path=path_input_data_errors_04, df_values=df_sp_values_errors_04, df_description=df_sp_description_errors_04, df_sp_scenario=df_sp_scenario_errors_04)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert "valores.xlsx, linha 17: O valor 0.789912176738247 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5000-2030-P'." == errors[0]
    assert "valores.xlsx, linha 6: O valor 0.779055534730612 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5000-2050-P'." == errors[1]
    assert "valores.xlsx, linha 15: O valor 0.846897288840176 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5005-2015'." == errors[2]


def test_true_verify_values_range_multiple_legend_data_errors_11():
    is_correct, errors, warnings = verify_values_range_multiple_legend(path_input_data_errors_11, df_sp_values_errors_11, df_sp_description_errors_11, df_sp_scenario_errors_11)
    
    assert is_correct is False
    assert len(errors) == 4
    assert len(warnings) == 0

    assert "valores.xlsx, linha 2: O valor 2 está fora do intervalo da legenda (0 a 1) para a coluna '2-2015'." == errors[0]
    assert "valores.xlsx, linha 3: O valor 3 está fora do intervalo da legenda (0 a 1) para a coluna '2-2015'." == errors[1]
    assert "valores.xlsx, linha 4: O valor 4 está fora do intervalo da legenda (0 a 1) para a coluna '2-2030-O'." == errors[2]
    assert "valores.xlsx, linha 5: O valor 5 está fora do intervalo da legenda (0 a 1) para a coluna '2-2030-O'." == errors[3]


def test_true_verify_values_range_multiple_legend_data_errors_06():
    is_correct, errors, warnings = verify_values_range_multiple_legend(path_input_data_errors_06, df_sp_values_errors_06, df_sp_description_errors_06, df_sp_scenario_errors_06)
    
    assert is_correct is False
    assert len(errors) == 4
    assert len(warnings) == 0

    assert "valores.xlsx, linha 17: O valor 0.789912176738247 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5000-2030-P'." == errors[0]
    assert "valores.xlsx, linha 6: O valor 0.779055534730612 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5000-2050-P'." == errors[1]
    assert "valores.xlsx, linha 2: O valor 0.806633367915323 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5001-2015'." == errors[2]
    assert "valores.xlsx, linha 15: O valor 0.846897288840176 está fora do intervalo da legenda (0.0 a 0.77) para a coluna '5005-2015'." == errors[3]

# Testes Unitários
def test_read_legend_qml_file_success():
    qml_content = """<root>
                        <renderer-v2>
                            <ranges>
                                <range uuid="1" label="Test 1" lower="0.0" upper="1.0" symbol="0" render="None"/>
                            </ranges>
                        </renderer-v2>
                     </root>"""
    qml_file_path = StringIO(qml_content)
    
    df, errors = read_legend_qml_file(qml_file_path)
    
    assert df.shape[0] == 1
    assert len(errors) == 0
    assert df.iloc[0]['uuid'] == "1"
    assert df.iloc[0]['label'] == "Test 1"
    assert df.iloc[0]['lower'] == "0.0"
    assert df.iloc[0]['upper'] == "1.0"
    assert df.iloc[0]['symbol'] == "0"
    assert df.iloc[0]['render'] == "None"

def test_read_legend_qml_file_no_renderer_v2():
    qml_content = """<root></root>"""
    qml_file_path = StringIO(qml_content)
    
    df, errors = read_legend_qml_file(qml_file_path)
    
    assert df.empty
    assert len(errors) == 1
    assert "Não foram encontrados dados." in errors[0]

def test_read_legend_qml_file_no_ranges():
    qml_content = """<root>
                        <renderer-v2></renderer-v2>
                     </root>"""
    qml_file_path = StringIO(qml_content)
    
    df, errors = read_legend_qml_file(qml_file_path)
    
    assert df.empty
    assert len(errors) == 1
    assert "Não foram encontrados dados." in errors[0]

def test_read_legend_qml_file_malformed():
    qml_content = """<root>
                        <renderer-v2>
                            <ranges>
                                <range uuid="1" label="Test 1" lower="0.0" upper="1.0" symbol="0" render="None">
                            </ranges>
                        </renderer-v2>
                     </root>"""  # Note the missing </range> closing tag
    qml_file_path = StringIO(qml_content)
    
    df, errors = read_legend_qml_file(qml_file_path)
    
    assert df.empty
    assert len(errors) == 1
    assert "Erro ao processar o arquivo" in errors[0]

def test_read_legend_qml_file_non_existent():
    qml_file_path = "non_existent_file.qml"
    
    df, errors = read_legend_qml_file(qml_file_path)
    
    assert df.empty
    assert len(errors) == 1

    assert "Erro ao processar o arquivo non_existent_file.qml: [Errno 2] No such file or directory: 'non_existent_file.qml'" == errors[0]
    