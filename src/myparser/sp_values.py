from src.util.utilities import dataframe_clean_numeric_values_less_than
from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_VALUES_COLUMNS,SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS 

def extract_ids_from_description(df_description):
    ids = set(df_description[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str))
    # Converte em inteiros
    ids = set(int(id) for id in ids if id.isdigit())
    return ids

def extract_ids_from_values(df_values):
    ids = set(df_values.columns.str.split('-').str[0])
    ids = set(id for id in ids if id.isdigit())
    # Converte em inteiros
    ids = set(int(id) for id in ids)
    return ids

def compare_ids(id_description, id_values, name_sp_description, name_sp_values):
    errors = []
    id_description_not_in_values = id_description - id_values
    id_values_not_in_description = id_values - id_description

    if id_description_not_in_values:
        errors.append(f"{name_sp_description}: Códigos dos indicadores ausentes em {name_sp_values}: {list(id_description_not_in_values)}.")
    if id_values_not_in_description:
        errors.append(f"{name_sp_values}: Códigos dos indicadores ausentes em {name_sp_description}: {list(id_values_not_in_description)}.")
    
    return errors

def verify_ids_sp_description_values(df_description, df_values):
    df_description = df_description.copy()
    df_values = df_values.copy()
    errors = []
    warnings = []

    try:

        # Verifica se as colunas com código existem
        if 'codigo' not in df_description.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos de indicadores não realizada.")
            return False, errors, []
        
        # Clean non numeric values
        df_description, _ = dataframe_clean_numeric_values_less_than(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])

        id_description = extract_ids_from_description(df_description)
        id_values = extract_ids_from_values(df_values)

        errors += compare_ids(id_description, id_values, SP_DESCRIPTION_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)

    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Erro ao processar os arquivos {SP_DESCRIPTION_COLUMNS.NAME_SP} e {SP_VALUES_COLUMNS.NAME_SP}: {e}.")

    
    return not errors, errors, warnings


def verificar_combinacoes_extras(lista_combinacoes, lista_combinacoes_sp_values):    
    for i in lista_combinacoes:
        # Se existe em lista_combinacoes_sp_values então pop
        if i in lista_combinacoes_sp_values:
            lista_combinacoes_sp_values.pop(lista_combinacoes_sp_values.index(i))

    # Criando mensagens de erro se houver elementos extras
    if lista_combinacoes_sp_values:
        return True, lista_combinacoes_sp_values
    return False, []
def verify_combination_sp_description_values_scenario_temporal_reference(df_description, df_values, df_scenario, df_temporal_reference):
    errors = []
    df_description = df_description.copy()
    df_values = df_values.copy()
    df_scenario = df_scenario.copy()
    df_temporal_reference = df_temporal_reference.copy()

    # Verifica se as colunas com código e cenário existem
    if SP_DESCRIPTION_COLUMNS.CODIGO not in df_description.columns or SP_DESCRIPTION_COLUMNS.CENARIO not in df_description.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de combinação de cenários e referência temporal não realizada.")
        return False, errors, []
    
    # Verifica se as colunas obrigatórias de df_temporal_reference e df_scenario existem
    if SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO not in df_temporal_reference.columns:
        errors.append(f"{SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP}: Verificação de combinação de cenários e referência temporal não realizada.")
        return False, errors, []

    if SP_SCENARIO_COLUMNS.SIMBOLO not in df_scenario.columns:
        errors.append(f"{SP_SCENARIO_COLUMNS.NAME_SP}: Verificação de combinação de cenários e referência temporal não realizada.")
        return False, errors, []
    
    if SP_VALUES_COLUMNS.ID not in df_values.columns:
        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: Verificação de combinação de cenários e referência temporal não realizada.")
        return False, errors, []


    # Clean non numeric values
    df_description, _ = dataframe_clean_numeric_values_less_than(df_description, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO])
    df_temporal_reference, _ = dataframe_clean_numeric_values_less_than(df_temporal_reference, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO])

    # Verificar cada indicador em df_description
    for line, row in df_description.iterrows():

        # Criar lista de símbolos de cenários
        lista_simbolos_cenarios = df_scenario[SP_SCENARIO_COLUMNS.SIMBOLO].unique().tolist()

        # Criar lista de símbolos temporais
        lista_simbolos_temporais = sorted(df_temporal_reference[SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO].unique().tolist())
        primeiro_ano = lista_simbolos_temporais[0]

        codigo = str(row[SP_DESCRIPTION_COLUMNS.CODIGO]).replace(',', '')
        # Replace .0
        codigo = codigo.replace('.0', '')

        # Verifica se o código é um número maior que zero
        if not codigo.isdigit():
           continue

        cenario = row['cenario']
        lista_combinacoes = []
        lista_combinacoes.clear()
        if cenario == 0:
            lista_combinacoes.append(f"{codigo}-{primeiro_ano}")
        elif cenario == 1:
            lista_combinacoes.append(f"{codigo}-{primeiro_ano}")
            # Remove first element
            lista_simbolos_temporais.pop(0)
            for ano in lista_simbolos_temporais:
                for simbolo in lista_simbolos_cenarios:
                    lista_combinacoes.append(f"{codigo}-{ano}-{simbolo}")
        
        # Copia de combinações
        lista_combinacoes_copia = lista_combinacoes.copy()
        # Verificar se as combinações estão presentes em df_values
        for combinacao in lista_combinacoes:
            if combinacao not in df_values.columns:
                errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: A coluna '{combinacao}' é obrigatória.")

        # Verifica combinações extras somente para o código X-texto
        lista_combinacoes_sp_values = [col for col in df_values.columns if col.startswith(f"{codigo}-")]
        # Verificar se há combinações extras
        is_error, erros_message = verificar_combinacoes_extras(lista_combinacoes_copia, lista_combinacoes_sp_values)
        if is_error:
            for erro in erros_message:
                errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: A coluna '{erro}' é desnecessária.")

    return not errors, errors, []
