import pandas as pd
from typing import List, Tuple # Added for type hinting clarity

def check_vertical_bar(dataframe: pd.DataFrame, name_file: str) -> Tuple[bool, List[str]]:
    df_copy = dataframe.copy()
    errors: list = []

    try:
        if isinstance(df_copy.columns, pd.MultiIndex):
            for col_tuple in df_copy.columns:
                # Nível 0
                if '|' in str(col_tuple[0]):
                    errors.append(f"{name_file}: O nome da coluna de nível 0 '{col_tuple[0]}' não pode conter o caracter '|'.")
                # Nível 1
                if len(col_tuple) > 1 and '|' in str(col_tuple[1]):
                    errors.append(f"{name_file}: O nome da subcoluna de nível 1 '{col_tuple[1]}' do pai '{col_tuple[0]}' de nível 0 não pode conter o caracter '|'.")
        else:
            for column_name in df_copy.columns:
                if '|' in str(column_name):
                    errors.append(f"{name_file}: A coluna '{column_name}' não pode conter o caractere '|'.")

        # Verifica se há barra vertical nos dados das colunas
        mask = df_copy.map(lambda x: '|' in str(x) if pd.notna(x) else False)
        if mask.any().any():
            for column in df_copy.columns:
                if mask[column].any():
                    rows_with_error = mask.index[mask[column]].tolist()
                    col_display_name = str(column) if not isinstance(column, tuple) else ".".join(map(str, column))
                    for row in rows_with_error:
                        errors.append(f"{name_file}, linha {row + 2}: A coluna '{col_display_name}' não pode conter o caracter '|'.")
    except Exception as e:
        errors.append(f"{name_file}: Erro ao processar a checagem de barra vertical: {str(e)}")

    return not errors, errors

def check_unnamed_columns(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
    df_copy = dataframe.copy() # Work on a copy to avoid any modification to the original
    errors: List[str] = []
    unnamed_columns_indices: List[int] = []

    try:
        # Não há pré-processamento que modifica df_copy.columns aqui.
        # Determina a string a ser verificada para "unnamed" com base na estrutura da coluna.

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

        # quantity_valid_columns é baseada no número original de colunas.
        quantity_total_columns = len(columns_to_iterate)
        quantity_valid_columns = quantity_total_columns - len(unnamed_columns_indices)

        # Verificar as linhas que têm valores nessas colunas "unnamed" (ou mais valores que colunas válidas)
        # A iteração é sobre df_copy, que mantém sua estrutura de colunas original (não achatada)
        for index, row in df_copy.iterrows():
            # pd.notna(row).sum() conta os valores não nulos na linha.
            if pd.notna(row).sum() > quantity_valid_columns:
                text_column = "coluna válida" if quantity_valid_columns == 1 else "colunas válidas"
                # A mensagem de erro original foi mantida, implicando que colunas "unnamed" não são contadas como válidas.
                errors.append(f"{file_name}, linha {index+2}: A linha possui {pd.notna(row).sum()} valores, mas a tabela possui apenas {quantity_valid_columns} {text_column}.")
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a checagem de colunas sem nome: {str(e)}")

    return not errors, errors