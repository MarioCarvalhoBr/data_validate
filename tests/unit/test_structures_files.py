from src.myparser.structures_files import verify_expected_structure_files, verify_not_exepected_files_in_folder_root, verify_files_data_clean

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

# Structures files
from tests.unit.test_constants import STRUCTURE_FILES_COLUMNS_DICT, STRUCTURE_FILES_TO_CLEAN_LIST

# DATA FRAMES - GROUND TRUTH 01
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_01, df_sp_temporal_reference_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_proportionalities_data_ground_truth_01

# DATA FRAMES - GROUND TRUTH 02
from tests.unit.test_constants import df_sp_scenario_data_ground_truth_02, df_sp_temporal_reference_data_ground_truth_02, df_sp_description_data_ground_truth_02, df_sp_composition_data_ground_truth_02, df_sp_values_data_ground_truth_02, df_sp_proportionalities_data_ground_truth_02

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01, df_sp_composition_errors_01, df_sp_values_errors_01, df_sp_proportionalities_errors_01

# DATA FRAMES - ERROS 03
from tests.unit.test_constants import df_sp_scenario_errors_03, df_sp_temporal_reference_errors_03, df_sp_description_errors_03, df_sp_composition_errors_03, df_sp_values_errors_03, df_sp_proportionalities_errors_03

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_scenario_errors_04, df_sp_temporal_reference_errors_04, df_sp_description_errors_04, df_sp_composition_errors_04, df_sp_values_errors_04, df_sp_proportionalities_errors_04

# DATA FRAMES - ERROS 05
from tests.unit.test_constants import df_sp_scenario_errors_05, df_sp_temporal_reference_errors_05, df_sp_description_errors_05, df_sp_composition_errors_05, df_sp_values_errors_05, df_sp_proportionalities_errors_05

# DATA FRAMES - ERROS 06

# PATHS MAIN
from tests.unit.test_constants import path_input_data_errors_02, path_input_data_errors_03, path_input_data_errors_05

# Testes: verify_expected_structure_files
def test_count_errors_verify_expected_structure_files_data_ground_truth_01():
        # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_data_ground_truth_01,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_data_ground_truth_01,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_data_ground_truth_01,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_data_ground_truth_01,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_data_ground_truth_01,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_data_ground_truth_01,
    }

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name])
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is True

    assert len(all_errors_structure_files) == 0
    assert len(all_warnings_structure_files) == 0

def test_count_errors_verify_expected_structure_files_data_ground_truth_02():
    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_data_ground_truth_02,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_data_ground_truth_02,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_data_ground_truth_02,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_data_ground_truth_02,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_data_ground_truth_02,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_data_ground_truth_02,
    }

    sp_scenario_exists = True
    sp_proportionalities_exists = True
    if df_sp_scenario_data_ground_truth_02 is None or df_sp_scenario_data_ground_truth_02.empty:
        sp_scenario_exists = False
    if df_sp_temporal_reference_data_ground_truth_02 is None or df_sp_temporal_reference_data_ground_truth_02.empty:
        sp_proportionalities_exists = False

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name], sp_scenario_exists, sp_proportionalities_exists)
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is True

    assert len(all_errors_structure_files) == 0
    assert len(all_warnings_structure_files) == 0

def test_count_errors_verify_expected_structure_files_errors_01():
        # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_01,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_01,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_01,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_01,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_01,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_01,
    }

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name])
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is True
    assert len(all_errors_structure_files) == 0
    assert len(all_warnings_structure_files) == 0

