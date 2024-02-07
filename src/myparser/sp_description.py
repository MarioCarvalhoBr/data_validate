import os
import re
from src.myparser.text_processor import capitalize_text
from src.util.utilities import read_excel_file, file_extension_check

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

    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

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
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_file(path_sp_description, True)
        for column in ['nome_simples']:
            df[column] = df[column].str.strip()
            for index, row in df.iterrows():
                if len(row[column]) > 30:
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: Até 30 caracteres. Encontrado: {len(row[column])} caracteres.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_titles_uniques(path_sp_description):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

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
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_file(path_sp_description, True)
        for index, row in df.iterrows():
            for column in ['nome_simples', 'nome_completo']:
                original_text = row[column]
                expected_corect_text = capitalize_text(original_text)
                if not original_text == expected_corect_text:
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: {column.replace('_', ' ').capitalize()} fora do padrão. Esperado: \"{expected_corect_text}\". Encontrado: \"{original_text}\".")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_levels(path_sp_description):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_file(path_sp_description, True)
        for index, row in df.iterrows():
            if row['nivel'] < 1:
                errors.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: Nível do indicador não pode ser menor que 1.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings

def verify_sp_description_punctuation(path_sp_description):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_sp_description)
    if not is_correct:
        errors.append(error)
        return is_correct, errors, warnings

    try:
        df = read_excel_file(path_sp_description, True)
        for index, row in df.iterrows():
            for column in ['nome_simples', 'nome_completo']:
                if row[column][-1] in [',', '.', ';', ':', '!', '?']:
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: A coluna '{column}' não deve terminar com pontuação.")
            for column in ['desc_simples', 'desc_completa']:
                if row[column][-1] != '.':
                    warnings.append(f"{os.path.basename(path_sp_description)}, linha {index + 1}: A coluna '{column}' deve terminar com ponto.")
    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    return not errors, errors, warnings
