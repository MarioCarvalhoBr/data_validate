from decimal import Decimal

import pandas as pd

from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS
from src.util.utilities import truncate_number, clean_non_numeric_and_less_than_value_integers_dataframe, check_values_integers, extract_ids_from_list

def build_subdatasets(df, file_path):
    parent_columns = df.columns.get_level_values(0)
    
    if file_path.endswith('.xlsx'):
        return create_subdatasets_xlsx(df, parent_columns)
    elif file_path.endswith('.csv'):
        return create_subdatasets_csv(df, parent_columns)
    else:
        return None

def create_subdatasets_xlsx(df, parent_columns):
    """ Cria subdatasets a partir de um arquivo Excel. """
    unique_parents = [col for col in parent_columns[1:] if 'Unnamed' not in col]
    subdatasets = {'main': df.iloc[:, :1]}
    
    for parent_id in unique_parents:
        start_col = (parent_columns == parent_id).argmax()
        if start_col + 1 == len(parent_columns):
            end_col = start_col + 1
        else:
            end_col = (parent_columns[start_col + 1:] != parent_id).argmax() + start_col + 1
            if end_col == start_col + 1:
                end_col = len(parent_columns)

        columns_to_include = df.columns[:1].tolist() + df.columns[start_col:end_col].tolist()
        subdatasets[parent_id] = df.loc[:, columns_to_include]
        
    return subdatasets

def create_subdatasets_csv(df, parent_columns):
    """ Cria subdatasets a partir de um arquivo CSV. """
    unique_parents = []
    for col in parent_columns[1:]:
        if not col.startswith('Unnamed'):
            unique_parents.append(col)
    
    subdatasets = {'main': df.iloc[:, :1]}

    for parent_id in unique_parents:
        start_col = parent_columns.get_loc(parent_id)
        end_col = start_col + 1

        while end_col < len(parent_columns) and parent_columns[end_col].startswith('Unnamed'):
            end_col += 1
        
        columns_to_include = df.columns[:1].tolist() + df.columns[start_col:end_col].tolist()
        subdatasets[parent_id] = df.loc[:, columns_to_include]
    
    return subdatasets

def check_sum_equals_one(subdatasets):
    errors = []
    warnings = []

    has_more_than_3_decimal_places = False

    for parent_id, subdataset in subdatasets.items():
        # Se o ID pai for 'main', pula para o próximo subdataset
        if parent_id == 'main':
            continue
        
        for index, row in subdataset.iterrows():
            all_cells = []

            index_aux = 1
            for cell in row[1:]:
                sub_col = row.index[index_aux][1]
                index_aux += 1

                # Se a célula for 'DI', pula para a próxima
                if cell == 'DI':
                    continue

                
                if pd.isna(cell) or pd.isna(pd.to_numeric(cell, errors='coerce')): 
                    errors.append(f"{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}, linha {index + 3}: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '{parent_id}' e indicador filho '{sub_col}'.")
                    continue
                cell_aux = cell.replace(',', '.')
                cell_aux = pd.to_numeric(cell_aux, errors='coerce')
                
                # Trunca o valor para 3 casas decimais
                new_value = truncate_number(cell_aux, 3)
                a = Decimal(str(cell))
                
                # Verifica se o valor tem mais de 3 casas decimais
                if not has_more_than_3_decimal_places and a.as_tuple().exponent < -3:
                    has_more_than_3_decimal_places = True
                    warnings.append(f"{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}, linha {index + 3}: Existem valores com mais de 3 casas decimais na planilha, serão consideradas apenas as 3 primeiras casas decimais.")
                
                all_cells.append(str(new_value))
                
            
            # Soma os valores válidos da linha
            row_sum = sum([Decimal(cell) for cell in all_cells])
            
            if row_sum < Decimal('0.99') or row_sum > Decimal('1.01'):
                errors.append(f'{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}, linha {index + 3}: A soma dos valores para o indicador pai {parent_id} é {row_sum}, e não 1.')
            elif row_sum != 1 and row_sum >= Decimal('0.99') and row_sum <= Decimal('1.01'):
                warnings.append(f'{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}, linha {index + 3}: A soma dos valores para o indicador pai {parent_id} é {row_sum}, e não 1.')
            
    return errors, warnings

def count_repeated_values(string_list):
    # Convert the list to a set to remove duplicates
    unique_values = set(string_list)
    # The number of repeated values is the original list length minus the unique set length
    num_repeated = len(string_list) - len(unique_values)
    return num_repeated

def verify_sum_prop_influence_factor_values(df_proportionalities, exists_sp_proportionalities, file_name):
    df = df_proportionalities.copy()
    
    errors = []
    warnings = []

    if df.empty:
        return True, errors, warnings
    
    level_two_columns = df_proportionalities.columns.get_level_values(1).unique().tolist()

    if SP_PROPORTIONALITIES_COLUMNS.ID not in level_two_columns:
        errors.append(f"{file_name}: Verificação abortada porque a coluna '{SP_PROPORTIONALITIES_COLUMNS.ID}' está ausente.")
        return not errors, errors, warnings
    
    # Se não existir a coluna de proporcionalidades, retorna True
    if not exists_sp_proportionalities:
        return True, errors, warnings

    try:
        # Verifica se a soma dos valores de cada subdataset é igual a 1
        subdatasets = build_subdatasets(df, file_name)
        errors, warnings = check_sum_equals_one(subdatasets)
    except Exception as e:
        errors.append(f"{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def extract_ids_from_list_from_description(df_description):
    # Remove a linha que o nivel == 1
    df_description = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] != '1']
    
    # Remove a linha que o nivel == 2 e cenario == 0
    # Verifica se a coluna cenario existe em df_description
    if SP_DESCRIPTION_COLUMNS.CENARIO in df_description.columns:
        df_description = df_description[~((df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '2') & (df_description[SP_DESCRIPTION_COLUMNS.CENARIO] == '0'))]
    
    valores_ids = set(df_description[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str))

    ids_valids = set()
    ids_invalids = set()

    for valor in valores_ids:
        is_correct, __ = check_values_integers(valor, 1)
        if not is_correct:
            ids_invalids.add(valor)
        if is_correct:
            ids_valids.add(valor)
    
    # Converte em inteiros
    ids_valids = set(str(id) for id in ids_valids)

    
    return ids_valids, ids_invalids

def compare_ids(id_description, id_proporcionalities, name_sp_description, name_sp_proportionalities):
    errors = []
    id_description_not_in_values = id_description - id_proporcionalities
    id_values_not_in_description = id_proporcionalities - id_description

    if id_description_not_in_values:
        errors.append(f"{name_sp_description}: Códigos dos indicadores ausentes em {name_sp_proportionalities}: {list(id_description_not_in_values)}.")
    if id_values_not_in_description:
        errors.append(f"{name_sp_proportionalities}: Códigos dos indicadores ausentes em {name_sp_description}: {list(id_values_not_in_description)}.")
    
    return errors
def verify_ids_sp_description_proportionalities(df_sp_description, df_sp_proportionalities, df_sp_scenario, name_sp_description, name_sp_proportionalities, name_sp_scenario):
    # Copia os dataframes para não alterar os originais
    df_description = df_sp_description.copy()
    df_proportionalities = df_sp_proportionalities.copy()
    df_sp_scenario = df_sp_scenario.copy()

    # Se for empty, retorna True
    if df_description.empty or df_proportionalities.empty:
        return True, [], []
    errors = []
    warnings = []

    if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns:
        errors.append(f"{name_sp_description}: Verificação abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
        return not errors, errors, warnings
    
    sp_scenario_exists = True
    if df_sp_scenario.empty:
        sp_scenario_exists = False

    if sp_scenario_exists:
        if SP_SCENARIO_COLUMNS.SIMBOLO not in df_sp_scenario.columns:
            errors.append(f"{name_sp_scenario}: Verificação abortada porque a coluna '{SP_SCENARIO_COLUMNS.SIMBOLO}' está ausente.")
    
    # Return if errors
    if errors:
        return not errors, errors, []
    
    lista_simbolos_cenarios = []
    if sp_scenario_exists:
        lista_simbolos_cenarios = df_sp_scenario[SP_SCENARIO_COLUMNS.SIMBOLO].unique().tolist()

    # Clean non numeric values
    df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, name_sp_description, [SP_DESCRIPTION_COLUMNS.CODIGO])
        

    codes_level_to_remove = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '1'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
    id_description_valids, __  = extract_ids_from_list_from_description(df_description)    

    # Lista com todos as colunas nivel 1
    level_one_columns = df_proportionalities.columns.get_level_values(0).unique().tolist()
    level_two_columns = df_proportionalities.columns.get_level_values(1).unique().tolist()

    if SP_PROPORTIONALITIES_COLUMNS.ID not in level_two_columns:
        errors.append(f"{name_sp_proportionalities}: Verificação abortada porque a coluna '{SP_PROPORTIONALITIES_COLUMNS.ID}' está ausente.")
        return not errors, errors, warnings
    
    # Verifica se id existe em level_two_columns
    if SP_PROPORTIONALITIES_COLUMNS.ID in level_two_columns:
        level_two_columns.remove(SP_PROPORTIONALITIES_COLUMNS.ID)
    
    # Remove todos os valores de level_one_columns que começam com 'Unnamed': if not col.startswith('Unnamed'):
    level_one_columns = [col for col in level_one_columns if not col.startswith('Unnamed')]
    level_two_columns = [col for col in level_two_columns if not col.startswith('Unnamed')]

    cleaned_level_one_columns, extras_columns_one = extract_ids_from_list(level_one_columns, lista_simbolos_cenarios)
    cleaned_level_one_columns = [str(id) for id in cleaned_level_one_columns]
    extras_columns_one = [str(id) for id in extras_columns_one]
    extracted_ids_one = set([id.split('-')[0] for id in cleaned_level_one_columns]) - set(codes_level_to_remove)

    cleaned_level_two_columns, extras_columns_two = extract_ids_from_list(level_two_columns, lista_simbolos_cenarios)
    cleaned_level_two_columns = [str(id) for id in cleaned_level_two_columns]
    extras_columns_two = [str(id) for id in extras_columns_two]
    extracted_ids_two = set([id.split('-')[0] for id in cleaned_level_two_columns]) - set(codes_level_to_remove)
    all_codes_proportionalities = set(extracted_ids_one) | set(extracted_ids_two)

    # Convert to ser para int 
    id_description_valids = set([int(id) for id in id_description_valids])
    all_codes_proportionalities = set([int(id) for id in all_codes_proportionalities])

    # Verifica se todos os códigos que estão em df_description e não estão em df_proportionalities
    errors += compare_ids(id_description_valids, all_codes_proportionalities, name_sp_description, name_sp_proportionalities)
        

    return not errors, errors, warnings
