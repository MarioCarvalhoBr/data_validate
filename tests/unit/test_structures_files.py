from src.orchestrator import verify_structure_folder_files
from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01, path_input_data_errors_02, path_input_data_errors_03


# Testes: Estrutura dos arquivos da pasta de entrada
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

def test_errors_verify_structure_folder_files_data_errors_3(): # Teste true
    is_correct, errors, warnings = verify_structure_folder_files(path_input_data_errors_03)
    assert is_correct is False

    # Numero de erros esperado == 13
    assert len(errors) == 13
    # Numero de warnings esperado == 6
    assert len(warnings) == 6

    # Verifica se os erros são o esperado
    assert errors[0] == "cenarios.xlsx, linha 2: A coluna 'nome' não pode conter o caracter '|'."
    assert errors[1] == "cenarios.xlsx, linha 3: A coluna 'descricao' não pode conter o caracter '|'."
    assert errors[2] == "referencia_temporal.xlsx, linha 3: A coluna 'descricao' não pode conter o caracter '|'."
    assert errors[3] == "descricao.xlsx, linha 8: A coluna 'nome_simples' não pode conter o caracter '|'."
    assert errors[4] == "descricao.xlsx, linha 9: A coluna 'nome_simples' não pode conter o caracter '|'."
    assert errors[5] == "descricao.xlsx, linha 8: A coluna 'nome_completo' não pode conter o caracter '|'."
    assert errors[6] == "descricao.xlsx, linha 8: A coluna 'desc_simples' não pode conter o caracter '|'."
    assert errors[7] == "descricao.xlsx, linha 8: A coluna 'desc_completa' não pode conter o caracter '|'."
    assert errors[8] == "descricao.xlsx, linha 8: A coluna 'fontes' não pode conter o caracter '|'."
    assert errors[9] == "descricao.xlsx, linha 8: A coluna 'MINHAS METAS' não pode conter o caracter '|'."
    assert errors[10] == "descricao.xlsx: Coluna 'meta' esperada mas não foi encontrada."
    assert errors[11] == "valores.xlsx: Coluna 'id' esperada mas não foi encontrada."
    assert errors[12] == "proporcionalidades.xlsx: Coluna 'id' esperada mas não foi encontrada."

    # Verifica se os warnings são o esperado
    assert warnings[0] == "cenarios.xlsx: Coluna 'COLUNA _A' será ignorada pois não está na especificação."
    assert warnings[1] == "referencia_temporal.xlsx: Coluna 'COLUNA_C' será ignorada pois não está na especificação."
    assert warnings[2] == "descricao.xlsx: Coluna 'MINHAS METAS' será ignorada pois não está na especificação."
    assert warnings[3] == "descricao.xlsx: Coluna 'COLUNA_EXTRA' será ignorada pois não está na especificação."
    assert warnings[4] == "composicao.xlsx: Coluna 'COLUNA_B' será ignorada pois não está na especificação."
    assert warnings[5] == "O arquivo 'arquivo_aleatorio.xlsx' não é esperado."

