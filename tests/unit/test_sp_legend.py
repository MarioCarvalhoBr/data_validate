import pandas as pd
from io import StringIO

from src.myparser.model.spreadsheets import SP_LEGEND_COLUMNS, SP_VALUES_COLUMNS
from src.myparser.sp_legend import read_legend_qml_file, verify_values_range, verify_overlapping_legend_value, check_tuple_sequence

from tests.unit.test_constants import df_sp_values_data_ground_truth_01, df_qml_legend_data_ground_truth_01, qml_legend_exists_data_ground_truth_01

from tests.unit.test_constants import df_qml_legend_errors_01, qml_legend_exists_errors_01
from tests.unit.test_constants import df_qml_legend_errors_02, qml_legend_exists_errors_02
from tests.unit.test_constants import df_qml_legend_errors_03, qml_legend_exists_errors_03
from tests.unit.test_constants import df_sp_values_errors_04, df_qml_legend_errors_04, qml_legend_exists_errors_04
from tests.unit.test_constants import df_qml_legend_errors_05, qml_legend_exists_errors_05


from tests.unit.test_constants import df_sp_values_errors_06, df_qml_legend_errors_06, qml_legend_exists_errors_06

# Testes para: verify_overlapping_legend_value
def test_true_verify_overlapping_legend_value_data_ground_truth_01():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_data_ground_truth_01, qml_legend_exists_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_overlapping_legend_value_data_errors_01():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_errors_01, qml_legend_exists_errors_01)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert errors[0] == "legenda.qml: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos."

    # Arquivo está corrompido. Uma das fatias possui um valor não numérico.
def test_false_verify_overlapping_legend_value_data_errors_02():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_errors_02, qml_legend_exists_errors_02)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]


def test_false_verify_overlapping_legend_value_data_errors_03():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_errors_03, qml_legend_exists_errors_03)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda." == errors[0]

def test_false_verify_overlapping_legend_value_data_errors_04():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_errors_04, qml_legend_exists_errors_04)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert "legenda.qml: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[1]

def test_false_verify_overlapping_legend_value_data_errors_05():
    is_correct, errors, warnings = verify_overlapping_legend_value(df_qml_legend_errors_05, qml_legend_exists_errors_05)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0
    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Valores insuficientes para delimitar as fatias." == errors[1]
    
