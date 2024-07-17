import os
import math
import re

from pathlib import Path
import pandas as pd
import chardet

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_SCENARIO_COLUMNS, SP_PROPORTIONALITIES_COLUMNS

def truncate_number(x, precision):
    """ Trunca o valor 'x' à precisão especificada sem arredondamento. """
    # Se não tiver casas decimais, retorna o valor original
    if x == int(x):
        return x
    factor = 10 ** precision
    return math.trunc(x * factor) / factor

def extract_ids_from_list(list_values):
    pattern_id_year = re.compile(r'^\d{1,}-\d{4}$')
    pattern_id_year_scenario = re.compile(r'^\d{1,}-\d{4}-(O|P)$')
    # Convert to string 
    list_values = [str(value) for value in list_values]

    # Extract IDs from list
    cleaned_columns = [column for column in list_values if pattern_id_year.match(column) or pattern_id_year_scenario.match(column)]
    extras_columns = [column for column in list_values if column not in cleaned_columns]

    return cleaned_columns, extras_columns


def get_min_max_values(df, key_lower, key_upper):
    min_value = df[key_lower].min()
    max_value = df[key_upper].max()

    return min_value, max_value

def generate_list_combinations(codigo, primeiro_ano, lista_simbolos_temporais, lista_simbolos_cenarios):
    # Create list of combinations
    lista_combinacoes = []
    lista_combinacoes.append(f"{codigo}-{primeiro_ano}")
    
    # Remove first element
    lista_simbolos_temporais.pop(0)
    for ano in lista_simbolos_temporais:
        for simbolo in lista_simbolos_cenarios:
            lista_combinacoes.append(f"{codigo}-{ano}-{simbolo}")
    return lista_combinacoes

def get_last_directory_name(path):
    return Path(path).name

def create_directory(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)
        
def check_column_names(df, expected_columns):
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]
    return missing_columns, extra_columns

