import re

import pandas as pd
from src.myparser.text_processor import capitalize_text_keep_acronyms
from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe
from src.util.utilities import check_punctuation, check_values_integers
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_DESCRIPTION_MAX_TITLE_LENGTH, SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH

def check_html_in_descriptions(df, column):
    df = df.copy()
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row[column])):
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Coluna desc_simples não pode conter código HTML.")
    return errors

def verify_sp_description_parser_html_column_names(df, column):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings
        
        if column not in df.columns:
            warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos HTML nas descrições simples foi abortada porque a coluna '{column}' está ausente.")
            return not errors, errors, warnings

    
        df.columns = df.columns.str.lower()
        html_errors = check_html_in_descriptions(df, column)
        warnings.extend(html_errors)
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação do arquivo: {e}.")

    return not errors, errors, warnings

def verify_sp_description_codes_sequential(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings
        # 0. Check if the column exists
        if SP_DESCRIPTION_COLUMNS.CODIGO not in df.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos sequenciais foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
            return not errors, errors, warnings

    
        df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1)
        
        # 1. Check if the column has only integers
        if erros:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos sequenciais foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' contém valores inválidos.")
            return not errors, errors, warnings
        
        # 2. Check if the first code is 1
        if df[SP_DESCRIPTION_COLUMNS.CODIGO].iloc[0] != 1:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: A coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' deve começar em 1.")

        # 3. Check if the codes are sequential
        codes = df[SP_DESCRIPTION_COLUMNS.CODIGO].tolist()
        if codes != list(range(codes[0], codes[-1] + 1)):
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: A coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' deve conter valores sequenciais (1, 2, 3, ...).")

    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_text_capitalize(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings
        
        for index, row in df.iterrows():
            for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]:

                if column not in df.columns:
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de padrões para nomes dos indicadores foi abortada porque a coluna '{column}' não está ausente.")
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
                expected_corect_text = capitalize_text_keep_acronyms(expected_corect_text)

                if not original_text == expected_corect_text:
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: \"{expected_corect_text}\". Encontrado: \"{original_text}\".")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    # Remove dados repetidos de warnings
    warnings = list(dict.fromkeys(warnings))
    return not errors, errors, warnings

