import os
import pandas as pd

def check_punctuation(df, name_file, columns_dont_punctuation=None, columns_must_end_with_dot=None):
    warnings = []
    # columns_dont_punctuation = ['nome_simples', 'nome_completo']
    # columns_must_end_with_dot = ['desc_simples', 'desc_completa']

    for index, row in df.iterrows():
        if columns_dont_punctuation is not None:
            for column in columns_dont_punctuation:
                text = row[column]
                # Verifique se o texto está vazio ou nan 
                if pd.isna(text) or text == "":
                    continue
                text = str(text).strip()
                if text[-1] in [',', '.', ';', ':', '!', '?']:
                    warnings.append(f"{name_file}, linha {index + 2}: A coluna '{column}' não deve terminar com pontuação.")
        
        if columns_must_end_with_dot is not None:
            for column in columns_must_end_with_dot:
                text = row[column]
                # Verifique se o texto está vazio ou nan 
                if pd.isna(text) or text == "":
                    continue
                text = str(text).strip()
                if text[-1] != '.':
                    warnings.append(f"{name_file}, linha {index + 2}: A coluna '{column}' deve terminar com ponto.")

    return not warnings, warnings

# check_unique_values:  Valores tem que ser unicos para as colunas especificadas
def check_unique_values(df, name_file, columns_uniques):
    warnings = []
    for column in columns_uniques:
        if not df[column].is_unique:
            warnings.append(f"{name_file}: A coluna '{column}' não deve conter valores repetidos.")
    return not warnings, warnings


'''
def dataframe_check_min_value(df, name_file, colunas_verificar):
    erros = []
    for coluna in colunas_verificar:
        # Verifica se a col
        if not (df[coluna] >= 0).all():
            # Linha onde existe o valor menor que zero
            linha_invalida = df[df[coluna] < 0].index.tolist()[0]            
            erros.append(f"{name_file}, linha {linha_invalida}: A coluna '{coluna}' deve conter apenas valores maiores ou iguais a zero.")
    return erros

'''

def dataframe_clean_numeric_values_less_than(df, name_file, colunas_limpar, value=0):
    erros = []

    for coluna in colunas_limpar:
        # Converte a coluna para numérico, forçando não numéricos a NaN
        df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

        # Encontra linhas com valores não numéricos ou menores que value (zero)
        linhas_invalidas = df[(df[coluna].isnull()) | (df[coluna] < value)]

        # Registra erros para valores não numéricos ou menores que zero
        for linha_invalida in linhas_invalidas.index:
            valor = df.at[linha_invalida, coluna]
            if pd.isnull(valor):
                erros.append(f"{name_file}, linha {linha_invalida + 2}: A coluna '{coluna}' contém um valor não numérico.")
            elif valor < value:
                erros.append(f"{name_file}, linha {linha_invalida + 2}: A coluna '{coluna}' contém um valor menor que {value}.")

    for coluna in colunas_limpar:
        # Converte a coluna para numérico, forçando não numéricos a NaN
        df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

        # Encontra linhas com valores não numéricos ou menores que zero
        linhas_invalidas = df[(df[coluna].isnull()) | (df[coluna] < value)]

        # Elimina linhas com valores não numéricos ou menores que zero
        df = df.drop(linhas_invalidas.index)

        # Muda as colunas para inteiros
        df[coluna] = df[coluna].astype(int)

    return df, erros

'''
# Função que limpa um dataframe de todas as linhas que contém valores não numéricos
def dataframe_clean_non_numeric_values(df, name_file, colunas_limpar):
    erros = []
    for coluna in colunas_limpar:
        # Converte a coluna para numérico, forçando não numéricos a NaN
        df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

        # Encontra linhas com valores não numéricos
        linhas_invalidas = df[df[coluna].isnull()]

        # Registra erros para valores não numéricos
        for linha_invalida in linhas_invalidas.index:
            erros.append(f"{name_file}, linha {linha_invalida + 2}: A coluna '{coluna}' contém um valor não numérico.")

    # Elimina linhas com valores não numéricos
    df = df.drop(linhas_invalidas.index)

    return df, erros
'''
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

"""
Barra vertical como caracter exclusivo do Adapta #87
O usuario nao pode usar | em nenhum arquivo de dados. Este caracter esta reservado para uso interno. Deve ser gerado erro toda vez que uma barra vertical for encontrada.
"""
def check_vertical_bar(df_sp, name_file):
    errors = []
    try:
        # Verificar se existe barra vertical
        for column in df_sp.columns:
            for index, row in df_sp.iterrows():
                if "|" in str(row[column]):
                    errors.append(f"{name_file}, linha {index + 2}: A coluna '{column}' não pode conter o caracter '|'.")
    except Exception as e:
        errors.append(f"Erro ao ler o arquivo {name_file}: {str(e)}")

    return not errors, errors

