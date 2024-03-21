import os
import re

import pandas as pd
from src.myparser.text_processor import capitalize_text
from src.util.utilities import read_excel_file, dataframe_clean_numeric_values_less_than, check_file_exists
from src.util.utilities import check_punctuation

def check_html_in_descriptions(path_sp_description, df):
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row['desc_simples'])):
            errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna desc_simples não pode conter código HTML.")
    return errors

def check_column_names(df, expected_columns):
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]
    return missing_columns, extra_columns

def format_errors_and_warnings(name, missing_columns, extra_columns):
    errors = [f"{name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
    warnings = [f"{name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
    return errors, warnings

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

        expected_columns = ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"]
        missing_columns, extra_columns = check_column_names(df, expected_columns)
        col_errors, col_warnings = format_errors_and_warnings(os.path.basename(path_sp_description), missing_columns, extra_columns)
        
        errors.extend(col_errors)
        warnings.extend(col_warnings)

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler a coluna desc_simples do arquivo .xlsx: {e}")

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
        df = read_excel_file(path_sp_description, True)
        # Renomear para as mcolunas nome_simples e nome_completo para nomes_simples e nomes_completos
        df.rename(columns={'nome_simples': 'nomes_simples', 'nome_completo': 'nomes_completos'}, inplace=True)
        for column in ['nomes_simples', 'nomes_completos']:
            df[column] = df[column].str.strip()
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
        df = read_excel_file(path_sp_description, True)
        for index, row in df.iterrows():
            for column in ['nome_simples', 'nome_completo']:
                original_text = row[column]
                # Verifique se o texto está vazio ou nan 
                if pd.isna(original_text) or original_text == "":
                    original_text = ""
                expected_corect_text = capitalize_text(original_text)
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
        for index, row in df.iterrows():
            if pd.isna(row['nome_simples']) or row['nome_simples'] == "":
                errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna 'nome_simples' não pode ser vazia.")
            if pd.isna(row['nome_completo']) or row['nome_completo'] == "":
                errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna 'nome_completo' não pode ser vazia.")
            if pd.isna(row['desc_simples']) or row['desc_simples'] == "":
                errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna 'desc_simples' não pode ser vazia.")
            if pd.isna(row['desc_completa']) or row['desc_completa'] == "":
                errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Coluna 'desc_completa' não pode ser vazia.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

'''
Nova função para verificar se os campos de texto possuem CR e LF: 
TAREFA: 
    - Remover #$0D, #$0A (CR, LF) dos campos texto #85

FAZER:
    - Na tabela de descrição dos indicadores, identificar em todos os campos texto os caracteres CR e LF que estiverem no fim do texto.
    - Nos campos nome e título, identificar se ocorrerem em qualquer lugar do texto.
    - Gerar um warning em ambos os casos dizendo em que posição estavam os caracteres que foram identificados.
'''
def verify_sp_description_cr_lf(path_sp_description):
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
            for column in ['desc_simples', 'desc_completa']:
                text = row[column]
                if pd.isna(text) or text == "":
                    continue
                if text.endswith('\x0D') or text.endswith('\x0A'):
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui CR ou LF no final do texto.")

            # Item 2: Identificar CR e LF em qualquer lugar nos campos nome e título
            for column in ['nome_simples', 'nome_completo']:
                text = row[column]
                if pd.isna(text) or text == "":
                    continue
                for match in re.finditer(r'[\x0D\x0A]', text):
                    char_type = "CR" if match.group() == '\x0D' else "LF"
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: O texto da coluna {column} possui {char_type} na posição {match.start() + 1}.")

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

'''
Exemplo de texto com CR e LF:
Texto 1 CR: "Texto com CR\x0D"
Texto 2 LF: "Texto com LF\x0A"
'''
