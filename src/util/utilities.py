import os
import pandas as pd

def file_extension_check(path, extension='.xlsx'):
    if not path.endswith(extension):
        return False, f"ERRO: O arquivo {path} de entrada não é {extension}"
    return True, ""

def read_excel_file(path, lower_columns=False):
    df = pd.read_excel(path)
    if lower_columns:
        df.columns = df.columns.str.lower()
    return df

def check_folder_exists(folder_path):
    is_error = False
    # Invalid path
    if folder_path is None:
        return False, f"O caminho da pasta não foi especificado: {folder_path}."
    
    # Empty string
    if folder_path == "":
        return False, f"O caminho da pasta está vazio: {folder_path}."
    
    # Path to a file, not a folder
    if not os.path.exists(folder_path):
        return False, f"A pasta não foi encontrada: {folder_path}."
    
    # Path to a folder
    if not os.path.isdir(folder_path):
        return False, f"O caminho especificado não é uma pasta: {folder_path}."
    return True, ""

def check_file_exists(file_path):
    # Invalid path
    if file_path is None:
        return False, f"{file_path}: O caminho do arquivo não foi especificado."
    
    # Pegar o arquivo que está sendo verificado
    file_name = os.path.basename(file_path)


    """Verifica se um arquivo existe."""
    if not os.path.isfile(file_path):
        ultima_pasta = os.path.basename(os.path.dirname(file_path))
        utimo_arquivo = os.path.basename(file_path)
        return False, f"{file_name}: O arquivo não foi encontrado no caminho '{ultima_pasta}/{utimo_arquivo}'."
    return True, ""