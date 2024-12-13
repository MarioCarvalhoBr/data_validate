from decimal import Decimal

import pandas as pd

from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS
from src.util.utilities import agrupar_lista, truncate_number, clean_non_numeric_and_less_than_value_integers_dataframe, check_values_integers, extract_ids_from_list

def build_subdatasets(df_proportionalities):
    df_proportionalities = df_proportionalities.copy()
    parent_columns = df_proportionalities.columns.get_level_values(0).unique().tolist()

    return create_subdatasets_xlsx(df_proportionalities, parent_columns)

def create_subdatasets_xlsx(df, parent_columns):
    """ Cria subdatasets a partir de um arquivo Excel. """
    # Remove a coluna que inicia com 'Unnamed'
    parent_ids_cleaned = [col for col in parent_columns if not col.startswith('Unnamed')]

    subdatasets = {}

    # Pegar toda a coluna level 2 que o código é id e colcoar em um sub_dataset_id
    level_2_columns = df.columns
    has_found_col_id = False
    
    found_col_level_0 = None

    for col in level_2_columns:
        col_level_0, col_level_1 = col
        if col_level_1 == SP_PROPORTIONALITIES_COLUMNS.ID:
            has_found_col_id = True
            found_col_level_0 = col_level_0
            break
    
    if not has_found_col_id:
        return subdatasets
    
    sub_dataset_id = df[found_col_level_0]    

    for parent_id in parent_ids_cleaned:
        subdatasets[parent_id] = pd.concat([sub_dataset_id, df[parent_id]], axis=1)

    return subdatasets

def check_sum_equals_one(subdatasets, sp_df_values, name_sp_df_values, name_sp_proporcionalities_name):
    errors = []
    warnings = []

    has_more_than_3_decimal_places = False
    count_values_has_more_than_3_decimal_places = 0
    line_init_values = 0

    for parent_id, subdataset in subdatasets.items():

        line_init = None
        line_end = None
        count_errors = 0
        errors_column = []
        
        for index, row in subdataset.iterrows():
            all_cells = []           

            # Iterrows retorna uma tupla nome da coluna, dados da linha
            lista_id_coluna_valor = []
            id_linha = 0
            # sub_col = ""
            for i, cell in enumerate(row):
                # Nome da coluna
                nome_coluna = row.index[i]

                if i == 0:
                    id_linha = cell
                    continue

                lista_id_coluna_valor.append([id_linha, nome_coluna, cell])
                # sub_col = nome_coluna

                # Se a célula for 'DI', pula para a próxima
                if cell == 'DI':
                    continue
                
                if pd.isna(cell) or pd.isna(pd.to_numeric(cell, errors='coerce')): 
                    if line_init is None:
                        line_init = index + 3
                        errors_column.append(f"{name_sp_proporcionalities_name}, linha {index + 3}: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '{parent_id}'.")
                    count_errors += 1
                    
                    line_end = index + 3
                    continue
                
                cell_aux = cell.replace(',', '.')
                cell_aux = pd.to_numeric(cell_aux, errors='coerce')
                
                # Trunca o valor para 3 casas decimais
                new_value = truncate_number(cell_aux, 3)
                a = Decimal(str(cell))
                
                # Verifica se o valor tem mais de 3 casas decimais
                if a.as_tuple().exponent < -3:
                    if not has_more_than_3_decimal_places:
                        line_init_values = index + 3
                    has_more_than_3_decimal_places = True
                    count_values_has_more_than_3_decimal_places += 1
                
                all_cells.append(str(new_value))
            
            # Soma os valores válidos da linha
            row_sum = sum([Decimal(cell) for cell in all_cells])

            
            if row_sum == 0:
                for data in lista_id_coluna_valor:
                    id_linha, id_coluna, valor = data
                    
                    try: 
                        valor = sp_df_values.loc[sp_df_values[SP_VALUES_COLUMNS.ID] == id_linha][id_coluna].values[0]
                        if valor != 'DI' and float(valor) != 0:
                            errors.append(f"{name_sp_proporcionalities_name}: A soma de fatores influenciadores para o ID '{id_linha}' no pai '{id_coluna}' é 0 (zero). Na planilha {name_sp_df_values}, existe(m) valor(es) para os filhos do indicador '{id_coluna}', no mesmo ID, que não é (são) zero ou DI (Dado Indisponível).")

                    except Exception:
                        continue
            elif row_sum < Decimal('0.99') or row_sum > Decimal('1.01'):
                errors.append(f'{name_sp_proporcionalities_name}, linha {index + 3}: A soma dos valores para o indicador pai {parent_id} é {row_sum}, e não 1.')
            elif row_sum != 1 and row_sum >= Decimal('0.99') and row_sum <= Decimal('1.01'):
                warnings.append(f'{name_sp_proporcionalities_name}, linha {index + 3}: A soma dos valores para o indicador pai {parent_id} é {row_sum}, e não 1.')
        if count_errors > 1:
            errors_column.clear()
            errors_column.append(f"{name_sp_proporcionalities_name}: {count_errors} valores que não são número válido nem DI (Dado Indisponível) para o indicador pai '{parent_id}' entre as linhas {line_init} e {line_end}.")
            
        errors.extend(errors_column)

    if has_more_than_3_decimal_places:
        text_existem = "Existem" if count_values_has_more_than_3_decimal_places > 1 else "Existe"
        text_valores = "valores" if count_values_has_more_than_3_decimal_places > 1 else "valor"
        # TODO: No futuro, verificar como vai ficar essa questão de reportar a linha
        warnings.append(f"{name_sp_proporcionalities_name}, linha {line_init_values}: {text_existem} {count_values_has_more_than_3_decimal_places} {text_valores} com mais de 3 casas decimais na planilha, serão consideradas apenas as 3 primeiras casas decimais.")
        
    return errors, warnings

def count_repeated_values(string_list):
    # Convert the list to a set to remove duplicates
    unique_values = set(string_list)
    # The number of repeated values is the original list length minus the unique set length
    num_repeated = len(string_list) - len(unique_values)
    return num_repeated

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

def verify_sum_prop_influence_factor_values(sp_df_proportionalities, sp_df_values, name_sp_df_proporcionalities, name_sp_df_values):
    errors, warnings = [], []
    try:
        df_proportionalities = sp_df_proportionalities.copy()
        df_values = sp_df_values.copy()

        if df_proportionalities.empty or df_values.empty:
            return True, errors, warnings
        
        level_two_columns = df_proportionalities.columns.get_level_values(1).unique().tolist()

        if SP_PROPORTIONALITIES_COLUMNS.ID not in level_two_columns:
            errors.append(f"{name_sp_df_proporcionalities}: Verificação abortada porque a coluna '{SP_PROPORTIONALITIES_COLUMNS.ID}' está ausente.")
            return not errors, errors, warnings
   
        # Verifica se a soma dos valores de cada subdataset é igual a 1
        subdatasets = build_subdatasets(df_proportionalities)

        errors, warnings = check_sum_equals_one(subdatasets,  sp_df_values, name_sp_df_values, name_sp_df_proporcionalities)
    except Exception as e:
        errors.append(f"{name_sp_df_proporcionalities}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_ids_sp_description_proportionalities(df_sp_description, df_sp_proportionalities, df_sp_scenario, name_sp_description, name_sp_proportionalities, name_sp_scenario):
    errors, warnings = [], []
    try:
        # Copia os dataframes para não alterar os originais
        df_description = df_sp_description.copy()
        df_proportionalities = df_sp_proportionalities.copy()
        df_sp_scenario = df_sp_scenario.copy()

        # Se for empty, retorna True
        if df_description.empty or df_proportionalities.empty:
            return True, errors, warnings
        
        # Verifica a coluna nível em descrição
        if SP_DESCRIPTION_COLUMNS.NIVEL not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de legenda não realizada. Coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' não encontrada.")
            return not errors, errors, warnings

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
    except Exception as e:
        errors.append(f"{name_sp_proportionalities}: Erro ao processar a verificação: {e}.")    

    return not errors, errors, warnings

def verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities, name_sp_proportionalities):
    errors, warnings = [], []
    try:
        # Copia os dataframes para não alterar os originais
        df_proportionalities = df_sp_proportionalities.copy()

        # Se for empty, retorna True
        if df_proportionalities.empty:
            return True, errors, warnings
        
        level_two_columns = df_proportionalities.columns.get_level_values(1).unique().tolist()

        if SP_PROPORTIONALITIES_COLUMNS.ID not in level_two_columns:
            errors.append(f"{name_sp_proportionalities}: Verificação abortada porque a coluna '{SP_PROPORTIONALITIES_COLUMNS.ID}' está ausente.")
            return not errors, errors, warnings
        
        # Return if errors
        if errors:
            return not errors, errors, warnings    
        
        # Códigos dos indicadores que estão em nível 1
        level_one_columns = [col for col in df_proportionalities.columns.get_level_values(0).tolist() if not col.startswith('Unnamed')]
        grouped_columns = agrupar_lista(level_one_columns)

        unique_list = []
        for group in grouped_columns:
            first_element = group[0]
            if first_element not in unique_list:
                unique_list.append(first_element)
            else:
                errors.append(f"{name_sp_proportionalities}: O indicador pai '{first_element}' está repetido na planilha.")
        
        errors = list(set(errors))
    except Exception as e:
        errors.append(f"{name_sp_proportionalities}: Erro ao processar a verificação: {e}.")

    return not errors, errors, warnings

def verify_parent_child_relationships(df_sp_proportionalities, df_sp_composition, name_sp_proportionalities, name_sp_composition):
    errors, warnings = [], []
    try:
        # Copia os DataFrames para evitar modificar os originais
        df_proportionalities = df_sp_proportionalities.copy()
        df_composition = df_sp_composition.copy()

        # Se algum DataFrame estiver vazio, retorna sucesso sem erros
        if df_proportionalities.empty or df_composition.empty:
            return True, errors, warnings
        
        # Cria os subdatasets de proporcionalidades
        subdatasets = build_subdatasets(df_proportionalities)

        level_two_columns = df_proportionalities.columns.get_level_values(1).unique()

        # Verifica se as colunas obrigatórias estão presentes
        required_columns = [
            (SP_PROPORTIONALITIES_COLUMNS.ID, level_two_columns, name_sp_proportionalities),
            (SP_COMPOSITION_COLUMNS.CODIGO_PAI, df_composition.columns, name_sp_composition),
            (SP_COMPOSITION_COLUMNS.CODIGO_FILHO, df_composition.columns, name_sp_composition),
        ]
        
        for column, available_columns, sheet_name in required_columns:
            if column not in available_columns:
                errors.append(f"{sheet_name}: Verificação abortada porque a coluna '{column}' está ausente.")
                return False, errors, warnings

        composition_gouped_dict = {}
        
        # Remove de df_composition as linhas que tem CODIGO_PAI == 1
        df_composition = df_composition[df_composition[SP_COMPOSITION_COLUMNS.CODIGO_PAI] != '1']
        
        for __, row in df_composition.iterrows():
            pai = row[SP_COMPOSITION_COLUMNS.CODIGO_PAI]
            filho = row[SP_COMPOSITION_COLUMNS.CODIGO_FILHO]
            if pai not in composition_gouped_dict:
                composition_gouped_dict[pai] = []
            composition_gouped_dict[pai].append(filho)        
        
        for parent_id, subdataset in subdatasets.items():

            cleaned_parent_id = parent_id.split('-')[0]

            # VERIFICAR SE O INDICADOR PAI ESTÁ NA COMPOSIÇÃO. Verificar na key de composition_gouped_dict
            if cleaned_parent_id not in composition_gouped_dict.keys():
                if ":" not in parent_id:
                    errors.append(f"{name_sp_proportionalities}: O indicador pai '{cleaned_parent_id}' (em '{parent_id}') não está presente na coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' da planilha {name_sp_composition}.")
                continue

            # Lista de filhos do subdataset com as chaves originais
            list_children_key_original = subdataset.columns.tolist()
            list_children_key_original.remove(SP_PROPORTIONALITIES_COLUMNS.ID) 
            
            # Lista de filhos do subdataset com as chaves limpas
            list_childrens_key_cleaned = [filho.split('-')[0] for filho in list_children_key_original] 
            
            # Dicionário que armazena os filhos de cada pai
            dict_childrens_keys_by_cleaned_parent_id = {} 
            dict_childrens_keys_by_cleaned_parent_id.setdefault(cleaned_parent_id, []).extend(list_childrens_key_cleaned)

            # Verifica se composition_gouped_dict[cleaned_parent_id] contém os mesmos filhos que dict_childrens_keys_by_cleaned_parent_id[cleaned_parent_id]
            set_errors = set()
            set_errors = {
                            f"{name_sp_proportionalities}: O indicador '{filho}' (em '{filho_orig}') não é filho do indicador '{cleaned_parent_id}' (em '{parent_id}') conforme especificado em {name_sp_composition}."
                            for filho, filho_orig in zip(list_childrens_key_cleaned, list_children_key_original)
                            if filho not in composition_gouped_dict[cleaned_parent_id]
                        }
            errors.extend(set_errors)

            # Verifica se dict_childrens_keys_by_cleaned_parent_id[cleaned_parent_id] contém os mesmos filhos que composition_gouped_dict[cleaned_parent_id]
            for filho in composition_gouped_dict[cleaned_parent_id]:
                if filho not in dict_childrens_keys_by_cleaned_parent_id[cleaned_parent_id]:
                    code_pai_local = parent_id.split('-')[0]
                    errors.append(f"{name_sp_proportionalities}: Deve existir pelo menos uma relação do indicador filho '{filho}' com o indicador pai '{code_pai_local}' (em '{parent_id}') conforme especificado em {name_sp_composition}.")
                    
    except Exception as e:
        errors.append(f"{name_sp_proportionalities}: Erro ao processar a verificação: {e}.")

    # Ordena os erros
    errors = sorted(set(errors))
    
    return not errors, errors, warnings

def verify_ids_values_proportionalities(df_proportionalities, df_values, proportionalities_name, values_name):
    errors, warnings = [], []
    try:
        df_proportionalities = df_proportionalities.copy()
        df_values = df_values.copy()

        if df_proportionalities.empty and df_values.empty:
            return True, errors, warnings
        
        proportionalities_columns = df_proportionalities.columns.get_level_values(1).unique().tolist()

        required_columns = [
            (SP_PROPORTIONALITIES_COLUMNS.ID, proportionalities_columns, proportionalities_name),
            (SP_VALUES_COLUMNS.ID, df_values.columns, values_name),
        ]
        
        for column, available_columns, sheet_name in required_columns:
            if column not in available_columns:
                errors.append(f"{sheet_name}: Verificação abortada porque a coluna '{column}' está ausente.")
                return False, errors, warnings

        proportionalities_indicators_lvl1 = df_proportionalities.columns.get_level_values(0).unique().tolist()
        proportionalities_indicators_lvl1.remove('Unnamed: 0_level_0')
        
        proportionalities_indicators_lvl2 = proportionalities_columns
        proportionalities_indicators_lvl2.remove(SP_PROPORTIONALITIES_COLUMNS.ID)
        
        proportionalities_indicators = sorted(set(proportionalities_indicators_lvl1 + proportionalities_indicators_lvl2))

        values_indicators = df_values.columns.unique().tolist()
        values_indicators.remove(SP_VALUES_COLUMNS.ID)
        values_indicators = sorted(set(values_indicators))

        common_indicators = sorted(set(values_indicators).intersection(proportionalities_indicators))

        missing_in_proportionalities = sorted(set(values_indicators) - set(common_indicators))
        for indicator in missing_in_proportionalities:
            if ":" not in indicator:
                errors.append(f"{values_name}: O indicador '{indicator}' não está presente na planilha {proportionalities_name}.")

        missing_in_values = sorted(set(proportionalities_indicators) - set(common_indicators))
        for indicator in missing_in_values:
            if indicator.endswith('.1'):
                continue
            if ":" not in indicator:
                errors.append(f"{proportionalities_name}: O indicador '{indicator}' não está presente na planilha {values_name}.")
    
    except Exception as e:
        errors.append(f"{proportionalities_name}: Erro ao processar a verificação: {e}.")
    
    return not errors, errors, warnings
