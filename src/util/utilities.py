import os
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter

from pathlib import Path
import pandas as pd
import chardet

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_SCENARIO_COLUMNS, SP_PROPORTIONALITIES_COLUMNS, SP_LEGEND_COLUMNS
def agrupar_lista(lista):
    # Inicializando variáveis
    lista_agrupada = []
    grupo_atual = [lista[0]]  # Começa com o primeiro elemento da lista
    
    # Itera a partir do segundo elemento
    for elemento in lista[1:]:
        if elemento == grupo_atual[0]:
            # Se o elemento for igual ao primeiro do grupo atual, adiciona ao grupo
            grupo_atual.append(elemento)
        else:
            # Se for diferente, salva o grupo atual e começa um novo grupo
            lista_agrupada.append(grupo_atual)
            grupo_atual = [elemento]
    
    # Adiciona o último grupo à lista de agrupados
    lista_agrupada.append(grupo_atual)
    return lista_agrupada

def check_repetead_list(file_name, lista):

    # Contar as ocorrências de cada elemento na lista
    contagem = Counter(lista)

    # Verificar se há repetições e criar a lista de erros
    existe_repeticao = False
    lista_erros = []
    
    for item, count in contagem.items():
        if count > 1:
            existe_repeticao = True
            # lista_erros.append(f"{file_name}: O indicador '{item}' está repetido {count} vezes nas colunas.")
            lista_erros.append([item,count])

    return existe_repeticao, lista_erros


def get_min_max_legend(name_file, df_qml_legend):
        errors = []
        MIN_VALUE, MAX_VALUE = SP_LEGEND_COLUMNS.MIN_LOWER_LEGEND_DEFAULT, SP_LEGEND_COLUMNS.MAX_UPPER_LEGEND_DEFAULT

        # Verifica se o DataFrame está vazio
        if df_qml_legend.empty:
            errors.append(f"{name_file}: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos.")
            return errors, MIN_VALUE, MAX_VALUE
        
        # Converte as colunas UPPER e LOWER para float. Se tiver dado string, converte para NaN
        df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.LOWER], errors='coerce')
        df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.UPPER], errors='coerce')
        
        # Convert as colunas para float: lower e upper
        df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].astype(float)
        df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].astype(float)
        
        # Verifica se os valores são números
        for column in [SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER]:
            # Verifica se  ovalor é nan 
            if df_qml_legend[column].isnull().values.any():
                errors.append(f"{name_file}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                return errors, MIN_VALUE, MAX_VALUE
        
        MIN_VALUE, MAX_VALUE = get_min_max_values(df_qml_legend, SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER)

        # Convert to float
        MIN_VALUE = float(MIN_VALUE)
        MAX_VALUE = float(MAX_VALUE)
        # Verifica se os valores foram encontradoos são nan ou None
        if (MIN_VALUE is None or MAX_VALUE is None) or (pd.isna(MIN_VALUE) or pd.isna(MAX_VALUE)):
            
            errors.append(f"{name_file}: Verificação de valores foi abortada porque os valores do arquivo QML '{SP_LEGEND_COLUMNS.NAME_SP}' não foram encontrados.")
            return errors, MIN_VALUE, MAX_VALUE
        
        return errors, MIN_VALUE, MAX_VALUE
    
def check_tuple_sequence(value_list):
    errors = []
    
    for i in range(len(value_list) - 1):
        current_tuple = value_list[i]
        next_tuple = value_list[i + 1]
 
        VALOR_DIFF = round(next_tuple[0] - current_tuple[1], 2)

        VALOR_DIFF = int(VALOR_DIFF*10000)        

        if VALOR_DIFF != 100 or current_tuple[1] >= next_tuple[0]:
            errors.append("Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda.")
    return errors

def check_overlapping(file_name, df_qml_legend):
    errors = []
    
    df_qml_legend = df_qml_legend.copy()
    
    # Verifica se o DataFrame está vazio
    if df_qml_legend.empty:
        errors.append(f"{file_name}: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos.")
        return not errors, errors

    # Verifica se os valores são números
    for column in [SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER]:
        
        for index, value in df_qml_legend[column].items():
            # Verifica se o valor é uma string DI
            if value == "DI":
                continue

            if value is None or pd.isna(value.replace(',', '.')):
                errors.append(f"{file_name}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                continue

            # CORREÇÃO DOS VALORES FLUTUANTES
            value = value.replace(',', '.')
            
            # Converte value para um numero. Se não for possivel, retorna nan
            value = pd.to_numeric(value, errors='coerce')
            
            # Verifica se o valor é um número
            if pd.isna(value):
                errors.append(f"{file_name}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                return not errors, errors

    
    df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.LOWER], errors='coerce')
    df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.UPPER], errors='coerce')
    
    # Convert as colunas para float: lower e upper
    df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].astype(float)
    df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].astype(float)

    # Verifica se os valores estão em ordem crescente
    lower_values = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].tolist()
    upper_values = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].tolist()

    # Remove valores nulos nan
    lower_values = [x for x in lower_values if pd.notna(x)]
    upper_values = [x for x in upper_values if pd.notna(x)]

    # Verifica se as listas tem tamanho diferente
    if len(lower_values) != len(upper_values):
        errors.append(f"{file_name}: Arquivo está corrompido. Valores insuficientes para delimitar as fatias.")
        return not errors, errors
    
    
    # Verifica se os valores são válidos
    for _, row in df_qml_legend.iterrows():
        if row[SP_LEGEND_COLUMNS.LOWER] > row[SP_LEGEND_COLUMNS.UPPER]:
            errors.append(f"{file_name}: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda.")

    full_list = []
    for i in range(len(lower_values)):
        full_list.append(lower_values[i])
        full_list.append(upper_values[i])

    # Verifica se os valores estão em ordem crescente
    if full_list != sorted(full_list):
        errors.append(f"{file_name}: Arquivo está corrompido. Fatias não estão descritas na ordem crescente.")
        return not errors, errors

    try:
        # Verifica se os valores estão em ordem crescente
        errors_tuple = check_tuple_sequence(list(zip(lower_values, upper_values)))
        if errors_tuple: 
            for error in errors_tuple:
                errors.append(f'{file_name}: {error}')
            return not errors, errors

    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {file_name}: {e}.")
        return not errors, errors

    return not errors, errors


