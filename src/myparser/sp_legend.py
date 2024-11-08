import pandas as pd
import os
from src.myparser.model.spreadsheets import SP_LEGEND_COLUMNS, SP_VALUES_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS
from src.util.utilities import extract_ids_from_list, clean_non_numeric_and_less_than_value_integers_dataframe, check_file_exists, read_legend_qml_file
from src.util.utilities import check_overlapping, get_min_max_legend

def verify_overlapping_multiple_legend_value(root_path, df_description):
    errors, warnings = [], []
    try:
        # Verificar se a coluna NIVEL está presente em descrição
        if SP_DESCRIPTION_COLUMNS.NIVEL not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' não está ausente.")
            return not errors, errors, warnings
        
        # 1 - Listar todos os arquivos qml da pasta
        files_qml = [f for f in os.listdir(root_path) if f.endswith('.qml')]

        # Caso não tenha arquivos qml, retorna sem erros pois não há o que verificar
        if len(files_qml) == 0:
            return not errors, errors, warnings
        
        # Cópia do DataFrame para não alterar o original
        df_description = df_description.copy()
        # Verifica se o DataFrame está vazio
        if df_description.empty:
            return not errors, errors, warnings
        # Verifica se a coluna CODIGO está presente
        if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
            return not errors, errors, warnings
        
        # Clean non numeric values - No futuro essa função será removida
        df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])
        
        # Lista com todos os códigos que são nivel 1 - Não tem dado
        codigos_indicadores_nivel_1 = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '1'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
        
        # Lista com todos os códigos que são nivel 2 - Pode ou não ter dado
        codigos_indicadores_nivel_2 = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '2'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()

        # Todos os códigos que não são nivel 1 e nem nivel 2 - Todos devem ter dado
        codigos_indicadores_outros = [codigo for codigo in df_description[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist() if codigo not in codigos_indicadores_nivel_1 and codigo not in codigos_indicadores_nivel_2]
        
        
        # CASO 1: Caso veio o legenda.qml, verifica apenas ele.
        if (SP_LEGEND_COLUMNS.NAME_SP in files_qml):
            path_legend = os.path.join(root_path, SP_LEGEND_COLUMNS.NAME_SP)
            df_qml_legend, errors_read_legend_case_1 = read_legend_qml_file(path_legend)
            
            if errors_read_legend_case_1:
                errors.extend(errors_read_legend_case_1)            
            else: 
                __, errors_check =  check_overlapping(SP_LEGEND_COLUMNS.NAME_SP, df_qml_legend)
                errors.extend(errors_check)
            errors = sorted(list(set(errors)))
            return not errors, errors, warnings

        # Processando os indicadores de nivel 2
        for codigo in codigos_indicadores_nivel_2:
            file_name = codigo + '.qml'
            path_legend = os.path.join(root_path, file_name)
            exist_file, __ = check_file_exists(path_legend)
            
            if not exist_file:
                continue
            
            df_qml_legend, errors_read_legend_level_2 = read_legend_qml_file(path_legend)
            
            if errors_read_legend_level_2:
                errors.extend(errors_read_legend_level_2)
            else: 
                __, errors_i = check_overlapping(file_name, df_qml_legend)
                errors.extend(errors_i)

        # Processando os outros indicadores que não são nivel 1 e nem nivel 2
        for codigo in codigos_indicadores_outros:
            file_name = codigo + '.qml'
            path_legend = os.path.join(root_path, file_name)
            exist_file, error = check_file_exists(path_legend)
            
            if not exist_file:
                continue
            
            df_qml_legend, errors_read_legend_not_level_1_2 = read_legend_qml_file(path_legend)

            if errors_read_legend_not_level_1_2:
                errors.extend(errors_read_legend_not_level_1_2)
            else:
                __, errors_i = check_overlapping(file_name, df_qml_legend)
                errors.extend(errors_i)
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_LEGEND_COLUMNS.NAME_SP}: {e}.")
    errors = sorted(list(set(errors)))
    return not errors, errors, warnings

def verify_values_range_multiple_legend(root_path, df_values, df_description, df_sp_scenario):
    errors, warnings = [], []
    try:
        # Verificar se a coluna NIVEL está presente em descrição
        if SP_DESCRIPTION_COLUMNS.NIVEL not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.NIVEL}' não está ausente.")
            return not errors, errors, warnings
        
        MIN_VALUE, MAX_VALUE = SP_LEGEND_COLUMNS.MIN_LOWER_LEGEND_DEFAULT, SP_LEGEND_COLUMNS.MAX_UPPER_LEGEND_DEFAULT

        df_qml_legend = None

        # Copia os DataFrames para não alterar os originais
        df_values = df_values.copy()
        df_description = df_description.copy()
        df_sp_scenario = df_sp_scenario.copy()
        
        # Verifica se o DataFrame está vazio
        if df_values.empty:
            return True, errors, warnings
        if df_description.empty or df_sp_scenario.empty:
            return not errors, errors, warnings
        
        sp_scenario_exists = True
        if df_sp_scenario.empty:
            sp_scenario_exists = False

        if sp_scenario_exists:
            if SP_SCENARIO_COLUMNS.SIMBOLO not in df_sp_scenario.columns:
                errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Verificação foi abortada porque a coluna '{SP_SCENARIO_COLUMNS.SIMBOLO}' não está ausente.")
        
        # Return if errors
        if errors:
            errors = sorted(list(set(errors)))
            return not errors, errors, []
        
        lista_simbolos_cenarios = []
        if sp_scenario_exists:
            lista_simbolos_cenarios = df_sp_scenario[SP_SCENARIO_COLUMNS.SIMBOLO].unique().tolist()
        
        #### Pré-processamento dos DataFrames
        
        # Remove a coluna ID se existir
        if SP_VALUES_COLUMNS.ID in df_values.columns:
            df_values.drop(columns=[SP_VALUES_COLUMNS.ID], inplace=True)

        # Verifica se a coluna CODIGO está presente
        if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
            return not errors, errors, warnings
        
        # Clean non numeric values - No futuro essa função será removida
        df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])
        
        # Lista com todos os códigos que são nivel 1 - Não tem dado
        codigos_indicadores_nivel_1 = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == '1'][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
    
        colunas_sp_valores, __ = extract_ids_from_list(df_values.columns, lista_simbolos_cenarios)
        exists_legend_default, __ = check_file_exists(os.path.join(root_path, SP_LEGEND_COLUMNS.NAME_SP))
        if exists_legend_default:
            df_qml_legend, errors_read_legend_default = read_legend_qml_file(os.path.join(root_path, SP_LEGEND_COLUMNS.NAME_SP))
            
            if errors_read_legend_default:
                errors.extend(errors_read_legend_default)
            else:            
                errors_legend_min_max, min_value, max_value = get_min_max_legend(SP_LEGEND_COLUMNS.NAME_SP, df_qml_legend)
                errors.extend(errors_legend_min_max)
            
            if errors:
                errors = sorted(list(set(errors)))
                return not errors, errors, warnings
            
            MIN_VALUE = min_value
            MAX_VALUE = max_value

        # Processando as colunas válidas
        for column in colunas_sp_valores:
                code_column = column.split('-')[0]

                if code_column in codigos_indicadores_nivel_1:
                    continue
                
                # Os casos abaixo são para os indicadores de nivel 2 e outros já são tratados
                if not exists_legend_default:
                    
                    qml_code_legend = code_column + '.qml'
                    exists_legend_i, __ = check_file_exists(os.path.join(root_path, qml_code_legend))

                    if not exists_legend_i:
                        MIN_VALUE = SP_LEGEND_COLUMNS.MIN_LOWER_LEGEND_DEFAULT
                        MAX_VALUE = SP_LEGEND_COLUMNS.MAX_UPPER_LEGEND_DEFAULT
                    
                    else:
                        df_qml_legend, errors_read_legend_level_2 = read_legend_qml_file(os.path.join(root_path, qml_code_legend))
                        if errors_read_legend_level_2:
                            errors.extend(errors_read_legend_level_2)
                            MIN_VALUE = SP_LEGEND_COLUMNS.MIN_LOWER_LEGEND_DEFAULT
                            MAX_VALUE = SP_LEGEND_COLUMNS.MAX_UPPER_LEGEND_DEFAULT
                        else:
                            errors_legend, min_value, max_value = get_min_max_legend(qml_code_legend, df_qml_legend)
                            
                            if errors_legend:
                                errors.extend(errors_legend)
                            
                            MIN_VALUE = min_value
                            MAX_VALUE = max_value
                        
                for index, value in df_values[column].items():
                    # Verifica se o valor é uma string DI
                    value_aux = value
                    if value == "DI":
                        continue
                    
                    if pd.isna(value):
                        continue
                    
                    # CORREÇÃO DOS VALORES FLUTUANTES
                    value = value.replace(',', '.')
        
                    value = pd.to_numeric(value, errors='coerce')
                    
                    # Verifica se o valor é um número
                    if pd.isna(value):
                        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}, linha {index + 2}: O valor '{value_aux}' não é um número válido para a coluna '{column}'.")
                        continue
                    # Verifica se o valor está no intervalo
                    if value < MIN_VALUE or value > MAX_VALUE:
                        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}, linha {index + 2}: O valor {value_aux} está fora do intervalo da legenda ({MIN_VALUE} a {MAX_VALUE}) para a coluna '{column}'.")     
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_VALUES_COLUMNS.NAME_SP}: {e}.")
    errors = sorted(list(set(errors))) # MELHORAR. Se um erro já existir dentro do erros não inserir
    return not errors, errors, warnings
