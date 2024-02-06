import os
from src.util.utilities import file_extension_check, read_excel_file

def extract_ids_from_description(df_description):
    ids = set(df_description['codigo'].astype(str))
    # Converte em inteiros
    ids = set(int(id) for id in ids if id.isdigit())
    return ids

def extract_ids_from_values(df_values):
    ids = set(df_values.columns.str.split('-').str[0])
    ids = set(id for id in ids if id.isdigit())
    # Converte em inteiros
    ids = set(int(id) for id in ids)
    return ids

def compare_ids(id_description, id_values, name_sp_description, name_sp_values):
    errors = []
    id_description_not_in_values = id_description - id_values
    id_values_not_in_description = id_values - id_description

    if id_description_not_in_values:
        errors.append(f"{name_sp_description}: Códigos dos indicadores ausentes em {name_sp_values}: {list(id_description_not_in_values)}")
    if id_values_not_in_description:
        errors.append(f"{name_sp_values}: Códigos dos indicadores ausentes em {name_sp_description}: {list(id_values_not_in_description)}")
    
    return errors

def verify_ids_sp_description_values(path_sp_description, path_sp_values):
    errors = []
    warnings = []

    try:
        is_correct, error_message = file_extension_check(path_sp_description, '.xlsx')
        if not is_correct:
            errors.append(error_message)
            return False, errors, warnings
        
        is_correct, error_message = file_extension_check(path_sp_values, '.xlsx')
        if not is_correct:
            errors.append(error_message)
            return False, errors, warnings
        
        
        df_description = read_excel_file(path_sp_description)
        df_values = read_excel_file(path_sp_values)

        id_description = extract_ids_from_description(df_description)
        id_values = extract_ids_from_values(df_values)

        errors += compare_ids(id_description, id_values, os.path.basename(path_sp_description), os.path.basename(path_sp_values))

    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Erro ao processar os arquivos: {e}")

    is_correct = False
    if not errors:
        is_correct = True
    return is_correct, errors, warnings
