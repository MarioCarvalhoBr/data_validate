import pandas as pd
from src.myparser.structures_files import _check_file_columns
from src.orchestrator import verify_structure_folder_files, check_structure_file

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01, path_input_data_errors_02


# Testes: Estrutura da pasta de arquivos
def test_true_verify_structure_folder_files(): # Teste true
    result_test,__,__ = verify_structure_folder_files(path_input_data_ground_truth)
    assert result_test is True

def test_false_verify_structure_folder_files(): # Teste false
    result_test,errors,warnings = verify_structure_folder_files(path_input_data_errors_01)
    assert result_test is True

def test_count_errors_verify_structure_folder_files(): # Teste false
    is_correct, errors, warnings = verify_structure_folder_files(path_input_data_errors_01)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

def test_errors_verify_structure_downr_exist_folder_files(): # Teste false
    is_correct, errors, warnings = verify_structure_folder_files("dont_exist_path")
    # Numero de erros esperado == 1
    assert len(errors) == 1
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
    assert errors[0] == "A pasta não foi encontrada: dont_exist_path."

# verify_structure_folder_files to path_input_data_errors_02
def test_count_errors_verify_structure_folder_files_data_errors_2(): # Teste false
    is_correct, errors, warnings = verify_structure_folder_files(path_input_data_errors_02)
    assert is_correct is False
    # Numero de erros esperado == 10
    assert len(errors) == 10
    # Numero de warnings esperado == 1
    assert len(warnings) == 1
    assert warnings[0] == "O arquivo 'arquivo_aleatorio.xlsx' não é esperado."

def test_check_file_columns():
    # Test when dataframe is empty
    df = pd.DataFrame()
    expected_structure_columns = {"test.xlsx": ["column1", "column2"]}
    errors = _check_file_columns("test.xlsx", df, expected_structure_columns)
    assert len(errors) == 1
    assert errors[0] == "test.xlsx: A planilha está vazia."

    # Test when dataframe has missing columns
    df = pd.DataFrame({"column1": [1, 2, 3]})
    errors = _check_file_columns("test.xlsx", df, expected_structure_columns)
    assert len(errors) == 1
    assert errors[0] == "test.xlsx: Coluna 'column2' não foi encontrada."

    # Test when dataframe has all expected columns
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": [4, 5, 6]})
    errors = _check_file_columns("test.xlsx", df, expected_structure_columns)
    assert len(errors) == 0

    # Test special case for 'proporcionalidades.xlsx'
    expected_structure_columns = {"proporcionalidades.xlsx": ["id"]}
    df = pd.DataFrame({"column1": ['id', 2, 3], "column2": [4, 5, 6]})
    errors = _check_file_columns("proporcionalidades.xlsx", df, expected_structure_columns)
    assert len(errors) == 0
    
    # Test special case for 'proporcionalidades.xlsx' with missing columns
    df = pd.DataFrame({"column1": [1, 2, 3]})
    errors = _check_file_columns("proporcionalidades.xlsx", df, expected_structure_columns)
    assert len(errors) == 1
    assert errors[0] == "proporcionalidades.xlsx: Coluna 'id' não foi encontrada."

# check_structure_file
def test_check_structure_file():
    # Test when file does not exist
    file_path = "dont_exist_path"
    result = check_structure_file(file_path)
    assert result is False

    # Test when file exists and has the expected structure
    file_path = path_input_data_ground_truth + "/proporcionalidades.xlsx"
    result = check_structure_file(file_path)
    assert result is True

    # Test when file exists but is not expected
    file_path = path_input_data_errors_02 + "/arquivo_aleatorio.xlsx"
    result = check_structure_file(file_path)
    assert result is False
