from decimal import Decimal

import pandas as pd

from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS
from src.util.utilities import truncate_number

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
    unique_parents = [col for col in parent_columns[2:] if 'Unnamed' not in col]
    subdatasets = {'main': df.iloc[:, :2]}
    
    for parent_id in unique_parents:
        start_col = (parent_columns == parent_id).argmax()
        end_col = (parent_columns[start_col + 1:] != parent_id).argmax() + start_col + 1
        if end_col == start_col + 1:
            end_col = len(parent_columns)
        columns_to_include = df.columns[:2].tolist() + df.columns[start_col:end_col].tolist()
        subdatasets[parent_id] = df.loc[:, columns_to_include]
    
    return subdatasets

def create_subdatasets_csv(df, parent_columns):
    """ Cria subdatasets a partir de um arquivo CSV. """
    unique_parents = []
    for col in parent_columns[2:]:
        if not col.startswith('Unnamed'):
            unique_parents.append(col)
    
    subdatasets = {'main': df.iloc[:, :2]}
    
    for parent_id in unique_parents:
        start_col = parent_columns.get_loc(parent_id)
        end_col = start_col + 1
        while end_col < len(parent_columns) and parent_columns[end_col].startswith('Unnamed'):
            end_col += 1
        columns_to_include = df.columns[:2].tolist() + df.columns[start_col:end_col].tolist()
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

            index_aux = 2
            for cell in row[2:]:
                sub_col = row.index[index_aux][1]
                index_aux += 1

                # Se a célula for 'DI', pula para a próxima
                if cell == 'DI':
                    continue

                cell_aux = pd.to_numeric(cell, errors='coerce')
                if pd.isna(cell_aux):
                    errors.append(f"{SP_PROPORTIONALITIES_COLUMNS.NAME_SP}, linha {index + 3}: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '{parent_id}' e indicador filho '{sub_col}'.")
                    continue
                
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
    df_proportionalities = df_proportionalities.copy()
    df = df_proportionalities.copy()
    
    errors = []
    warnings = []
    
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
