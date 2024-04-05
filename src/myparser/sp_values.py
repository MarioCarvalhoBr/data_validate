import os
from src.util.utilities import read_excel_file, dataframe_clean_numeric_values_less_than, check_file_exists

def extract_ids_from_description(df_description):
    ids = set(df_description['codigo'].astype(str))
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

def verify_ids_sp_description_values(path_sp_description, path_sp_values):
    errors = []
    warnings = []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)
    
    is_correct, error_message = check_file_exists(path_sp_values)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    try:

        df_description = read_excel_file(path_sp_description)
        # Verifica se as colunas com código existem
        if 'codigo' not in df_description.columns:
            return False, errors, []
        
        df_values = read_excel_file(path_sp_values)

        # Clean non numeric values
        df_description, _ = dataframe_clean_numeric_values_less_than(df_description, os.path.basename(path_sp_description), ['codigo'])

        id_description = extract_ids_from_description(df_description)
        id_values = extract_ids_from_values(df_values)

        errors += compare_ids(id_description, id_values, os.path.basename(path_sp_description), os.path.basename(path_sp_values))

    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Erro ao processar os arquivos: {e}.")

    
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
def verify_combination_sp_description_values_scenario_temporal_reference(path_sp_description, path_sp_values, path_sp_scenario, path_temporal_reference):
    errors = []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)
    
    is_correct, error_message = check_file_exists(path_sp_values)
    if not is_correct:
        errors.append(error_message)

    is_correct, error_message = check_file_exists(path_sp_scenario)
    if not is_correct:
        errors.append(error_message)
    
    is_correct, error_message = check_file_exists(path_temporal_reference)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []

    df_values = read_excel_file(path_sp_values)
    name_file_values = os.path.basename(path_sp_values)

    df_scenario = read_excel_file(path_sp_scenario)
    
    df_description = read_excel_file(path_sp_description)
    name_file_description = os.path.basename(path_sp_description)

    df_temporal_reference = read_excel_file(path_temporal_reference)
    name_file_temporal_reference = os.path.basename(path_temporal_reference)

    # Clean non numeric values
    df_description, _ = dataframe_clean_numeric_values_less_than(df_description, name_file_description, ['codigo'])
    df_temporal_reference, _ = dataframe_clean_numeric_values_less_than(df_temporal_reference, name_file_temporal_reference, ['simbolo'])

    # Verifica se as colunas com código e cenário existem
    if 'codigo' not in df_description.columns or 'cenario' not in df_description.columns:
        return False, errors, []
    
    # VErifica se as colunas obrigatórias de df_temporal_reference e df_scenario existem
    if 'simbolo' not in df_temporal_reference.columns:
        return False, errors, []

    if 'simbolo' not in df_scenario.columns:
        return False, errors, []

    # Verificar cada indicador em df_description
    for line, row in df_description.iterrows():

        # Criar lista de símbolos de cenários
        lista_simbolos_cenarios = df_scenario['simbolo'].unique().tolist()

        # Criar lista de símbolos temporais
        lista_simbolos_temporais = sorted(df_temporal_reference['simbolo'].unique().tolist())
        primeiro_ano = lista_simbolos_temporais[0]

        codigo = str(row['codigo']).replace(',', '')

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
                errors.append(f"{name_file_values}: A coluna '{combinacao}' é obrigatória.")

        # Verifica combinações extras somente para o código X-texto
        lista_combinacoes_sp_values = [col for col in df_values.columns if col.startswith(f"{codigo}-")]
        # Verificar se há combinações extras
        is_error, erros_message = verificar_combinacoes_extras(lista_combinacoes_copia, lista_combinacoes_sp_values)
        if is_error:
            for erro in erros_message:
                # Formata erros: errors.append(f"{name_file_values}: A combinação {combinacao} existe de forma extra para o indicador {codigo}.")
                errors.append(f"{name_file_values}: A coluna '{erro}' é desnecessária.")

    return not errors, errors, []