def verify_sp_description_levels(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        # Verifica se a coluna existe
        if SP_DESCRIPTION_COLUMNS.NIVEL not in df.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de níveis de indicadores foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' está ausente.")
            return not errors, errors, warnings
    
    
        for index, row in df.iterrows():
            dig = row[SP_DESCRIPTION_COLUMNS.NIVEL]
            is_correct, msg = check_values_integers(dig, 1)
            if not is_correct:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
                continue
            dig = int(dig)
            if dig < 1:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        columns_dont_punctuation_fixed = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot_fixed = [column for column in columns_must_end_with_dot if column in df.columns]

        # Verifica todas as colunas que estão ausentes em df.columns
        missing_columns_dont_punctuation = [column for column in columns_dont_punctuation if column not in df.columns]
        missing_columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column not in df.columns]

        # Set de colunas que não estão presentes no df.columns
        missing_columns = set(missing_columns_dont_punctuation + missing_columns_must_end_with_dot)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: A verificação de pontuações obrigatórias e proibidas foi abortada para as colunas: {missing_columns}.")
        
        _, warnings = check_punctuation(df, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_dont_punctuation_fixed, columns_must_end_with_dot_fixed)
        
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_codes_uniques(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        if SP_DESCRIPTION_COLUMNS.CODIGO not in df.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos únicos foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
            return not errors, errors, warnings

        df, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1)
        
        duplicated = df[SP_DESCRIPTION_COLUMNS.CODIGO].duplicated().any()
        if duplicated:
            codes_duplicated = df[df[SP_DESCRIPTION_COLUMNS.CODIGO].duplicated()][SP_DESCRIPTION_COLUMNS.CODIGO].tolist()
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Existem códigos duplicados: {codes_duplicated}.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_empty_strings(df, list_columns=[]):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        for column in list_columns:
            # Verifica se a coluna existe
            if column not in df.columns:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de campos vazios foi abortada porque a coluna '{column}' está ausente.")
                continue
            # Localiza linhas onde a coluna é NaN ou vazia (string vazia)
            empty_mask = df[column].isna() | (df[column] == "")
            if empty_mask.any():
                # Usa o numpy para obter os índices diretamente, que é mais rápido que iterrows
                empty_indices = empty_mask[empty_mask].index + 2  # +1 para ajustar o índice para ser baseado em 1
                errors.extend([f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {idx}: Nenhum item da coluna '{column}' pode ser vazio." for idx in empty_indices])

    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")


    return not errors, errors, warnings

def verify_sp_description_cr_lf(df, file_name,  columns_start_end=[], columns_anywhere=[]):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        # Verifica se a coluna RELACAO está presente no df
        if SP_DESCRIPTION_COLUMNS.RELACAO not in df.columns:
            columns_start_end = [column for column in columns_start_end if column != SP_DESCRIPTION_COLUMNS.RELACAO]
            columns_anywhere = [column for column in columns_anywhere if column != SP_DESCRIPTION_COLUMNS.RELACAO]
        
        # Verifica se a coluna UNIDADE está presente no df
        if SP_DESCRIPTION_COLUMNS.UNIDADE not in df.columns:
            columns_start_end = [column for column in columns_start_end if column != SP_DESCRIPTION_COLUMNS.UNIDADE]
            columns_anywhere = [column for column in columns_anywhere if column != SP_DESCRIPTION_COLUMNS.UNIDADE]

        # Verifica todas as colunas que estão ausentes em df.columns
        missing_columns = set(columns_start_end + columns_anywhere) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            warnings.append(f"{file_name}: A verificação de CR e LF foi abortada para as colunas: {missing_columns}.")

        # Filtra as colunas que estão presentes em df.columns
        columns_start_end_fixed = [column for column in columns_start_end if column in df.columns]
        columns_anywhere_fixed = [column for column in columns_anywhere if column in df.columns]

        # Item 1: Identificar CR e LF no final dos campos de texto
        for index, row in df.iterrows():
            
            for column in columns_start_end_fixed:
                text = str(row[column])

                # Dont check empty strings
                if pd.isna(text) or text == "":
                    continue

                if text.endswith('\x0D'):
                    warnings.append(f"{file_name}, linha {index + 2}: O texto da coluna {column} possui um caracter inválido (CR) no final do texto. Remova o último caractere do texto.")
                if text.endswith('\x0A'):
                    warnings.append(f"{file_name}, linha {index + 2}: O texto da coluna {column} possui um caracter inválido (LF) no final do texto. Remova o último caractere do texto.")
                
                if text.startswith('\x0D'):
                    warnings.append(f"{file_name}, linha {index + 2}: O texto da coluna {column} possui um caracter inválido (CR) no início do texto. Remova o primeiro caractere do texto.")
                if text.startswith('\x0A'):
                    warnings.append(f"{file_name}, linha {index + 2}: O texto da coluna {column} possui um caracter inválido (LF) no início do texto. Remova o primeiro caractere do texto.")
           
            # Item 2: Identificar CR e LF em qualquer lugar nos campos nome e título
            for column in columns_anywhere_fixed:
                text = str(row[column])

                # Dont check empty strings
                if pd.isna(text) or text == "":
                    continue

                for match in re.finditer(r'[\x0D\x0A]', text):
                    char_type = "CR" if match.group() == '\x0D' else "LF"
                    warnings.append(f"{file_name}, linha {index + 2}: O texto da coluna {column} possui um caracter inválido ({char_type}) na posição {match.start() + 1}. Remova o caractere do texto.")

    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_titles_length(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings
        
        column = SP_DESCRIPTION_COLUMNS.NOME_SIMPLES
        if column not in df.columns:
            warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres foi abortada porque a coluna '{column}' está ausente.")
            return not errors, errors, warnings

        df.columns = df.columns.str.lower()
        df[column] = df[column].str.strip()

        for index, row in df.iterrows():
            text = row[column]
            if pd.isna(text) or text == "":
                continue
                
            if len(text) > SP_DESCRIPTION_MAX_TITLE_LENGTH: 
                warnings.append(f'{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: "{text}". {column.replace("_", " ").capitalize()} fora do padrão. Esperado: Até {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres. Encontrado: {len(row[column])} caracteres.')
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_simple_description_max_length(df):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        column = SP_DESCRIPTION_COLUMNS.DESC_SIMPLES
        if column not in df.columns:
            warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de descrições simples com mais de {SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH} caracteres foi abortada porque a coluna '{column}' está ausente.")
            return not errors, errors, warnings

        df.columns = df.columns.str.lower()
        df[column] = df[column].str.strip()

        for index, row in df.iterrows():
            text = row[column]
            
            if pd.isna(text) or text == "":
                continue
                
            if len(text) > SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH:
                warnings.append(f'{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: "{text}". Descrição simples fora do padrão. Esperado: Até {SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH} caracteres. Encontrado: {len(row[column])} caracteres.')
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings
