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
    # Invalid path
    if folder_path is None:
        return False, f"Pasta não encontrada: {folder_path}"
    # Empty string
    if folder_path == "":
        return False, f"Pasta não encontrada: {folder_path}"
    # Path to a file, not a folder
    if not os.path.exists(folder_path):
        return False, f"Pasta não encontrada: {folder_path}"
    
    if not os.path.isdir(folder_path):
        return False, f"Pasta não encontrada: {folder_path}"
    return True, ""

def check_file_exists(file_path):
    # Invalid path
    if file_path is None:
        return False, f"Arquivo não encontrado: {file_path}"
    """Verifica se um arquivo existe."""
    if not os.path.isfile(file_path):
        return False, f"Arquivo não encontrado: {file_path}"
    return True, ""