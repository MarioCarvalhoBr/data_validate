import os
import pandas as pd

def dataframe_clean_non_numeric_values(df, name_file, colunas_limpar):
    # Colunas para verificar se são numéricas
    colunas = colunas_limpar
    erros = []

    # Verificar e eliminar linhas com valores não numéricos
    for coluna in colunas:
        # Verifica se a coluna contém valores não numéricos
        if not pd.to_numeric(df[coluna], errors='coerce').notnull().all():
            # Registra as linhas com valores não numéricos para a coluna atual
            linhas_invalidas = df[pd.to_numeric(df[coluna], errors='coerce').isnull()]
            if not linhas_invalidas.empty:
                erros.append(f"{name_file}, linha {linhas_invalidas.index.tolist()[0]}: A coluna '{coluna}' deve conter apenas valores numéricos.")
            # Elimina linhas com valores não numéricos
            df = df[pd.to_numeric(df[coluna], errors='coerce').notnull()]
    return df, erros

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
        return False, f"{file_name}: Arquivo não foi encontrado em '{ultima_pasta}/{utimo_arquivo}'."
    return True, ""