def test_errors_verify_expected_structure_files_errors_03():
    
    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_03,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_03,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_03,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_03,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_03,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_03,
    }

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name])
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is False

    # Numero de erros esperado == 13
    assert len(all_errors_structure_files) == 13
    # Numero de warnings esperado == 5
    assert len(all_warnings_structure_files) == 5

    # Verifica se os erros são o esperado
    assert all_errors_structure_files[0] == "cenarios.xlsx, linha 2: A coluna 'nome' não pode conter o caracter '|'."
    assert all_errors_structure_files[1] == "cenarios.xlsx, linha 3: A coluna 'descricao' não pode conter o caracter '|'."
    assert all_errors_structure_files[2] == "referencia_temporal.xlsx, linha 3: A coluna 'descricao' não pode conter o caracter '|'."
    assert all_errors_structure_files[3] == "descricao.xlsx, linha 8: A coluna 'nome_simples' não pode conter o caracter '|'."
    assert all_errors_structure_files[4] == "descricao.xlsx, linha 9: A coluna 'nome_simples' não pode conter o caracter '|'."
    assert all_errors_structure_files[5] == "descricao.xlsx, linha 8: A coluna 'nome_completo' não pode conter o caracter '|'."
    assert all_errors_structure_files[6] == "descricao.xlsx, linha 8: A coluna 'desc_simples' não pode conter o caracter '|'."
    assert all_errors_structure_files[7] == "descricao.xlsx, linha 8: A coluna 'desc_completa' não pode conter o caracter '|'."
    assert all_errors_structure_files[8] == "descricao.xlsx, linha 8: A coluna 'fontes' não pode conter o caracter '|'."
    assert all_errors_structure_files[9] == "descricao.xlsx, linha 8: A coluna 'MINHAS METAS' não pode conter o caracter '|'."
    assert all_errors_structure_files[10] == "descricao.xlsx: Coluna 'meta' esperada mas não foi encontrada."
    assert all_errors_structure_files[11] == "valores.xlsx: Coluna 'id' esperada mas não foi encontrada."
    assert all_errors_structure_files[12] == "proporcionalidades.xlsx: Coluna 'id' esperada mas não foi encontrada."

    # Verifica se os warnings são o esperado
    assert all_warnings_structure_files[0] == "cenarios.xlsx: Coluna 'COLUNA _A' será ignorada pois não está na especificação."
    assert all_warnings_structure_files[1] == "referencia_temporal.xlsx: Coluna 'COLUNA_C' será ignorada pois não está na especificação."
    assert all_warnings_structure_files[2] == "descricao.xlsx: Coluna 'MINHAS METAS' será ignorada pois não está na especificação."
    assert all_warnings_structure_files[3] == "descricao.xlsx: Coluna 'COLUNA_EXTRA' será ignorada pois não está na especificação."
    assert all_warnings_structure_files[4] == "composicao.xlsx: Coluna 'COLUNA_B' será ignorada pois não está na especificação."

def test_errors_verify_expected_structure_files_errors_04():
    
    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_04,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_04,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_04,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_04,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_04,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_04,
    }

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name])
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is False

    # Numero de erros esperado == 2
    assert len(all_errors_structure_files) == 2
    # Numero de warnings esperado == 1
    assert len(all_warnings_structure_files) == 1

    # Verifica se os erros são o esperado
    assert all_errors_structure_files[0] == "composicao.xlsx: Coluna número 3 não possui nome mas possui valores."
    assert all_errors_structure_files[1] == "valores.xlsx: Coluna número 20 não possui nome mas possui valores."

    # Verifica se os warnings são o esperado
    assert all_warnings_structure_files[0] == "composicao.xlsx: Coluna 'Unnamed: 2' será ignorada pois não está na especificação."

def test_errors_verify_expected_structure_files_errors_05():
    
    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_05,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_05,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_05,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_05,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_05,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_05,
    }
    sp_scenario_exists = True
    sp_proportionalities_exists = True
    if df_sp_scenario_errors_05 is None or df_sp_scenario_errors_05.empty:
        sp_scenario_exists = False
    if df_sp_temporal_reference_errors_05 is None or df_sp_temporal_reference_errors_05.empty:
        sp_proportionalities_exists = False

    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura de cada arquivo
    for file_name, df in data_df.items():
        is_correct, errors, warnings = verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name], sp_scenario_exists, sp_proportionalities_exists)
        all_correct_structure_files = all_correct_structure_files and is_correct
        all_errors_structure_files.extend(errors)
        all_warnings_structure_files.extend(warnings)

    assert all_correct_structure_files is False

    # Numero de erros esperado == 0
    assert len(all_errors_structure_files) == 1
    # Numero de warnings esperado == 0
    assert len(all_warnings_structure_files) == 0

    # Verifica se os erros são o esperado
    assert all_errors_structure_files[0] == "descricao.xlsx: A coluna 'cenario' não pode existir se o arquivo 'cenarios.xlsx' não existir."

# Testes: verify_not_exepected_files_in_folder_root
def test_count_errors_verify_not_exepected_files_in_folder_root_data_errors_02():
    is_correct, errors, warnings = verify_not_exepected_files_in_folder_root(path_input_data_errors_02, STRUCTURE_FILES_COLUMNS_DICT)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1
    # warnings.append(f"O arquivo '{file_basename}' não é esperado.")
    assert warnings[0] == "O arquivo 'arquivo_aleatorio.xlsx' não é esperado."

def test_count_errors_verify_not_exepected_files_in_folder_root_data_errors_05():
    is_correct, errors, warnings = verify_not_exepected_files_in_folder_root(path_input_data_errors_05, STRUCTURE_FILES_COLUMNS_DICT)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_errors_verify_not_exepected_files_in_folder_root_downt_exist_folder_files():
    is_correct, errors, warnings = verify_not_exepected_files_in_folder_root("dont_exist_path", STRUCTURE_FILES_COLUMNS_DICT)
    assert len(errors) == 1
    assert len(warnings) == 0

    assert errors[0] == "dont_exist_path: Erro ao processar verificação dos arquivos da pasta principal: [Errno 2] No such file or directory: 'dont_exist_path'."

