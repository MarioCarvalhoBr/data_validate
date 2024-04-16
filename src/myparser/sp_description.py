import re

import pandas as pd
from src.myparser.text_processor import capitalize_text
from src.util.utilities import dataframe_clean_numeric_values_less_than
from src.util.utilities import check_punctuation
from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS 


def check_html_in_descriptions(df):
    df = df.copy()
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row[SP_DESCRIPTION_COLUMNS.DESC_SIMPLES])):
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: Coluna desc_simples não pode conter código HTML.")
    return errors

def verify_sp_description_parser_html_column_names(df):
    df = df.copy()
    errors, warnings = [], []

    try:

        if SP_DESCRIPTION_COLUMNS.DESC_SIMPLES not in df.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Vericação de colunas HTML não realizada.")
            return False, errors, []

        df.columns = df.columns.str.lower()

        html_errors = check_html_in_descriptions(df)
        warnings.extend(html_errors)
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao ler a colunas do arquivo .xlsx: {e}")

    is_correct = len(errors) == 0
    return is_correct, errors, warnings

def verify_sp_description_titles_length(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        # Convert columns to lowercase
        df.columns = df.columns.str.lower()

        for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES]:

            if column not in df.columns:
                continue
            
            df[column] = df[column].str.strip()

            for index, row in df.iterrows():
                text = row[column]
                # Verifique se o texto está vazio ou nan 
                if pd.isna(text) or text == "":
                    continue
                    
                if len(text) > 30:
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: Até 30 caracteres. Encontrado: {len(row[column])} caracteres.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_titles_uniques(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        # Rename columns to plural
        if SP_DESCRIPTION_COLUMNS.NOME_SIMPLES in df.columns:
            df.rename(columns={SP_DESCRIPTION_COLUMNS.NOME_SIMPLES: SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_SIMPLES}, inplace=True)
        if SP_DESCRIPTION_COLUMNS.NOME_COMPLETO in df.columns:
            df.rename(columns={SP_DESCRIPTION_COLUMNS.NOME_COMPLETO: SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_COMPLETOS}, inplace=True)
        
        for column in [SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_SIMPLES, SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_COMPLETOS]:
            
            # Verifica se a coluna existe
            if column not in df.columns:
                continue
            
            # Convert to string
            df[column] = df[column].astype(str).str.strip()
            duplicated = df[column].duplicated().any()

            if duplicated:
                titles_duplicated = df[df[column].duplicated()][column].tolist()
                warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Existem {column.replace('_', ' ')} duplicados: {titles_duplicated}.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings


def verify_sp_description_text_capitalize(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        for index, row in df.iterrows():
            for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]:

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
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: \"{expected_corect_text}\". Encontrado: \"{original_text}\".")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_levels(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        if SP_DESCRIPTION_COLUMNS.NIVEL in df.columns:            
            for index, row in df.iterrows():
                dig = str(row[SP_DESCRIPTION_COLUMNS.NIVEL])
                dig = dig.replace('.0', '')
                if not dig.isdigit() or int(row[SP_DESCRIPTION_COLUMNS.NIVEL]) < 1:
                    errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
    
    
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot): 
    df = df.copy()
    errors, warnings = [], []

    try:
        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]

        _, warnings = check_punctuation(df, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_dont_punctuation, columns_must_end_with_dot)
        
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_codes_uniques(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        if SP_DESCRIPTION_COLUMNS.CODIGO in df.columns:
            df, _ = dataframe_clean_numeric_values_less_than(df, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1)
            
            duplicated = df[SP_DESCRIPTION_COLUMNS.CODIGO].duplicated().any()
            if duplicated:
                codes_duplicated = df[df[SP_DESCRIPTION_COLUMNS.CODIGO].duplicated()][SP_DESCRIPTION_COLUMNS.CODIGO].tolist()
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Existem códigos duplicados: {codes_duplicated}.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def  verify_sp_description_empty_strings(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        list_columns = [column for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA] if column in df.columns]
        for index, row in df.iterrows():

            for column in list_columns:
                if pd.isna(row[column]) or row[column] == "":
                    errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: Nenhum item da coluna '{column}' pode ser vazio.")

    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings


def verify_sp_description_cr_lf(df, file_name,  columns_start_end=[], columns_anywhere=[]):
    df = df.copy()
    # Salva o df em um arquivo novo_df.xlsx
    errors, warnings = [], []

    try:
        # Item 1: Identificar CR e LF no final dos campos de texto
        for index, row in df.iterrows():
            
            for column in columns_start_end:
                # Verifica se a coluna existe
                if column in df.columns:
                    text = row[column]
                    # To srt 
                    text = str(text)
                    if pd.isna(text) or text == "":
                        continue
                    if text.endswith('\x0D'):
                        warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (CR) no final do texto.")
                    if text.endswith('\x0A'):
                        warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (LF) no final do texto.")
                    
                    if text.startswith('\x0D'):
                        warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (CR) no início do texto.")
                    if text.startswith('\x0A'):
                        warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido (LF) no início do texto.")
           
            # Item 2: Identificar CR e LF em qualquer lugar nos campos nome e título
            for column in columns_anywhere:
                # Verifica se a coluna existe
                if column in df.columns:
                    text = row[column]
                    text = str(text)

                    if pd.isna(text) or text == "":
                        continue
                    for match in re.finditer(r'[\x0D\x0A]', text):
                        char_type = "CR" if match.group() == '\x0D' else "LF"
                        warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido ({char_type}) na posição {match.start() + 1}.")

    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings
