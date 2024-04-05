import os
from src.util.utilities import read_excel_file, check_file_exists, check_punctuation, check_unique_values

def verify_sp_temporal_reference_unique_values(path_sp_temporal_reference, columns_uniques):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_temporal_reference)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []
    name_file = os.path.basename(path_sp_temporal_reference)
    try:
        df = read_excel_file(path_sp_temporal_reference, True)
        _, errors_checkeds = check_unique_values(df, name_file, columns_uniques)
        errors.extend(errors_checkeds)
        
    except Exception as e:
        errors.append(f"{name_file}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_temporal_reference_punctuation(path_sp_temporal_reference, columns_dont_punctuation, columns_must_end_with_dot): 
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_temporal_reference)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []
    name_file = os.path.basename(path_sp_temporal_reference)
    try:
        df = read_excel_file(path_sp_temporal_reference, True)
        # Verifica se todas as colunas existem em df
        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]
        
        _, warnings = check_punctuation(df, name_file, columns_dont_punctuation, columns_must_end_with_dot)
        
    except Exception as e:
        errors.append(f"{name_file}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings
