import os

from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe, check_vertical_bar
from src.util.utilities import check_column_names, format_errors_and_warnings
# Spreadsheets classes and constants
from src.myparser.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

# GLOBAL VARIABLES
# Estrutura esperada de colunas para cada arquivo
STRUCTURE_FILES_COLUMNS_DICT = {
    SP_SCENARIO_COLUMNS.NAME_SP: [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO, SP_SCENARIO_COLUMNS.SIMBOLO],
    SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO],
    
    SP_DESCRIPTION_COLUMNS.NAME_SP: [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META],
    
    SP_COMPOSITION_COLUMNS.NAME_SP: [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO],
    SP_VALUES_COLUMNS.NAME_SP: [SP_VALUES_COLUMNS.ID, SP_VALUES_COLUMNS.NOME],
    SP_PROPORTIONALITIES_COLUMNS.NAME_SP: [SP_PROPORTIONALITIES_COLUMNS.ID, SP_PROPORTIONALITIES_COLUMNS.NOME]
}

STRUCTURE_FILES_TO_CLEAN_LIST = [
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1], # CORRIGIR para 0.x
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NIVEL], 1],
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CENARIO], -1],
    
    [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0],
    [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1],
    
    [SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO], 0]
]

def verify_not_exepected_files_in_folder_root(path_folder):
    errors = []
    warnings = []
    try:
        # Verifica se há arquivos não esperados na pasta
        for file_name_i in os.listdir(path_folder):
            if file_name_i not in STRUCTURE_FILES_COLUMNS_DICT and os.path.isfile(os.path.join(path_folder, file_name_i)):
                warnings.append(f"O arquivo '{file_name_i}' não é esperado.")

    except Exception as e:
        errors.append(f"{path_folder}: Erro ao processar verificação dos arquivos da pasta principal: {e}.")

    return not errors, errors, warnings
      
def verify_expected_structure_files(df, file_name, expected_columns, sp_scenario_exists=True, sp_proportionalities_exists=True):
    df = df.copy()
    errors = []
    warnings = []

    # Se o df for none ou vazio retorna erro
    if df is None or df.empty:
        if not (file_name == SP_SCENARIO_COLUMNS.NAME_SP or file_name == SP_PROPORTIONALITIES_COLUMNS.NAME_SP):
            errors.append(f"{file_name}: O arquivo esperado não foi encontrado ou está vazio.")
        return not errors, errors, warnings
    
    # Quando não existir o arquivo de SP_SCENARIO_COLUMNS.NAME_SP, a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' não pode existir no arquivo de descrição
    if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP and not sp_scenario_exists:
            # Remove a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' da lista de colunas esperadas
            expected_columns = [column for column in expected_columns if column != SP_DESCRIPTION_COLUMNS.CENARIO]
            # Verifica se a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' existe no arquivo
            if SP_DESCRIPTION_COLUMNS.CENARIO in df.columns:
                errors.append(f"{file_name}: A coluna '{SP_DESCRIPTION_COLUMNS.CENARIO}' não pode existir se o arquivo '{SP_SCENARIO_COLUMNS.NAME_SP}' não existir.")
                # Remove a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' do dataframe
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

        # Verifica se há colunas sem nome
        for i, col in enumerate(df.columns):
            col = str(col).strip().lower()
            if col.startswith("unnamed") or col.startswith("Unnamed"):
                # Formatar mensagem de erro
                errors.append(f"{file_name}: Coluna número {i+1} não possui nome mas possui valores.")
                
    
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
