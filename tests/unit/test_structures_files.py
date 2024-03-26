from src.orchestrator import verify_structure_folder_files

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
    # Numero de erros esperado == 2
    assert len(errors) == 1
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
    assert errors[0] == "A pasta não foi encontrada: dont_exist_path."

# verify_structure_folder_files to path_input_data_errors_02
def test_count_errors_verify_structure_folder_files_data_errors_2(): # Teste false
    is_correct, errors, warnings = verify_structure_folder_files(path_input_data_errors_02)
    assert is_correct is False
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
