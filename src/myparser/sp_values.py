from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe, check_values_integers, generate_list_combinations, clean_sp_values_columns
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_VALUES_COLUMNS,SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS
import pandas as pd
def extract_ids_from_values(codes_level_to_remove, df_values):
    valores_ids = df_values.columns.str.split('-').str[0]

    # Remove os códigos que não são nivel 1
    valores_ids = set(valores_ids) - set(codes_level_to_remove)

    ids_valids = set()
    ids_invalids = set()

    for valor in valores_ids:
        is_correct, __ = check_values_integers(valor, 1)
        if not is_correct:
            ids_invalids.add(valor)
        if is_correct:
            ids_valids.add(valor)

    # Remover colunas que não são códigos: id e nome
    ids_invalids.discard(SP_VALUES_COLUMNS.ID)
    ids_invalids.discard(SP_VALUES_COLUMNS.NOME)
    
    # Converte em inteiros
    ids_valids = set(int(id) for id in ids_valids)

    return ids_valids, ids_invalids

def extract_ids_from_description(df_description):
    # Remove a linha que o nivel == 1
    df_description = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] != 1]
    
    # Remove a linha que o nivel == 2 e cenario == 0
    # Verifica se a coluna cenario existe em df_description
    if SP_DESCRIPTION_COLUMNS.CENARIO in df_description.columns:
        df_description = df_description[~((df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == 2) & (df_description[SP_DESCRIPTION_COLUMNS.CENARIO] == 0))]
    
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
    ids_valids = set(int(id) for id in ids_valids)

    
    return ids_valids, ids_invalids

def compare_ids(id_description, id_values, name_sp_description, name_sp_values):
    errors = []
    id_description_not_in_values = id_description - id_values
    id_values_not_in_description = id_values - id_description

    if id_description_not_in_values:
        errors.append(f"{name_sp_description}: Códigos dos indicadores ausentes em {name_sp_values}: {list(id_description_not_in_values)}.")
    if id_values_not_in_description:
        errors.append(f"{name_sp_values}: Códigos dos indicadores ausentes em {name_sp_description}: {list(id_values_not_in_description)}.")
    
    return errors

def processar_combinacoes_extras(lista_combinacoes, lista_combinacoes_sp_values):    
    for i in lista_combinacoes:
        # Se existe em lista_combinacoes_sp_values então pop
        if i in lista_combinacoes_sp_values:
            lista_combinacoes_sp_values.pop(lista_combinacoes_sp_values.index(i))

    # Criando mensagens de erro se houver elementos extras
    if lista_combinacoes_sp_values:
        return True, lista_combinacoes_sp_values
    return False, []

def verify_ids_sp_description_values(df_description, df_values):
    df_description = df_description.copy()
    df_values = df_values.copy()

    # Se for empty, retorna True
    if df_description.empty or df_values.empty:
        return True, [], []
    errors = []
    warnings = []

    if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos de indicadores foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
        return not errors, errors, warnings

    try:
        # Clean non numeric values
        df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])
        
        # codes_level = Lista com todos os códigos que são nivel 1
        codes_level_to_remove = df_description[df_description[SP_DESCRIPTION_COLUMNS.NIVEL] == 1][SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).tolist()
        id_description_valids, __  = extract_ids_from_description(df_description)
        id_values_valids, id_values_invalids = extract_ids_from_values(codes_level_to_remove, df_values)

        # Verifica se há códigos inválidos
        final_list_invalid_codes = list(id_values_invalids)
        # Order list
        final_list_invalid_codes.sort()
        if id_values_invalids:
            errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: Códigos inválidos: {final_list_invalid_codes}.")

        errors += compare_ids(id_description_valids, id_values_valids, SP_DESCRIPTION_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)

    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Erro ao processar os arquivos {SP_DESCRIPTION_COLUMNS.NAME_SP} e {SP_VALUES_COLUMNS.NAME_SP}: {e}.")

    
    return not errors, errors, warnings

