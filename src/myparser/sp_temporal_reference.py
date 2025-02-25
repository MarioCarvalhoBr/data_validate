from src.util.utilities import check_punctuation, check_unique_values
import datetime
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_TEMPORAL_REFERENCE_COLUMNS

def verify_sp_temporal_reference_unique_values(df, columns_uniques):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        missing_columns = set(columns_uniques) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: A verificação de relações de valores únicos foi abortada para as colunas: {missing_columns}.")

        columns_uniques = [column for column in columns_uniques if column in df.columns]

        _, errors_checkeds = check_unique_values(df, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_uniques)
        errors.extend(errors_checkeds) 
    except Exception as e:
        errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_temporal_reference_punctuation(df, columns_dont_punctuation, columns_must_end_with_dot): 
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings

        missing_columns = set(columns_dont_punctuation + columns_must_end_with_dot) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            warnings.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: A verificação de pontuação foi abortada para as colunas: {missing_columns}.")

        columns_dont_punctuation = [column for column in columns_dont_punctuation if column in df.columns]
        columns_must_end_with_dot = [column for column in columns_must_end_with_dot if column in df.columns]
    
        _, warnings = check_punctuation(df, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_dont_punctuation, columns_must_end_with_dot)  
    except Exception as e:
        errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_sp_temporal_reference_years(df_temporal_reference):
    errors, warnings = [], []
    CURRENT_YEAR = datetime.datetime.now().year

    try:
        df_temporal_reference = df_temporal_reference.copy()
        if df_temporal_reference.empty:
            return True, errors, warnings

        if SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO not in df_temporal_reference.columns:
            return True, errors, warnings

        # Remover a primeira linha do dataframe df_temporal_reference
        df_temporal_reference = df_temporal_reference.iloc[1:]

        # Get all years
        years = df_temporal_reference[SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO].unique()

        # Check if all years are greater than the current year
        for year in years:
            # Verifica se year é um número inteiro válido
            try:
                year = int(year)
            except ValueError:
                errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O valor {year} não é um número inteiro válido.")
                continue            
            if year <= CURRENT_YEAR:
                errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.")
    except Exception as e:
        errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

