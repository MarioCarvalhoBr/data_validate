import os
import pandas as pd
import re
from src.util.text_processor import capitalize_nouns_keep_articles_prepositions

def file_extension_check(path, extension='.xlsx'):
    if not path.endswith(extension):
        return False, f"ERRO: O arquivo {path} de entrada não é {extension}"
    return True, ""

def read_excel_and_lower_columns(path):
    df = pd.read_excel(path)
    df.columns = df.columns.str.lower()
    return df

def is_xlsx_file(path):
    return path.endswith('.xlsx')

def load_dataframe(path):
    return pd.read_excel(path)

def check_html_in_descriptions(df):
    errors = []
    for index, row in df.iterrows():
        if re.search('<.*?>', str(row['desc_simples'])):
            errors.append(f"Erro na linha {index + 1}. Coluna desc_simples não pode conter código HTML.")
    return errors

def check_column_names(df, expected_columns):
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]
    return missing_columns, extra_columns

def format_errors_and_warnings(name, missing_columns, extra_columns):
    errors = [f"{name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
    warnings = [f"{name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
    return errors, warnings

def verify_sp_description_parser(path_sp_description):
    errors, warnings = [], []

    if not is_xlsx_file(path_sp_description):
        return False, [f"ERRO: O arquivo {path_sp_description} de entrada não é .xlsx"], warnings

    try:
        df = load_dataframe(path_sp_description)
        df.columns = df.columns.str.lower()

        html_errors = check_html_in_descriptions(df)
        errors.extend(html_errors)

        expected_columns = ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"]
        missing_columns, extra_columns = check_column_names(df, expected_columns)
        col_errors, col_warnings = format_errors_and_warnings(os.path.basename(path_sp_description), missing_columns, extra_columns)
        
        errors.extend(col_errors)
        warnings.extend(col_warnings)

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler a coluna desc_simples do arquivo .xlsx: {e}")

    is_correct = len(errors) == 0
    return is_correct, errors, warnings


def verify_sp_description_titles_uniques(path_sp_description):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_and_lower_columns(path_sp_description)
        for column in ['nome_simples', 'nome_completo']:
            df[column] = df[column].str.strip()
            duplicated = df[column].duplicated().any()
            if duplicated:
                errors.append(f"{os.path.basename(path_sp_description)}: Existem {column.replace('_', ' ')} duplicados.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings


def verify_sp_description_text_capitalize(path_sp_description):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_and_lower_columns(path_sp_description)
        for index, row in df.iterrows():
            for column in ['nome_simples', 'nome_completo']:
                original_text = row[column]
                corrected_text = capitalize_nouns_keep_articles_prepositions(original_text)
                if original_text != corrected_text:
                    warnings.append(f"{os.path.basename(path_sp_description)}: {column.replace('_', ' ')} na linha {index + 1} está fora do padrão. Esperado: \"{corrected_text}\" Encontrado: \"{original_text}\"")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings
