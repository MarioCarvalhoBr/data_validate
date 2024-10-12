from src.util.utilities import check_punctuation, check_unique_values
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_SCENARIO_COLUMNS

def verify_sp_scenario_unique_values(df, columns_uniques):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        missing_columns = set(columns_uniques) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]    
        if missing_columns:
            errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: A verificação de relações de valores únicos foi abortada para as colunas: {missing_columns}.")

        columns_uniques = [column for column in columns_uniques if column in df.columns]


        _, errors_checkeds = check_unique_values(df, SP_SCENARIO_COLUMNS.NAME_SP, columns_uniques)
        errors.extend(errors_checkeds) 
    except Exception as e:
        errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_scenario_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot): 
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        missing_columns = set(columns_dont_punctuation + columns_must_end_with_dot) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            warnings.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: A verificação de pontuação foi abortada para as colunas: {missing_columns}.")

        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]
        
        _, warnings = check_punctuation(df, SP_SCENARIO_COLUMNS.NAME_SP, columns_dont_punctuation, columns_must_end_with_dot)
    except Exception as e:
        errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")
    
    return not errors, errors, warnings