# Testes: para check_tuple_sequence
def test_check_tuple_sequence_no_overlap():
    value_list = [(0.0, 0.154), (0.154, 0.308), (0.308, 0.462), (0.462, 0.616), (0.616, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 0

def test_check_tuple_sequence_single_overlap():
    value_list = [(0.0, 0.154), (0.155, 0.308), (0.308, 0.462), (0.462, 0.616), (0.616, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_multiple_overlaps():
    value_list = [(0.0, 0.154), (0.155, 0.308), (0.309, 0.462), (0.463, 0.616), (0.617, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 4

def test_check_tuple_sequence_partial_overlap():
    value_list = [(0.0, 0.154), (0.154, 0.308), (0.308, 0.462), (0.463, 0.616), (0.616, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_start_overlap():
    value_list = [(0.0, 0.154), (0.154, 0.308), (0.308, 0.462), (0.462, 0.616), (0.615, 0.77)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 1
    assert errors[0] == "Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda."

def test_check_tuple_sequence_end_overlap():
    value_list = [(0.0, 0.154), (0.154, 0.308), (0.308, 0.462), (0.462, 0.616), (0.616, 0.770)]
    errors = check_tuple_sequence(value_list)
    assert len(errors) == 0


def test_verify_overlapping_legend_value_overlap_detected():
    data = {
        'lower': ["0.0"," 0.154", "0.308", "0.462", "0.616"],
        'upper': ["0.154", "0.308", "0.462","0.516", "0.77"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, warnings = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda." == errors[0]

def test_verify_overlapping_legend_value_no_legend():
    df_qml_legend = pd.DataFrame()
    qml_legend_exists = False
    
    is_valid, errors, _ = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert is_valid
    assert len(errors) == 0


def test_verify_overlapping_legend_value_empty_df():
    df_qml_legend = pd.DataFrame()
    qml_legend_exists = True
    
    is_valid, errors, _ = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 1
    assert errors[0] == "legenda.qml: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos."

def test_verify_overlapping_legend_value_non_numeric_values():
    data = {
        'lower': ["0.0"," 0.154", None],
        'upper': ["0.154", "0.308", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, _ = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 2

    assert "legenda.qml: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]
    assert 'legenda.qml: Arquivo está corrompido. Valores insuficientes para delimitar as fatias.' == errors[1]

def test_verify_overlapping_legend_value_lower_greater_than_upper():
    data = {
        'lower': ["0.0"," 0.154", "0.5"],
        'upper': ["0.154", "0.308", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, _ = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 2

    assert "legenda.qml: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda." == errors[0]
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[1]

def test_verify_overlapping_legend_value_not_in_order():
    data = {
        'lower': ["0.0"," 0.462", "0.154"],
        'upper': ["0.154", "0.616", "0.308"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, warnings = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." in errors[0]

def test_verify_overlapping_legend_value_overlapping():
    data = {
        'lower': ["0.0", "0.154", "0.308"],
        'upper': ["0.154", "0.462", "0.462"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, warnings = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert not is_valid
    assert len(errors) == 1
    assert "legenda.qml: Arquivo está corrompido. Fatias não estão descritas na ordem crescente." == errors[0]

def test_verify_overlapping_legend_value_success():
    data = {
        'lower': ["0.0", "0.154", "0.308", "0.462", "0.616"],
        'upper': ["0.154", "0.308", "0.462", "0.616", "0.77"]
    }
    df_qml_legend = pd.DataFrame(data)
    qml_legend_exists = True
    
    is_valid, errors, warnings = verify_overlapping_legend_value(df_qml_legend, qml_legend_exists)
    
    assert is_valid
    assert len(errors) == 0

# Testes: verify_values_range
def test_true_verify_values_range_data_ground_truth_01():
    is_correct, errors, warnings = verify_values_range(df_sp_values_data_ground_truth_01, df_qml_legend_data_ground_truth_01, qml_legend_exists_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0


def test_true_verify_values_range_data_errors_04():
    is_correct, errors, warnings = verify_values_range(df_sp_values_errors_04, df_qml_legend_errors_04, qml_legend_exists_errors_04)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert "valores.xlsx, linha 17: O valor 0.789912176738247 está fora do intervalo de 0.0 a 0.77 para a coluna '5000-2030-P'." == errors[0]
    assert "valores.xlsx, linha 6: O valor 0.779055534730612 está fora do intervalo de 0.0 a 0.77 para a coluna '5000-2050-P'." == errors[1]
    assert "valores.xlsx, linha 15: O valor 0.846897288840176 está fora do intervalo de 0.0 a 0.77 para a coluna '5005-2015'." == errors[2]

def test_true_verify_values_range_data_errors_06():
    is_correct, errors, warnings = verify_values_range(df_sp_values_errors_06, df_qml_legend_errors_06, qml_legend_exists_errors_06)
    
    assert is_correct is False
    assert len(errors) == 4
    assert len(warnings) == 0

    assert "valores.xlsx, linha 17: O valor 0.789912176738247 está fora do intervalo de 0.0 a 0.77 para a coluna '5000-2030-P'." == errors[0]
    assert "valores.xlsx, linha 6: O valor 0.779055534730612 está fora do intervalo de 0.0 a 0.77 para a coluna '5000-2050-P'." == errors[1]
    assert "valores.xlsx, linha 2: O valor 0.806633367915323 está fora do intervalo de 0.0 a 0.77 para a coluna '5001-2015'." == errors[2]
    assert "valores.xlsx, linha 15: O valor 0.846897288840176 está fora do intervalo de 0.0 a 0.77 para a coluna '5005-2015'." == errors[3]


# Testes Unitários
def test_verify_values_range_default_range_within():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        'indicador_1': [0.5, 0.7, 0.9],
        'indicador_2': [0.1, 0.4, 0.8]
    }
    df_values = pd.DataFrame(data_values)
    df_qml_legend = None  # Não usado para este teste

    qml_legend_exists = False

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert is_valid
    assert len(errors) == 0

def test_verify_values_range_default_range_outside():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        '2-2015-O': ["0.5", "1.2", "0.7"],
        '2-2015-P': ["0.1","0.4", "1.1"]
    }
    df_values = pd.DataFrame(data_values)
    df_qml_legend = pd.DataFrame()  # Não usado para este teste

    qml_legend_exists = False

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert not is_valid
    assert len(errors) == 2
    assert f"{SP_VALUES_COLUMNS.NAME_SP}, linha 3: O valor 1.2 está fora do intervalo de 0 a 1 para a coluna '2-2015-O'." in errors
    assert f"{SP_VALUES_COLUMNS.NAME_SP}, linha 4: O valor 1.1 está fora do intervalo de 0 a 1 para a coluna '2-2015-P'." in errors

def test_verify_values_range_qml_range_within():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        '2-2015': ["5.0", "7.0", "9.0"],
        '2-2016': ["1.0", "4.0", "8.0"]
    }
    df_values = pd.DataFrame(data_values)
    data_qml = {
        'lower': [0, 1],
        'upper': [10, 10]
    }
    df_qml_legend = pd.DataFrame(data_qml)

    qml_legend_exists = True

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert is_valid
    assert len(errors) == 0

def test_verify_values_range_qml_range_outside():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        '2-2015-O': ["5.0", "12.0", "7.0"],
        '2-2015-P': ["1.0", "4.0", "11.0"]
    }
    df_values = pd.DataFrame(data_values)
    data_qml = {
        'lower': [0, 1],
        'upper': [10, 10]
    }
    df_qml_legend = pd.DataFrame(data_qml)

    qml_legend_exists = True

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert not is_valid
    assert len(errors) == 2
    assert f"{SP_VALUES_COLUMNS.NAME_SP}, linha 3: O valor 12.0 está fora do intervalo de 0.0 a 10.0 para a coluna '2-2015-O'." in errors
    assert f"{SP_VALUES_COLUMNS.NAME_SP}, linha 4: O valor 11.0 está fora do intervalo de 0.0 a 10.0 para a coluna '2-2015-P'." in errors

def test_verify_values_range_processing_error():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        '2-2015-O': ['5.0', '12.0', '7.0'],
        '2-2015-P': ['1.0', '4.0', '11.0']
    }
    df_values = pd.DataFrame(data_values)
    df_qml_legend = pd.DataFrame()  # Não usado para este teste

    qml_legend_exists = False

    # Introduzir um erro removendo uma coluna necessária
    df_values = df_values.drop(columns=['2-2015-O'])

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert is_valid is False
    assert len(errors) == 2

    assert f"{SP_VALUES_COLUMNS.NAME_SP}, linha 4: O valor 11.0 está fora do intervalo de 0 a 1 para a coluna '2-2015-P'." == errors[1]


def test_verify_values_range_qml_invalid_values():
    data_values = {
        'id': [1, 2, 3],
        'nome': ['Cidade A', 'Cidade B', 'Cidade C'],
        'indicador_1': [5.0, 12.0, 7.0],
        'indicador_2': [1.0, 4.0, 11.0]
    }
    df_values = pd.DataFrame(data_values)
    data_qml = {
        'lower': [None],
        'upper': [None]
    }
    df_qml_legend = pd.DataFrame(data_qml)

    qml_legend_exists = True

    is_valid, errors, warnings = verify_values_range(df_values, df_qml_legend, qml_legend_exists)

    assert is_valid is False
    assert len(errors) == 1
    assert f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Uma das fatias possui um valor não numérico." == errors[0]



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
    assert df.iloc[0]['symbol'] == 0
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
    