def format_errors_and_warnings(name, missing_columns, extra_columns):
    errors = [f"{name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
    warnings = [f"{name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
    return errors, warnings

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

def check_unique_values(df, name_file, columns_uniques):
    warnings = []
    for column in columns_uniques:
        if not df[column].is_unique:
            warnings.append(f"{name_file}: A coluna '{column}' não deve conter valores repetidos.")
    return not warnings, warnings

def check_values_integers(number, min_value=0):
    try:
        # Verifica se e um NaN do pandas 
        if pd.isna(number) or math.isnan(float(number)) or float(number) != int(float(number)):
            if not float(number).is_integer():
                return False, f"O valor '{number}' não é um número inteiro."
            return False, f"O valor '{number}' não é um número."
        
        if int(number) < min_value:
            return False, f"O valor '{number}' é menor que {min_value}."

        return True, "O valor é um número inteiro."

    except Exception:
        return False, f"O valor '{number}' não é um número."

def clean_non_numeric_and_less_than_value_integers_dataframe(df, name_file, colunas_limpar, min_value=0):
    df = df.copy()
    erros = []

    for coluna in colunas_limpar:

        # Lista de índices para remover
        indices_para_remover = []
       
        for index, row in df.iterrows():
            cell = row[coluna]
            # Replace , to .
            if isinstance(cell, str):
                cell = cell.replace(',', '.')
            is_correct, msg = check_values_integers(cell, min_value)
            if not is_correct:
                # Linha
                erros.append(f"{name_file}, linha {index + 2}: A coluna '{coluna}' contém um valor inválido: {msg}")
                indices_para_remover.append(index)

        # Remover linhas inválidas
        df.drop(indices_para_remover, inplace=True)
        # Ajusta o índice
        # df.reset_index(drop=True, inplace=True)

        # Converte a coluna para inteiro
        if not df[coluna].empty:
            
            df[coluna] = df[coluna].astype(int)
    
    return df, erros
    
def file_extension_check(path, extension='.xlsx'):
    if not path.endswith(extension):
        return False, f"ERRO: O arquivo {path} de entrada não é {extension}"
    return True, ""

# Função para detectar a codificação de um arquivo lendo apenas a primeira linha
def detect_encoding(file_path, num_bytes=1024):
    with open(file_path, 'rb') as f:
        raw_data = f.read(num_bytes)
        result = chardet.detect(raw_data)
        return result['encoding']


def read_excel_file(path):
    DEFAULT_SEPARATOR = '|'
    ENCODING = 'utf-8'
    errors = []

    # Checa se o arquivo existe
    if not os.path.exists(path):
        # errors.append(f"O arquivo {path} não foi encontrado.")
        return pd.DataFrame(), errors

    file_extension = os.path.splitext(path)[1].lower()
    filename = os.path.basename(path)

    if file_extension == ".csv":
        try:
            file_encoding = detect_encoding(path)
            if not any(enc in file_encoding.lower() for enc in ['ascii', 'utf-8']):
                errors.append(f"{filename}: O arquivo está no formato {file_encoding}, deveria ser UTF-8.")
                return pd.DataFrame(), errors
            
            df = pd.read_csv(path, sep=DEFAULT_SEPARATOR, encoding=ENCODING, low_memory=False)
            
        except Exception as e:
            errors.append(f"{filename}: Erro ao abrir o arquivo: {str(e)}")
            return pd.DataFrame(), errors
    elif file_extension == ".xlsx":
        try:
            df = pd.read_excel(path)
        except Exception as e:
            errors.append(f"{filename}: Erro ao abrir o arquivo: {str(e)}")
            return pd.DataFrame(), errors
    else:
        errors.append(f"{filename}: Tipo de arquivo não suportado: {file_extension}")
        return pd.DataFrame(), errors
    
    return df, errors

def read_file_proporcionalites(path):
    """ Lê o arquivo de entrada (CSV ou Excel) e retorna um DataFrame. """
    DEFAULT_SEPARATOR = '|'
    ENCODING = 'utf-8'
    errors = []

    filename = os.path.basename(path)

    # Checa se o arquivo existe
    if not os.path.exists(path):
        # errors.append(f"O arquivo {path} não foi encontrado.")
        return pd.DataFrame(), errors
    
    file_extension = os.path.splitext(path)[1].lower()

    if file_extension == ".csv":
        try:
            file_encoding = detect_encoding(path)
            if not any(enc in file_encoding.lower() for enc in ['ascii', 'utf-8']):
                errors.append(f"{filename}: O arquivo está no formato {file_encoding}, deveria ser UTF-8.")
                return pd.DataFrame(), errors
            
            df = pd.read_csv(path, delimiter=DEFAULT_SEPARATOR, encoding=ENCODING, low_memory=False, dtype=str, header=[0, 1])

        except Exception as e:
            errors.append(f"{filename}: Erro ao abrir o arquivo: {str(e)}")
            return pd.DataFrame(), errors
    elif file_extension == ".xlsx":
        try:
            df = pd.read_excel(path, header=[0, 1], dtype=str)
        except Exception as e:
            errors.append(f"{filename}: Erro ao abrir o arquivo: {str(e)}")
            return pd.DataFrame(), errors
    else:
        errors.append(f"{filename}: Tipo de arquivo não suportado: {file_extension}")
        return pd.DataFrame(), errors
    
    return df, errors

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

def check_sp_file_exists(file_path):
    is_csv = False
    is_xlsx = False
    file_name = os.path.basename(file_path)
    file_name = file_name.replace(".xlsx", "").replace(".csv", "") + ".csv"

    file_path_non_extension = os.path.splitext(file_path)[0]

    path_file_csv = file_path_non_extension + ".csv"
    path_file_xlsx = file_path_non_extension + ".xlsx"

    if os.path.exists(path_file_csv):
        is_csv = True
    if os.path.exists(path_file_xlsx):
        is_xlsx = True

    ultima_pasta = os.path.basename(os.path.dirname(file_path))

    # Se não encontrou nenhum dos dois
    if not is_csv and not is_xlsx:
        name_scnario = SP_SCENARIO_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
        name_proportionality = SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
        file_name_non_extension = file_name.replace(".csv","").replace(".xlsx","")

        if file_name_non_extension == name_scnario or file_name_non_extension == name_proportionality:
            return False, is_csv, is_xlsx, []
        return False, is_csv, is_xlsx, [f"{file_name}: O arquivo esperado não foi encontrado."]
    if is_csv and is_xlsx:
        return True, is_csv, is_xlsx, [f"{file_name}: Existe um arquivo .csv e um arquivo .xlsx com o mesmo nome. Será considerado o arquivo .csv."]
    
    return True, is_csv, is_xlsx, []


def check_file_exists(file_path):
    errors = []
    exists_file = False
    if os.path.exists(file_path):
        exists_file = True
    else: 
        errors.append(f"O arquivo {os.path.basename(file_path)} não foi encontrado.")
    
    return exists_file, errors


def check_vertical_bar(df_sp, name_file):
    errors = []

    try:
        # Verifica se há barra vertical nos nomes das colunas
        for column in df_sp.columns:
            column = str(column)
            if '|' in column:
                errors.append(f"{name_file}: O nome da coluna '{column}' não pode conter o caracter '|'.")

        # Verifica se há barra vertical nos dados das colunas
        mask = df_sp.map(lambda x: '|' in str(x) if pd.notna(x) else False)
        if mask.any().any():
            for column in df_sp.columns:
                if mask[column].any():
                    # Encontra linhas específicas com o problema
                    rows_with_error = mask.index[mask[column]].tolist()
                    for row in rows_with_error:
                        errors.append(f"{name_file}, linha {row + 2}: A coluna '{column}' não pode conter o caracter '|'.")
    
    except Exception as e:
        errors.append(f"{name_file}: Erro ao processar a checagem de barra vertical: {str(e)}")

    return not errors, errors
