import pandas as pd
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

def check_unnamed_columns(df: pd.DataFrame, file_name: str):
    errors = []
    unnamed_columns_indices = []

    try:
        # Pré-processamento: Configura o header caso seja de múltiplos níveis
        if df.columns.nlevels == 2:
            df.columns = [str(col[1]).strip() for col in df.columns]

        # Verifica se há colunas sem nome
        for i, col in enumerate(df.columns):
            col_str = str(col).strip().lower()
            if col_str.startswith("unnamed"):
                unnamed_columns_indices.append(i)

        # Verificar as linhas que têm valores nessas colunas sem nome
        quantity_valid_columns = len(df.columns) - len(unnamed_columns_indices)

        for index, row in df.iterrows():
            # Caso a linha não seja vazia e tenha mais valores do que o número de colunas
            if pd.notnull(row).sum() > quantity_valid_columns:
                text_column = "coluna" if quantity_valid_columns == 1 else "colunas"
                errors.append(f"{file_name}, linha {index+2}: A linha possui {pd.notnull(row).sum()} valores, mas a tabela possui apenas {quantity_valid_columns} {text_column}.")
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a checagem de colunas sem nome: {str(e)}")

    return not errors, errors

