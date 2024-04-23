import re

import pandas as pd
from src.myparser.text_processor import capitalize_text_keep_acronyms
from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe
from src.util.utilities import check_punctuation, check_values_integers
from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_DESCRIPTION_MAX_TITLE_LENGTH

def check_html_in_descriptions(df, column):
    df = df.copy()
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row[column])):
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: Coluna desc_simples não pode conter código HTML.")
    return errors

def verify_sp_description_parser_html_column_names(df, column):
    df = df.copy()
    errors, warnings = [], []

    if column not in df.columns:
        warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos HTML nas descrições simples foi abortada porque a coluna '{column}' está ausente.")
        return not errors, errors, warnings

    try:
        df.columns = df.columns.str.lower()
        html_errors = check_html_in_descriptions(df, column)
        warnings.extend(html_errors)
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação do arquivo: {e}.")

    is_correct = len(errors) == 0
    return is_correct, errors, warnings

def verify_sp_description_titles_length(df):
    df = df.copy()
    errors, warnings = [], []
    
    column = SP_DESCRIPTION_COLUMNS.NOME_SIMPLES
    if column not in df.columns:
        warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres foi abortada porque a coluna '{column}' está ausente.")
        return not errors, errors, warnings

    try:
        df.columns = df.columns.str.lower()
        df[column] = df[column].str.strip()

        for index, row in df.iterrows():
            text = row[column]
            if pd.isna(text) or text == "":
                continue
                
            if len(text) > SP_DESCRIPTION_MAX_TITLE_LENGTH:
                warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: Até {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres. Encontrado: {len(row[column])} caracteres.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_titles_uniques(df):
    df = df.copy()
    errors, warnings = [], []

    try:
        for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]:
            
            # Verifica se a coluna existe
            if column not in df.columns:
                warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de títulos únicos foi abortada porque a coluna '{column}' está ausente.")
                continue
            
            # Convert to string
            df[column] = df[column].astype(str).str.strip()
            duplicated = df[column].duplicated().any()

            if duplicated:
                titles_duplicated = df[df[column].duplicated()][column].tolist()
                # Rename columns to plural
                if column == SP_DESCRIPTION_COLUMNS.NOME_SIMPLES:
                    column = SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_SIMPLES
                elif column == SP_DESCRIPTION_COLUMNS.NOME_COMPLETO:
                    column = SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_COMPLETOS

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
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de padrões para nomes dos indicadores foi abortada porque a coluna '{column}' está ausente.")
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
                    warnings.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: \"{expected_corect_text}\". Encontrado: \"{original_text}\".")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_levels(df):
    df = df.copy()
    errors, warnings = [], []

    # Verifica se a coluna existe
    if SP_DESCRIPTION_COLUMNS.NIVEL not in df.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de níveis de indicadores foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' está ausente.")
        return not errors, errors, warnings
    
    try:
        for index, row in df.iterrows():
            dig = row[SP_DESCRIPTION_COLUMNS.NIVEL]
            is_correct, msg = check_values_integers(dig, 1)
            if not is_correct:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
                continue
            if dig < 1:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {index + 2}: Nível do indicador não é um número inteiro maior que 0.")
    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_description_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot): 
    df = df.copy()
    errors, warnings = [], []

    try:
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
    df = df.copy()
    errors, warnings = [], []

    if SP_DESCRIPTION_COLUMNS.CODIGO not in df.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos únicos foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
        return not errors, errors, warnings

    try:
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
        for column in list_columns:
            # Verifica se a coluna existe
            if column not in df.columns:
                errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de campos vazios foi abortada porque a coluna '{column}' está ausente.")
                continue
            # Localiza linhas onde a coluna é NaN ou vazia (string vazia)
            empty_mask = df[column].isna() | (df[column] == "")
            if empty_mask.any():
                # Usa o numpy para obter os índices diretamente, que é mais rápido que iterrows
                empty_indices = empty_mask[empty_mask].index + 1  # +1 para ajustar o índice para ser baseado em 1
                errors.extend([f"{SP_DESCRIPTION_COLUMNS.NAME_SP}, linha {idx}: Nenhum item da coluna '{column}' pode ser vazio." for idx in empty_indices])

    except Exception as e:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")


    return not errors, errors, warnings

def verify_sp_description_cr_lf(df, file_name,  columns_start_end=[], columns_anywhere=[]):
    df = df.copy()
    # Salva o df em um arquivo novo_df.xlsx
    errors, warnings = [], []

    missing_columns = set(columns_start_end + columns_anywhere) - set(df.columns)
    missing_columns = [str(column) for column in missing_columns]
    if missing_columns:
        warnings.append(f"{file_name}: A verificação de CR e LF foi abortada para as colunas: {missing_columns}.")

    columns_start_end_fixed = [column for column in columns_start_end if column in df.columns]
    columns_anywhere_fixed = [column for column in columns_anywhere if column in df.columns]

    try:
        # Item 1: Identificar CR e LF no final dos campos de texto
        for index, row in df.iterrows():
            
            for column in columns_start_end_fixed:
                text = str(row[column])

                # Dont check empty strings
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
            for column in columns_anywhere_fixed:
                text = str(row[column])

                # Dont check empty strings
                if pd.isna(text) or text == "":
                    continue

                for match in re.finditer(r'[\x0D\x0A]', text):
                    char_type = "CR" if match.group() == '\x0D' else "LF"
                    warnings.append(f"{file_name}, linha {index + 1}: O texto da coluna {column} possui um caracter inválido ({char_type}) na posição {match.start() + 1}.")

    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings
