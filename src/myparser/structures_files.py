import os
import pandas as pd

from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe, check_vertical_bar
from src.util.utilities import check_column_names, format_errors_and_warnings
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

def verify_not_exepected_files_in_folder_root(path_folder, STRUCTURE_FILES_COLUMNS_DICT):
    errors = []
    warnings = []
    STRUCTURE_FILES_COLUMNS_DICT = STRUCTURE_FILES_COLUMNS_DICT.copy()

    NEW_STRUCTURE_FILES_COLUMNS_DICT = {}

    # Remove todas as execessões de arquivos esperados: STRUCTURE_FILES_COLUMNS_DICT
    for key in list(STRUCTURE_FILES_COLUMNS_DICT.keys()):
        new_key = key.replace(".csv", "").replace(".xlsx", "")
        NEW_STRUCTURE_FILES_COLUMNS_DICT[new_key] = STRUCTURE_FILES_COLUMNS_DICT[key]

    try:
        # Verifica se há arquivos não esperados na pasta
        for file_name_i in os.listdir(path_folder):
            file_basename = os.path.basename(file_name_i)
            file_extension = os.path.splitext(file_basename)[1] 
            file_name_non_extension = file_basename.replace(file_extension, "")
            
            if file_name_non_extension not in NEW_STRUCTURE_FILES_COLUMNS_DICT:
                    warnings.append(f"O arquivo '{os.path.basename(file_name_i)}' não é esperado.")

    except Exception as e:
        errors.append(f"{path_folder}: Erro ao processar verificação dos arquivos da pasta principal: {e}.")

    return not errors, errors, warnings
      
def verify_expected_structure_files(df, file_name, expected_columns, sp_scenario_exists=True, sp_proportionalities_exists=True):
    df = df.copy()
    errors = []
    warnings = []

    # Se o df for none ou vazio retorna erro
    if df is None or df.empty:
        name_scnario = SP_SCENARIO_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
        name_proportionality = SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
        file_name_non_extension = file_name.replace(".csv","").replace(".xlsx","")

        if (file_name_non_extension == name_scnario and not sp_scenario_exists) or (file_name_non_extension == name_proportionality and not sp_proportionalities_exists):
            return True, [], []

        return False, [], []
    
    # Quando não existir o arquivo de SP_SCENARIO_COLUMNS.NAME_SP, a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' não pode existir no arquivo de descrição
    if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP and not sp_scenario_exists:
            expected_columns = [column for column in expected_columns if column != SP_DESCRIPTION_COLUMNS.CENARIO]
            if SP_DESCRIPTION_COLUMNS.CENARIO in df.columns:
                errors.append(f"{file_name}: A coluna '{SP_DESCRIPTION_COLUMNS.CENARIO}' não pode existir se o arquivo '{SP_SCENARIO_COLUMNS.NAME_SP}' não existir.")
                df = df.drop(columns=[SP_DESCRIPTION_COLUMNS.CENARIO])
            
    try:
        # Check if there is a vertical bar in the column name
        is_error_vertical_bar, errors_vertical_bar = check_vertical_bar(df, file_name)
        errors.extend(errors_vertical_bar)
        
        # Fixing the header row of SP_PROPORTIONALITIES_COLUMNS.NAME_SP
        if file_name == SP_PROPORTIONALITIES_COLUMNS.NAME_SP:
            header_row = df.iloc[0]
            df.columns = header_row
            df = df[1:].reset_index(drop=True)

        unnamed_columns_indices = []

        # Verifica se há colunas sem nome
        for i, col in enumerate(df.columns):
            col_str = str(col).strip().lower()
            if col_str.startswith("unnamed"):
                unnamed_columns_indices.append(i)
                # Formatar mensagem de erro genérica
                # errors.append(f"{file_name}: Coluna número {i+1} não possui nome mas possui valores.")
        
        # Verificar as linhas que têm valores nessas colunas sem nome
        quantity_valid_columns = len(df.columns) - len(unnamed_columns_indices)
        for index, row in df.iterrows():
            for col_index in unnamed_columns_indices:
                if not pd.isna(row.iloc[col_index]) and str(row.iloc[col_index]).strip() != "":                    
                    # Verify plural = "coluna" or "colunas"
                    text_collumn = "coluna nomeada" if quantity_valid_columns == 1 else "colunas nomeadas"
                        
                    errors.append(f"{file_name}, linha {index+2}: A linha possui um valor na coluna {col_index+1}, que não possui nome. A tabela possui {quantity_valid_columns} {text_collumn}.")

        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(df, expected_columns)
        col_errors, col_warnings = format_errors_and_warnings(file_name, missing_columns, extra_columns)

        if file_name == SP_VALUES_COLUMNS.NAME_SP:
            errors.extend(col_errors)
        elif file_name == SP_PROPORTIONALITIES_COLUMNS.NAME_SP:
            errors.extend(col_errors)
        else:
            errors.extend(col_errors)
            warnings.extend(col_warnings)
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a verificação de estrutura do arquivo: {e}.")

    return not errors, errors, warnings
      
def verify_files_data_clean(df, file_name, columns_to_clean, value, sp_scenario_exists=True):
    df = df.copy()
    errors = []

    # Verifica se a tabela SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP tem apenas um valor
    if file_name == SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP:
        if (not sp_scenario_exists) and (len(df) != 1):
                errors.append(f"{file_name}: A tabela deve ter apenas um valor porque o arquivo {SP_SCENARIO_COLUMNS.NAME_SP} não existe.")
                return not errors, errors, []

    # Verifica se a tabela SP_SCENARIO_COLUMNS.NAME_SP tem apenas um valor
    if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP:
        if not sp_scenario_exists:
            columns_to_clean = [column for column in columns_to_clean if column != SP_DESCRIPTION_COLUMNS.CENARIO]

    missing_columns = set(columns_to_clean) - set(df.columns)
    missing_columns = [str(column) for column in missing_columns]
    if missing_columns:
        errors.append(f"{file_name}: A verificação de limpeza foi abortada para as colunas: {missing_columns}.")

    columns_to_clean = [column for column in columns_to_clean if column in df.columns]

    try:        
        _, errors_data = clean_non_numeric_and_less_than_value_integers_dataframe(df, file_name, columns_to_clean, value)
        if errors_data:
            errors.extend(errors_data)
                
    except Exception as e:
        errors.append(f'{file_name}: Erro ao processar a verificação de limpeza do arquivo: {e}.')

    return not errors, errors, []