def truncate_number(x, precision):
    """ Trunca o valor 'x' à precisão especificada sem arredondamento. """
    # Se não tiver casas decimais, retorna o valor original
    if x == int(x):
        return x
    factor = 10 ** precision
    return math.trunc(x * factor) / factor

def extract_ids_from_list(list_values, values_scenario=[]):
    pattern_id_year = re.compile(r'^\d{1,}-\d{4}$')
    # Recebe uma lista values_scenario e adiciona ao final da expressão regular. Se recebeu ['M','O', 'P'] adiciona M|O|P
    pattern_id_year_scenario = re.compile(r'^\d{1,}-\d{4}-(?:' + '|'.join(values_scenario) + ')$')
    # Convert to string 
    list_values = [str(value) for value in list_values]
    values_scenario = [str(value) for value in values_scenario]

    # Extract IDs from list
    cleaned_columns = [column for column in list_values if pattern_id_year.match(column) or pattern_id_year_scenario.match(column)]
    extras_columns = [column for column in list_values if column not in cleaned_columns]

    return cleaned_columns, extras_columns

def read_legend_qml_file(qml_file_path):
    # Parse the QML file

    # Create a list to store the data
    data_list = []
    errors = []

    try: 
        tree = ET.parse(qml_file_path)
        root = tree.getroot()

        # For each child in the root
        for child in root:
            # Check if the child is the renderer-v2
            if child.tag == SP_LEGEND_COLUMNS.KEY_RENDERER_V2:
                
                # Get the ranges element
                ranges_element = child.find(SP_LEGEND_COLUMNS.KEY_RANGES)

                # Check if the ranges element exists
                if ranges_element is not None:

                    # Get all range elements
                    for range_element in ranges_element.findall(SP_LEGEND_COLUMNS.KEY_RANGE): 
                        uuid = range_element.get(SP_LEGEND_COLUMNS.UUID)
                        label = range_element.get(SP_LEGEND_COLUMNS.LABEL)
                        lower = range_element.get(SP_LEGEND_COLUMNS.LOWER)
                        upper = range_element.get(SP_LEGEND_COLUMNS.UPPER)
                        symbol = range_element.get(SP_LEGEND_COLUMNS.SYMBOL)
                        render = range_element.get(SP_LEGEND_COLUMNS.RENDER)
                        
                        # Append the data to the list
                        data_list.append({
                            SP_LEGEND_COLUMNS.UUID: uuid,
                            SP_LEGEND_COLUMNS.LABEL: label,
                            SP_LEGEND_COLUMNS.LOWER: lower,
                            SP_LEGEND_COLUMNS.UPPER: upper,
                            SP_LEGEND_COLUMNS.SYMBOL: symbol,
                            SP_LEGEND_COLUMNS.RENDER: render
                        })
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {qml_file_path}: {e}")
        return pd.DataFrame(), errors

    # Convert the list to a DataFrame
    df = pd.DataFrame(data_list, columns=[
        SP_LEGEND_COLUMNS.UUID, SP_LEGEND_COLUMNS.LABEL, SP_LEGEND_COLUMNS.LOWER,
        SP_LEGEND_COLUMNS.UPPER, SP_LEGEND_COLUMNS.SYMBOL, SP_LEGEND_COLUMNS.RENDER
    ])
    

    # Se não houver dados, adiciona no vetor erros que não foi encontrado dados
    if df.empty:
        errors.append(f"Erro ao processar o arquivo {qml_file_path}: Não foram encontrados dados.")

    # Remove a linha do dataframe cujo symbol == "Dado indisponivel"
    df = df[df[SP_LEGEND_COLUMNS.LABEL] != "Dado indisponível"]
    return df, errors

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
        # Verifica se a coluna existe no dataframe
        if coluna not in df.columns:
            erros.append(f"{name_file}: A coluna '{coluna}' não foi encontrada.")
            continue
       
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
            try: 
                df = pd.read_csv(path, sep=DEFAULT_SEPARATOR, encoding=ENCODING, low_memory=False, dtype=str)
            except Exception:
                return pd.DataFrame(), errors
            
        except Exception as e:
            errors.append(f"{filename}: Erro ao abrir o arquivo: {str(e)}")
            return pd.DataFrame(), errors
    elif file_extension == ".xlsx":
        try:
            df = pd.read_excel(path, dtype=str)
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
            try:            
                df = pd.read_csv(path, delimiter=DEFAULT_SEPARATOR, encoding=ENCODING, low_memory=False, dtype=str, header=[0, 1])
            except Exception:
                return pd.DataFrame(), errors

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
    # FIX COLUMN NAMES
    if not df.empty:
        # -------------------------------------------------------
        # REFACTOR THIS IN THE FUTURE: Corrige o dataframe para padronizar os nomes das colunas. No futoro, isso será feito uma ÚNICA VEZ em uma classe que irá processar os dados.
        parent_columns = []
        old_columns = df.columns.get_level_values(0)
        for col in old_columns:
            if col.startswith('Unnamed'):
                if parent_columns:
                    ultimo = parent_columns[-1]
                    parent_columns.append(ultimo)
                    continue

            parent_columns.append(col)
        df.columns = pd.MultiIndex.from_arrays([parent_columns, df.columns.get_level_values(1)])
        # -------------------------------------------------------
    return df, errors

def check_folder_exists(folder_path):
    try: 
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
    except Exception as e:
        return False, f"Erro ao verificar a pasta: {str(e)}"

def check_sp_file_exists(file_path):
    try: 
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
    except Exception as e:
        return False, f"Erro ao verificar se o arquivo existe: {str(e)}"


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