def verify_combination_sp_description_values_scenario_temporal_reference(df_description, df_values, df_scenario, df_temporal_reference):
    errors = []
    df_description = df_description.copy()
    df_values = df_values.copy()
    df_scenario = df_scenario.copy()
    df_temporal_reference = df_temporal_reference.copy()
    # Se for empty, retorna True
    if df_description.empty or df_values.empty or df_temporal_reference.empty:
        return True, [], []

    # Check if columns exists
    text_error_column = "Verificação de combinação de cenários e referência temporal foi abortada porque a coluna"
    if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: {text_error_column} '{SP_DESCRIPTION_COLUMNS.CODIGO}' está ausente.")
    elif SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO not in df_temporal_reference.columns:
        errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: {text_error_column} '{SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO}' está ausente.")
    elif SP_VALUES_COLUMNS.ID not in df_values.columns:
        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: {text_error_column} '{SP_VALUES_COLUMNS.ID}' está ausente.")

    sp_scenario_exists = True
    if df_scenario is None or df_scenario.empty:
        sp_scenario_exists = False

    if sp_scenario_exists:
        if SP_DESCRIPTION_COLUMNS.CENARIO not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: {text_error_column} '{SP_DESCRIPTION_COLUMNS.CENARIO}' está ausente.")
        if SP_SCENARIO_COLUMNS.SIMBOLO not in df_scenario.columns:
            errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: {text_error_column} '{SP_SCENARIO_COLUMNS.SIMBOLO}' está ausente.")
    
    # Return if errors
    if errors:
        return not errors, errors, []

    # Clean non numeric values
    # Verifica se a coluna cenario existe em df_description
    collumns_to_clean_df_description = [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL]
    if sp_scenario_exists:
        collumns_to_clean_df_description.append(SP_DESCRIPTION_COLUMNS.CENARIO)
    df_description, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, collumns_to_clean_df_description)
    df_temporal_reference, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_temporal_reference, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])

    try: 
        # Verificar cada indicador em df_description
        for line, row in df_description.iterrows():
            # Leitura de valores
            codigo = str(row[SP_DESCRIPTION_COLUMNS.CODIGO])
            nivel = int(row[SP_DESCRIPTION_COLUMNS.NIVEL])

            # Criar lista de símbolos de cenários
            lista_simbolos_cenarios = []
            if sp_scenario_exists:
                lista_simbolos_cenarios = df_scenario[SP_SCENARIO_COLUMNS.SIMBOLO].unique().tolist()

            # Criar lista de símbolos temporais:
            lista_simbolos_temporais = sorted(df_temporal_reference[SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO].unique().tolist())
            primeiro_ano = lista_simbolos_temporais[0]

            cenario = 0
            if sp_scenario_exists:
                cenario = int(row[SP_DESCRIPTION_COLUMNS.CENARIO])
            
            # Define a lista de combinações
            lista_combinacoes = []
            if nivel >= 2:
                if cenario == 0:
                    lista_combinacoes.append(f"{codigo}-{primeiro_ano}")
                elif cenario == 1:

                    lista_combinacoes = generate_list_combinations(codigo, primeiro_ano, lista_simbolos_temporais, lista_simbolos_cenarios)
            
            # Copia de combinações
            lista_combinacoes_copia = lista_combinacoes.copy()
            
            # Verificar se as combinações estão presentes em df_values
            for combinacao in lista_combinacoes:
                if combinacao not in df_values.columns:
                    if nivel == 2 and cenario == 0:
                        continue
                    errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: A coluna '{combinacao}' é obrigatória.")
                    
            # Verifica combinações extras somente para o código X-texto
            lista_combinacoes_sp_values = [col for col in df_values.columns if col.startswith(f"{codigo}-")]
            
            # Verificar se há combinações extras            
            is_error, erros_message = processar_combinacoes_extras(lista_combinacoes_copia, lista_combinacoes_sp_values)
            if is_error:
                for erro in erros_message:
                    if nivel == 1:
                        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: A coluna '{erro}' é desnecessária para o indicador de nível 1.")
                        continue
                    # Casos nivel >= 2
                    errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: A coluna '{erro}' é desnecessária.")
            # Limpa lista
            lista_combinacoes.clear()
            lista_combinacoes_copia.clear()
    except Exception as e:
        errors.append(f"Erro ao processar os arquivos {SP_DESCRIPTION_COLUMNS.NAME_SP}, {SP_VALUES_COLUMNS.NAME_SP}, {SP_SCENARIO_COLUMNS.NAME_SP} e {SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: {e}.")
    return not errors, errors, []

def verify_unavailable_values(df_values):
    errors = []
    warnings = []
    if df_values.empty:
        return True, [], []
    try:
        df_values = df_values.copy()

        # Remove colunas que não são códigos: id e nome
        if SP_VALUES_COLUMNS.ID in df_values.columns:
            df_values.drop(columns=[SP_VALUES_COLUMNS.ID], inplace=True)
        if SP_VALUES_COLUMNS.NOME in df_values.columns:
            df_values.drop(columns=[SP_VALUES_COLUMNS.NOME], inplace=True)

        colunas_sp_valores, __ = clean_sp_values_columns(df_values.columns)
        for column in colunas_sp_valores:
            for index, value in df_values[column].items():
                # Verifica se o valor é uma string DI
                if value == "DI":
                    continue

                value = pd.to_numeric(value, errors='coerce')
                # Verifica se o valor é um número
                if pd.isna(value) or not isinstance(value, (int, float)):
                    errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}, linha {index + 2}: O valor não é um número válido e nem DI (Dado Indisponível) para a coluna '{column}'.")

    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_VALUES_COLUMNS.NAME_SP}: {e}.")
    return not errors, errors, warnings
