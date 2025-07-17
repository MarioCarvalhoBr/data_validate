import re
from typing import List, Tuple, Dict, Any
import pandas as pd

def check_vertical_bar(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
    df_copy = dataframe.copy()
    errors: list = []

    try:
        if isinstance(df_copy.columns, pd.MultiIndex):
            for col_tuple in df_copy.columns:
                # Nível 0
                if '|' in str(col_tuple[0]):
                    errors.append(f"{file_name}: O nome da coluna de nível 0 '{col_tuple[0]}' não pode conter o caracter '|'.")
                # Nível 1
                if len(col_tuple) > 1 and '|' in str(col_tuple[1]):
                    errors.append(f"{file_name}: O nome da subcoluna de nível 1 '{col_tuple[1]}' do pai '{col_tuple[0]}' de nível 0 não pode conter o caracter '|'.")
        else:
            for column_name in df_copy.columns:
                if '|' in str(column_name):
                    errors.append(f"{file_name}: A coluna '{column_name}' não pode conter o caractere '|'.")

        # Verifica se há barra vertical nos dados das colunas
        mask = df_copy.map(lambda x: '|' in str(x) if pd.notna(x) else False)
        if mask.any().any():
            for column in df_copy.columns:
                if mask[column].any():
                    rows_with_error = mask.index[mask[column]].tolist()
                    col_display_name = str(column) if not isinstance(column, tuple) else ".".join(map(str, column))
                    for row in rows_with_error:
                        errors.append(f"{file_name}, linha {row + 2}: A coluna '{col_display_name}' não pode conter o caracter '|'.")
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a checagem de barra vertical: {str(e)}")

    return not errors, errors

def check_unnamed_columns(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
    df_copy = dataframe.copy() # Work on a copy to avoid any modification to the original
    errors: List[str] = []
    unnamed_columns_indices: List[int] = []

    try:
        columns_to_iterate = df_copy.columns
        is_multi_level_2 = isinstance(columns_to_iterate, pd.MultiIndex) and columns_to_iterate.nlevels == 2

        for i, col_original_identifier in enumerate(columns_to_iterate):
            col_str_to_check: str
            if is_multi_level_2:
                # Se for um MultiIndex de 2 níveis, a lógica original efetivamente verificava o segundo nível.
                col_str_to_check = str(col_original_identifier[1]).strip().lower()
            else:
                # Para SingleIndex ou MultiIndex que não seja de 2 níveis, verifica a representação em string do identificador da coluna.
                col_str_to_check = str(col_original_identifier).strip().lower()

            if col_str_to_check.startswith("unnamed"):
                unnamed_columns_indices.append(i)

        quantity_total_columns = len(columns_to_iterate)
        quantity_valid_columns = quantity_total_columns - len(unnamed_columns_indices)

        for index, row in df_copy.iterrows():
            if pd.notna(row).sum() > quantity_valid_columns:
                text_column = "coluna válida" if quantity_valid_columns == 1 else "colunas válidas"
                errors.append(f"{file_name}, linha {index+2}: A linha possui {pd.notna(row).sum()} valores, mas a tabela possui apenas {quantity_valid_columns} {text_column}.")
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a checagem de colunas sem nome: {str(e)}")

    return not errors, errors


def check_punctuation(df, file_name, columns_dont_punctuation=None, columns_must_end_with_dot=None):
    warnings = []
    if columns_dont_punctuation is None:
        columns_dont_punctuation = []
    if columns_must_end_with_dot is None:
        columns_must_end_with_dot = []

    columns_dont_punctuation = [col for col in columns_dont_punctuation if col in df.columns]
    columns_must_end_with_dot = [col for col in columns_must_end_with_dot if col in df.columns]

    for index, row in df.iterrows():
        for column in columns_dont_punctuation:
            text = row[column]
            if pd.isna(text) or text == "":
                continue
            text = str(text).strip()
            if text[-1] in [',', '.', ';', ':', '!', '?']:
                warnings.append(
                    f"{file_name}, linha {index + 2}: O valor da coluna '{column}' não deve terminar com pontuação.")

        for column in columns_must_end_with_dot:
            text = row[column]
            if pd.isna(text) or text == "":
                continue
            text = str(text).strip()
            if text[-1] != '.':
                warnings.append(
                    f"{file_name}, linha {index + 2}: O valor da coluna '{column}' deve terminar com ponto.")

    return not warnings, warnings


def _check_special_characters_cr_lf_columns_start_end(df, file_name, columns_start_end=None):
    warnings = []
    if columns_start_end is None:
        columns_start_end = []

    # Filter existing columns
    columns_start_end = [col for col in columns_start_end if col in df.columns]

    # Check CR/LF at start and end
    for column in columns_start_end:
        mask = df[column].notna() & (df[column] != "")
        if not mask.any():
            continue

        text_series = df.loc[mask, column].astype(str)

        # Check end positions
        end_cr_mask = text_series.str.endswith('\x0D')
        end_lf_mask = text_series.str.endswith('\x0A')

        # Check start positions
        start_cr_mask = text_series.str.startswith('\x0D')
        start_lf_mask = text_series.str.startswith('\x0A')

        # Generate warnings
        for idx in text_series[end_cr_mask].index:
            warnings.append(f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido (CR) no final do texto. Remova o último caractere do texto.")

        for idx in text_series[end_lf_mask].index:
            warnings.append(f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido (LF) no final do texto. Remova o último caractere do texto.")

        for idx in text_series[start_cr_mask].index:
            warnings.append(f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido (CR) no início do texto. Remova o primeiro caractere do texto.")

        for idx in text_series[start_lf_mask].index:
            warnings.append(f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido (LF) no início do texto. Remova o primeiro caractere do texto.")

    return not warnings, warnings

def _check_special_characters_cr_lf_columns_anywhere(df, file_name, columns_anywhere=None):
    warnings = []

    if columns_anywhere is None:
        columns_anywhere = []

    # Filter existing columns
    columns_anywhere = [col for col in columns_anywhere if col in df.columns]

    # Check CR/LF anywhere in text
    for column in columns_anywhere:
        mask = df[column].notna() & (df[column] != "")
        if not mask.any():
            continue

        text_series = df.loc[mask, column].astype(str)

        # Use apply for regex search (more complex logic)
        def find_cr_lf_positions(text):
            positions = []
            for match in re.finditer(r'[\x0D\x0A]', text):
                char_type = "CR" if match.group() == '\x0D' else "LF"
                positions.append((match.start() + 1, char_type))
            return positions

        cr_lf_positions = text_series.apply(find_cr_lf_positions)

        for idx, positions in cr_lf_positions.items():
            for pos, char_type in positions:
                warnings.append(
                    f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido ({char_type}) na posição {pos}. Remova o caractere do texto.")

    return not warnings, warnings

def check_special_characters_cr_lf(df, file_name, columns_start_end=None, columns_anywhere=None):
    df = df.copy()
    all_warnings = []

    # Check for CR/LF at start and end of specified columns
    valid, warnings_start_end = _check_special_characters_cr_lf_columns_start_end(df, file_name, columns_start_end)
    if not valid:
        all_warnings.extend(warnings_start_end)

    # Check for CR/LF anywhere in specified columns
    valid, warnings_anywhere = _check_special_characters_cr_lf_columns_anywhere(df, file_name, columns_anywhere)
    if not valid:
        all_warnings.extend(warnings_anywhere)

    return not all_warnings, all_warnings

def check_unique_values(df: pd.DataFrame, file_name: str, columns_uniques: list):
    warnings = []

    columns_uniques = [column for column in columns_uniques if column in df.columns]

    for column in columns_uniques:
        if not df[column].is_unique:
            warnings.append(f"{file_name}: A coluna '{column}' não deve conter valores repetidos.")
    return not warnings, warnings

def column_exists(dataframe, file_name, column) -> Tuple[bool, str]:
    if column not in dataframe.columns:
        return False, f"{file_name}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente."
    return True, ""

def check_text_length(dataframe, file_name, column, max_len) -> Tuple[List[str], List[str]]:
        """Helper function to validate text length in a column."""
        errors = []
        exists_column, msg_error_column = column_exists(dataframe, file_name, column)
        if not exists_column:
            return [msg_error_column], []
        for index, row in dataframe.iterrows():
            text = str(row[column])
            if pd.isna(text):
                continue
            if len(text) > max_len:
                errors.append(f'{file_name}, linha {index + 2}: O texto da coluna "{column}" excede o limite de {max_len} caracteres (encontrado: {len(text)}).')
        return not errors, errors