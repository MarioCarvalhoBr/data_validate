from src.util.utilities import check_punctuation, check_unique_values
from src.myparser.structures_files import SP_SCENARIO_COLUMNS 

def verify_sp_scenario_unique_values(df, columns_uniques):
    df = df.copy()
    errors, warnings = [], []

    try:
        # Veriificar se todas as colunas existem em df
        columns_uniques = [column for column in columns_uniques if column in df.columns]
        _, errors_checkeds = check_unique_values(df, SP_SCENARIO_COLUMNS.NAME_SP, columns_uniques)
        errors.extend(errors_checkeds)
        
    except Exception as e:
        errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_scenario_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot): 
    df = df.copy()
    errors, warnings = [], []

  
    try:
        # Verifica se todas as colunas existem em df
        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]

        _, warnings = check_punctuation(df, SP_SCENARIO_COLUMNS.NAME_SP, columns_dont_punctuation, columns_must_end_with_dot)
        
    except Exception as e:
        errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings
