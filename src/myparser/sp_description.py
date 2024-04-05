import os
import re

import pandas as pd
from src.myparser.text_processor import capitalize_text
from src.util.utilities import read_excel_file, dataframe_clean_numeric_values_less_than, check_file_exists
from src.util.utilities import check_punctuation, check_column_names, format_errors_and_warnings

def check_html_in_descriptions(path_sp_description, df):
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row['desc_simples'])):
            errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna desc_simples não pode conter código HTML.")
    return errors

def verify_sp_description_parser_html_column_names(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description)
        df.columns = df.columns.str.lower()

        html_errors = check_html_in_descriptions(path_sp_description, df)
        warnings.extend(html_errors)
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler a colunas do arquivo .xlsx: {e}")

    is_correct = len(errors) == 0
    return is_correct, errors, warnings

def verify_sp_description_titles_length(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description, True)
        for column in ['nome_simples']:
            # Verifica se a coluna existe
            if column not in df.columns:
                continue
            df[column] = df[column].str.strip()
            for index, row in df.iterrows():
                text = row[column]
                # Verifique se o texto está vazio ou nan 
                if pd.isna(text) or text == "":
                    continue
                    
                if len(text) > 30:
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: Até 30 caracteres. Encontrado: {len(row[column])} caracteres.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_titles_uniques(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description)
        # Renomear para as mcolunas nome_simples e nome_completo para nomes_simples e nomes_completos
        # Verifica se a coluna 'nome_simples' existe
        if 'nome_simples' in df.columns:
            df.rename(columns={'nome_simples': 'nomes_simples'}, inplace=True)
        if 'nome_completo' in df.columns:
            df.rename(columns={'nome_completo': 'nomes_completos'}, inplace=True)
        
        for column in ['nomes_simples', 'nomes_completos']:
            # Verifica se a coluna existe
            if column not in df.columns:
                continue
            # Convert to string
            df[column] = df[column].astype(str).str.strip()
            duplicated = df[column].duplicated().any()

            if duplicated:
                titles_duplicated = df[df[column].duplicated()][column].tolist()
                warnings.append(f"{os.path.basename(path_sp_description)}: Existem {column.replace('_', ' ')} duplicados: {titles_duplicated}.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings


def verify_sp_description_text_capitalize(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description)
        for index, row in df.iterrows():
            for column in ['nome_simples', 'nome_completo']:

                # Verifica se a coluna existe
                if column not in df.columns:
                    continue

                text = row[column]

                # Check if the text is empty or nan
                if pd.isna(text) or text == "":
                    continue

                # To str
                text = str(text)

                # Remove all \r and \n (x0D and x0A) and strip the text
                original_text = text.replace('\x0D', '<CR>').replace('\x0A', '<LF>')
                
                expected_corect_text = text.replace('\x0D', '').replace('\x0A', '').strip()
                expected_corect_text = capitalize_text(expected_corect_text)

                if not original_text == expected_corect_text:
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: \"{expected_corect_text}\". Encontrado: \"{original_text}\".")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_levels(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        
        df = read_excel_file(path_sp_description, True)
        name_file_description = os.path.basename(path_sp_description)
        # Verifica se a coluna 'nivel' existe
        if 'nivel' in df.columns:
            for index, row in df.iterrows():
                dig = str(row['nivel'])
                # Verifica se row['nivel'] é um digito inteiro maior que zero
                if not dig.isdigit() or int(row['nivel']) < 1:
                    errors.append(f"{name_file_description}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
    except Exception as e:
        errors.append(f"{name_file_description}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_punctuation(path_sp_description, columns_dont_punctuation, columns_must_end_with_dot): 
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []
    name_file = os.path.basename(path_sp_description)
    try:
        df = read_excel_file(path_sp_description, True)
        # Verifica se todas as colunas existem em df
        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]

        _, warnings = check_punctuation(df, name_file, columns_dont_punctuation, columns_must_end_with_dot)
        
    except Exception as e:
        errors.append(f"{name_file}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_codes_uniques(path_sp_description):
    errors, warnings = [], []
    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description, True)
        # Verifica se a coluna 'codigo' existe
        if 'codigo' in df.columns:
            # Limpar os dados
            df, _ = dataframe_clean_numeric_values_less_than(df, os.path.basename(path_sp_description), ['codigo'], 1)
            
            # Verificar se há códigos duplicados
            duplicated = df['codigo'].duplicated().any()
            if duplicated:
                codes_duplicated = df[df['codigo'].duplicated()]['codigo'].tolist()
                errors.append(f"{os.path.basename(path_sp_description)}: Existem códigos duplicados: {codes_duplicated}.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def  verify_sp_description_empty_strings(path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description, True)
        list_columns = [column for column in ['nome_simples', 'nome_completo', 'desc_simples', 'desc_completa'] if column in df.columns]

        for index, row in df.iterrows():

            for column in list_columns:
                if pd.isna(row[column]) or row[column] == "":
                    errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna '{column}' não pode ser vazia.")

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings


def verify_sp_description_cr_lf(path_sp_description, columns_start_end=[], columns_anywhere=[]):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)

    if errors:
        return False, errors, []

    try:
        df = read_excel_file(path_sp_description, True)
        # Item 1: Identificar CR e LF no final dos campos de texto
        for index, row in df.iterrows():
            
            for column in columns_start_end:
                # Verifica se a coluna existe
                if column not in df.columns:
                    continue

                text = row[column]
                # To srt 
                text = str(text)
                if pd.isna(text) or text == "":
                    continue
                if text.endswith('\x0D'):
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (CR) no final do texto.")
                if text.endswith('\x0A'):
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (LF) no final do texto.")
                
                if text.startswith('\x0D'):
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (CR) no início do texto.")
                if text.startswith('\x0A'):
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (LF) no início do texto.")
           
            # Item 2: Identificar CR e LF em qualquer lugar nos campos nome e título
            for column in columns_anywhere:
                text = row[column]
                text = str(text)
                if pd.isna(text) or text == "":
                    continue
                for match in re.finditer(r'[\x0D\x0A]', text):
                    char_type = "CR" if match.group() == '\x0D' else "LF"
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido ({char_type}) na posição {match.start() + 1}.")

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings
