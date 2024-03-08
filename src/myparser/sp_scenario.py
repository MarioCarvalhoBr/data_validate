import os
from src.util.utilities import read_excel_file, check_file_exists, check_punctuation

def verify_sp_scenario_punctuation(path_sp_scenario, columns_dont_punctuation, columns_must_end_with_dot): 
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_scenario)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []
    name_file = os.path.basename(path_sp_scenario)
    try:
        df = read_excel_file(path_sp_scenario, True)
        _, warnings = check_punctuation(df, name_file, columns_dont_punctuation, columns_must_end_with_dot)
        
    except Exception as e:
        errors.append(f"{name_file}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings
