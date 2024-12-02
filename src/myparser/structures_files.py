import os
import re 
import pandas as pd
import copy
from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe, check_vertical_bar
from src.util.utilities import check_column_names, format_errors_and_warnings
from src.util.utilities import  check_file_exists, extract_ids_from_list

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_LEGEND_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS


def verify_errors_read_files_in_folder_root(read_errors):
    warnings = []
    errors = []
    for error in read_errors:
        errors.append(error)
    return not errors, errors, warnings

def verify_not_exepected_files_in_folder_root(path_folder, STRUCTURE_FILES_COLUMNS_DICT):
    errors, warnings = [], []
    try:
        STRUCTURE_FILES_COLUMNS_DICT = STRUCTURE_FILES_COLUMNS_DICT.copy()
        
        # Verifica se dentro da pasta path_folder existe apenas 1 unica pasta
        lista_arquivos = [file_name for file_name in os.listdir(path_folder)]
        if len(lista_arquivos) == 1 and os.path.isdir(os.path.join(path_folder, lista_arquivos[0])):
            errors.append("Os arquivos não podem estar dentro de uma pasta. Eles devem ser zipados diretamente.")
            return not errors, errors, warnings

        NEW_STRUCTURE_FILES_COLUMNS_DICT = {}

        # Remove todas as execessões de arquivos esperados: STRUCTURE_FILES_COLUMNS_DICT
        for key in list(STRUCTURE_FILES_COLUMNS_DICT.keys()):
            new_key = key.replace(".csv", "").replace(".xlsx", "")
            NEW_STRUCTURE_FILES_COLUMNS_DICT[new_key] = STRUCTURE_FILES_COLUMNS_DICT[key]
        
        # Verifica se há arquivos não esperados na pasta
        lista_arquivos = [file_name for file_name in os.listdir(path_folder) if not file_name.endswith('.qml')]
        # Verifica se há arquivos não esperados na pasta
        for file_name_i in lista_arquivos:
            file_basename = os.path.basename(file_name_i)
            
            # Legenda QML é opcional
            if file_basename == SP_LEGEND_COLUMNS.NAME_SP:
                continue
            
            file_extension = os.path.splitext(file_basename)[1] 
            file_name_non_extension = file_basename.replace(file_extension, "")
            
            if file_name_non_extension not in NEW_STRUCTURE_FILES_COLUMNS_DICT:
                    # Verifica se é uma pasta ou um arquivo
                    if os.path.isdir(os.path.join(path_folder, file_name_i)):
                        errors.append(f"A pasta '{file_name_i}' não é esperada.")
                    else:
                        # Arquivos não esperados são tratados como erros
                        errors.append(f"O arquivo '{file_name_i}' não é esperado.")
    except Exception as e:
        errors.append(f"{path_folder}: Erro ao processar verificação dos arquivos da pasta principal: {e}.")

    return not errors, errors, warnings

def extract_ids_from_list_from_values(list_values, lista_cenarios):   
    # Extrai ids das colunas
    cleaned_columns, extras_columns = extract_ids_from_list(list_values, lista_cenarios)

    # Converte ambas as listas em strings
    cleaned_columns_str = []
    for id in cleaned_columns:
        cleaned_columns_str.append(str(id))
    
    extras_columns_str = []
    for id in extras_columns:
        extras_columns_str.append(str(id))

    # Remove os valores ID e NOME das colunas extras
    filtered_extras_columns = []
    for column in extras_columns_str:
        if column != SP_VALUES_COLUMNS.ID:
            filtered_extras_columns.append(column)

    extracted_ids = set()
    for id in cleaned_columns_str:
        code_level = id.split('-')[0]
        extracted_ids.add(code_level)

    # Remove os códigos repetidos e converte em inteiros
    ids_valids = set()
    for id in extracted_ids:
        ids_valids.add(int(id))

    return ids_valids, filtered_extras_columns
  
def verify_expected_structure_files(df, file_name, expected_columns, sp_scenario_exists=True, sp_proportionalities_exists=True, lista_simbolos_cenarios=[]):
    errors, warnings = [], []
    try:
        df = df.copy()
        # Se o df for none ou vazio retorna erro
        if df is None or df.empty:
            name_scnario = SP_SCENARIO_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
            name_proportionality = SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".csv","").replace(".xlsx","")
            file_name_non_extension = file_name.replace(".csv","").replace(".xlsx","")

            if (file_name_non_extension == name_scnario and not sp_scenario_exists) or (file_name_non_extension == name_proportionality and not sp_proportionalities_exists):
                return True, errors, warnings

            return False, errors, warnings
        
        # Quando não existir o arquivo de SP_SCENARIO_COLUMNS.NAME_SP, a coluna 'SP_DESCRIPTION_COLUMNS.CENARIO' não pode existir no arquivo de descrição
        if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP and not sp_scenario_exists:
                expected_columns = [column for column in expected_columns if column != SP_DESCRIPTION_COLUMNS.CENARIO]
                if SP_DESCRIPTION_COLUMNS.CENARIO in df.columns:
                    errors.append(f"{file_name}: A coluna '{SP_DESCRIPTION_COLUMNS.CENARIO}' não pode existir se o arquivo '{SP_SCENARIO_COLUMNS.NAME_SP}' não existir.")
                    df = df.drop(columns=[SP_DESCRIPTION_COLUMNS.CENARIO])
        
        # Corrige a coluna relacao
        if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP and (SP_DESCRIPTION_COLUMNS.RELACAO not in df.columns):
            # Cria a coluna relacao e preenche com 1
            df[SP_DESCRIPTION_COLUMNS.RELACAO] = 1
        
        # Corrige a coluna unidade
        if file_name == SP_DESCRIPTION_COLUMNS.NAME_SP and (SP_DESCRIPTION_COLUMNS.UNIDADE not in df.columns):
            # Cria a coluna unidade e preenche com vazio
            df[SP_DESCRIPTION_COLUMNS.UNIDADE] = ""

    
        # Check if there is a vertical bar in the column name
        is_error_vertical_bar, errors_vertical_bar = check_vertical_bar(df, file_name)
        errors.extend(errors_vertical_bar)
        level_one_columns = []
        if file_name == SP_PROPORTIONALITIES_COLUMNS.NAME_SP:
            level_one_columns = df.columns.get_level_values(0).unique().tolist()
            header_row = df.columns
            header_row = [str(col[1]).strip() for col in header_row]
            df.columns = header_row

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
            # Caso a linha não seja vaio e tenha mais valores do que o número de colunas
            if pd.notnull(row).sum() > quantity_valid_columns:
                text_column = "coluna" if quantity_valid_columns == 1 else "colunas"
                errors.append(f"{file_name}, linha {index+2}: A linha possui {pd.notnull(row).sum()} valores, mas a tabela possui apenas {quantity_valid_columns} {text_column}.")
        
        

        if file_name == SP_PROPORTIONALITIES_COLUMNS.NAME_SP:
            level_one_columns = [col for col in level_one_columns if not re.search(r'unnamed', col)]
            level_one_columns = [col for col in level_one_columns if not re.search(r'Unnamed', col)]

            # Level one columns
            ids_valids, extras_columns = extract_ids_from_list_from_values(level_one_columns, lista_simbolos_cenarios)
            for extra_column in extras_columns:
                if extra_column.lower().startswith("unnamed"):
                    continue
                errors.append(f"{file_name}: A coluna '{extra_column}' não é esperada.")

            # Level two columns
            level_two_columns = df.columns
            ids_valids, extras_columns = extract_ids_from_list_from_values(level_two_columns, lista_simbolos_cenarios)
            for extra_column in extras_columns:
                if extra_column.lower().startswith("unnamed"):
                    continue
                errors.append(f"{file_name}: A coluna '{extra_column}' não é esperada.")

            # Verifica se as colunas expected_columns foram encontradas em level_one_columns
            for col in expected_columns:
                if col not in level_two_columns:
                    errors.append(f"{file_name}: Coluna '{col}' esperada mas não foi encontrada.")


        elif file_name == SP_VALUES_COLUMNS.NAME_SP:
            ids_valids, extras_columns = extract_ids_from_list_from_values(df.columns, lista_simbolos_cenarios)
            for extra_column in extras_columns:
                if extra_column.lower().startswith("unnamed"):
                    continue
                errors.append(f"{file_name}: A coluna '{extra_column}' não é esperada.")
            for col in expected_columns:
                if col not in df.columns:
                    errors.append(f"{file_name}: Coluna '{col}' esperada mas não foi encontrada.")
        else:
            # Check missing columns expected columns and extra columns
            missing_columns, extra_columns = check_column_names(df, expected_columns)
            col_errors, col_warnings = format_errors_and_warnings(file_name, missing_columns, extra_columns)
            
            errors.extend(col_errors)
            warnings.extend(col_warnings)
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a verificação de estrutura do arquivo: {e}.")

    return not errors, errors, warnings
      
def verify_files_data_clean(df, file_name, columns_to_clean, value, sp_scenario_exists=True):
    errors, warnings = [], []
    try:
        df = df.copy()
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

            
        _, errors_data = clean_non_numeric_and_less_than_value_integers_dataframe(df, file_name, columns_to_clean, value)
        if errors_data:
            errors.extend(errors_data)
                
    except Exception as e:
        errors.append(f'{file_name}: Erro ao processar a verificação de limpeza do arquivo: {e}.')

    return not errors, errors, warnings

def verify_files_legends_qml(df_description, root_path):
    errors, warnings = [], []
    try:
        # Verifica a coluna nível em descrição
        if SP_DESCRIPTION_COLUMNS.NIVEL not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de legenda não realizada. Coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' não encontrada.")
            return not errors, errors, warnings
        
        files_qml = [f for f in os.listdir(root_path) if f.endswith('.qml')]
        len_files_qml = len(files_qml) - 1 
        
        # Caso 0: Não foi entregue nenhum arquivo QML
        if len(files_qml) == 0:
            return not errors, errors, warnings
        
        # Caso 1: Somento o arquivo de legenda SP_LEGEND_COLUMNS.NAME_SP foi entregue
        if len(files_qml) == 1 and files_qml[0] == SP_LEGEND_COLUMNS.NAME_SP:
            return not errors, errors, warnings
        
        # Caso 2: O arquivo de legenda SP_LEGEND_COLUMNS.NAME_SP fo entrege junto com outros arquivos QML
        if SP_LEGEND_COLUMNS.NAME_SP in files_qml:
            errors.append(f'{SP_LEGEND_COLUMNS.NAME_SP}: O arquivo {SP_LEGEND_COLUMNS.NAME_SP} foi entregue junto com os outros {len_files_qml} arquivos QML. Os outros arquivos serão ignorados.')
            return not errors, errors, warnings

        # Copiar files_qml com deepcopy, pois a lista files_qml será alterada
        copy_files_qml = copy.deepcopy(files_qml)
        
        # Caso 3: Apenas arquivos QML dos indicadores foram entregues
        df_description = df_description.copy()
        if df_description.empty: # Não continuar a verificação se o arquivo de descrição estiver vazio
            return not errors, errors, warnings
        if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns: # Não continuar a verificação se o arquivo de descrição não tiver a coluna de código
            return not errors, errors, warnings
        
        # No futuro essa função será removida, pois não iremos alterar os dados do usuário
        df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])
        
        codigos_indicadores_nivel_1 = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '1'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
        codigos_indicadores_nivel_2 = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '2'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
        codigos_indicadores_outros = [codigo for codigo in df_description[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist() if codigo not in codigos_indicadores_nivel_1 and codigo not in codigos_indicadores_nivel_2]
        
        for codigo in codigos_indicadores_outros:
            file_name = codigo + '.qml'
            path_legend = os.path.join(root_path, file_name)
            exist_file, __ = check_file_exists(path_legend)
            
            if not exist_file:
                errors.append(f'{file_name}: Arquivo de legenda esperado mas não encontrado.')
            else:
                copy_files_qml.remove(file_name)

        # Remove todos os codigos_indicadores_nivel_2 do copy_files_qml
        for codigo in codigos_indicadores_nivel_2:
            file_name = codigo + '.qml'
            if file_name in copy_files_qml:
                copy_files_qml.remove(file_name)
        # Arquivos extras
        for file_name in copy_files_qml:
            warnings.append(f'{file_name}: Arquivo de legenda não esperado.')
            
    except Exception as e:
        errors.append(f'{SP_LEGEND_COLUMNS.NAME_SP}: Erro ao processar a verificação dos arquivos QML: {e}.')
    
    return not errors, errors, warnings