def test_errors_verify_not_exepected_files_in_folder_root_data_errors_03():
    all_correct_structure_files = True
    all_errors_structure_files = []
    all_warnings_structure_files = []

    # Verifica a estrutura dos arquivos principais
    is_correct_main_path, errors_main_path, warnings_main_path = verify_not_exepected_files_in_folder_root(path_input_data_errors_03, STRUCTURE_FILES_COLUMNS_DICT)
    all_correct_structure_files = all_correct_structure_files and is_correct_main_path
    all_errors_structure_files.extend(errors_main_path)
    all_warnings_structure_files.extend(warnings_main_path)
    
    assert all_correct_structure_files is True

    assert len(all_errors_structure_files) == 0
    assert len(all_warnings_structure_files) == 1

    # Verifica se os warnings são o esperado
    assert all_warnings_structure_files[0] == "O arquivo 'arquivo_aleatorio.xlsx' não é esperado."

# Testes: verify_files_data_clean
def test_count_errors_verify_files_data_clean_data_errors_04():

    all_correct_clean_files = True
    all_errors_clean_files = []
    all_warnings_clean_files = []

    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_04,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_04,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_04,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_04,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_04,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_04
    }

    for file_name, columns_to_clean, value in STRUCTURE_FILES_TO_CLEAN_LIST:
        df = data_df[file_name]
        # Se for None ou empty Ignora a verificação
        if df is None or df.empty:
            continue
        is_correct_clean_files, errors_clean_files, warnings_clean_files = verify_files_data_clean(df, file_name, columns_to_clean, value)
        
        all_correct_clean_files = all_correct_clean_files and is_correct_clean_files
        all_errors_clean_files.extend(errors_clean_files)
        all_warnings_clean_files.extend(warnings_clean_files)
        
    assert all_correct_clean_files is False
    assert len(all_errors_clean_files) == 7
    assert len(all_warnings_clean_files) == 0

    assert all_errors_clean_files[0] == "descricao.xlsx, linha 3: A coluna 'codigo' contém um valor inválido: O valor '5000.77' não é um número inteiro."
    assert all_errors_clean_files[1] == "descricao.xlsx, linha 4: A coluna 'codigo' contém um valor inválido: O valor 'XX5001' não é um número."
    assert all_errors_clean_files[2] == "descricao.xlsx, linha 2: A coluna 'nivel' contém um valor inválido: O valor '-1' é menor que 1."
    assert all_errors_clean_files[3] == "descricao.xlsx, linha 3: A coluna 'nivel' contém um valor inválido: O valor '2.77' não é um número inteiro."
    assert all_errors_clean_files[4] == "descricao.xlsx, linha 4: A coluna 'nivel' contém um valor inválido: O valor 'XX3' não é um número."
    assert all_errors_clean_files[5] == "composicao.xlsx, linha 5: A coluna 'codigo_pai' contém um valor inválido: O valor '5000.7875' não é um número inteiro."
    assert all_errors_clean_files[6] == "composicao.xlsx, linha 7: A coluna 'codigo_pai' contém um valor inválido: O valor '5001.88' não é um número inteiro."

# Testes: verify_files_data_clean
def test_count_errors_verify_files_data_clean_data_errors_05():

    all_correct_clean_files = True
    all_errors_clean_files = []
    all_warnings_clean_files = []

    # Dicionário com os dataframes
    data_df = {
        SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario_errors_05,
        SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference_errors_05,

        SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description_errors_05,
        
        SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition_errors_05,
        SP_VALUES_COLUMNS.NAME_SP: df_sp_values_errors_05,
        SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities_errors_05
    }
    sp_scenario_exists = True
    if df_sp_scenario_errors_05 is None or df_sp_scenario_errors_05.empty:
        sp_scenario_exists = False

    for file_name, columns_to_clean, value in STRUCTURE_FILES_TO_CLEAN_LIST:
        df = data_df[file_name]
        # Se for None ou empty Ignora a verificação
        if df is None or df.empty:
            continue
        is_correct_clean_files, errors_clean_files, warnings_clean_files = verify_files_data_clean(df, file_name, columns_to_clean, value, sp_scenario_exists)
        
        all_correct_clean_files = all_correct_clean_files and is_correct_clean_files
        all_errors_clean_files.extend(errors_clean_files)
        all_warnings_clean_files.extend(warnings_clean_files)
        
    assert all_correct_clean_files is False
    assert len(all_errors_clean_files) == 1
    assert len(all_warnings_clean_files) == 0

    assert all_errors_clean_files[0] == f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: A tabela deve ter apenas um valor porque o arquivo {SP_SCENARIO_COLUMNS.NAME_SP} não existe."

