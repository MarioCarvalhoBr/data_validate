from src.util.utilities import read_excel_file, dataframe_clean_numeric_values_less_than, check_file_exists
import pandas as pd
def criar_arvore(composicao):
    arvore = {}
    for _, row in composicao.iterrows():
        pai = str(row['codigo_pai']).replace(',', '')
        filho = str(row['codigo_filho']).replace(',', '')
        if pai not in arvore:
            arvore[pai] = []
        arvore[pai].append(filho)
    return arvore

def dfs(arvore, node, visitado, caminho_atual):
    if node in visitado:
        if node in caminho_atual:
            return True, caminho_atual[caminho_atual.index(node):] + [node]
        return False, []
    visitado.add(node)
    caminho_atual.append(node)
    for filho in arvore.get(node, []):
        ciclo_encontrado, ciclo = dfs(arvore, filho, visitado, caminho_atual)
        if ciclo_encontrado:
            return True, ciclo
    caminho_atual.pop()
    return False, []

def verificar_ciclos(arvore):
    visitado = set()
    for node in arvore:
        ciclo_encontrado, ciclo = dfs(arvore, node, visitado, [])
        if ciclo_encontrado:
            return True, ciclo
    return False, []

def verificar_erros_niveis(composicao, descricao):
    erros = []
    niveis = {(row['codigo']): row['nivel'] for _, row in descricao.iterrows()}
    for _, row in composicao.iterrows():
        pai = (row['codigo_pai'])
        filho = (row['codigo_filho'])
        nivel_pai = niveis.get(pai, None)
        nivel_filho = niveis.get(filho, None)
        
        # Verifica se é none
        if nivel_pai is None:
            erros.append((pai, None))
        elif nivel_filho is None:
            erros.append((None, filho))
        elif nivel_pai >= nivel_filho:
            erros.append((pai, filho))
    return erros

def verify_tree_sp_description_composition_hierarchy(path_sp_composition, path_sp_description):
    errors, warnings = [], []

    # Verificar se os arquivos existem
    is_correct, error_message = check_file_exists(path_sp_description)
    if not is_correct:
        errors.append(error_message)
    
    is_correct, error_message = check_file_exists(path_sp_composition)
    if not is_correct:
        errors.append(error_message)

    # Verifica se há erros
    if errors:
        return False, errors, []
    
    df_composicao = read_excel_file(path_sp_composition)
    name_file_composition = path_sp_composition.split("/")[-1]
    df_composicao, _ = dataframe_clean_numeric_values_less_than(df_composicao, name_file_composition, ['codigo_pai'], 0)
    df_composicao, _ = dataframe_clean_numeric_values_less_than(df_composicao, name_file_composition, ['codigo_filho'], 1)
    
    df_descricao = read_excel_file(path_sp_description)
    name_file_description = path_sp_description.split("/")[-1]
    df_descricao, _ = dataframe_clean_numeric_values_less_than(df_descricao, name_file_description, ['codigo', 'nivel'], 1)
    
    if not ((df_composicao['codigo_pai'] == 0)).any():
        errors.extend([f"{name_file_composition}: A coluna 'codigo_pai' deve conter pelo menos um valor igual a 0 para ser a raiz da árvore."])

    if not ((df_descricao['codigo'] == 0)).any():
        # Adiciona a a linha com codigo=0 e nivel=0																						
        df_descricao = pd.concat([df_descricao, pd.DataFrame([[0,0,0,0,0,0,0,0,0,0,0]], columns=['codigo', 'nivel', 'nome_simples', 'nome_completo', 'unidade', 'desc_simples','desc_completa', 'cenario', 'relacao', 'fontes', 'meta'])], ignore_index=True)
    
    arvore = criar_arvore(df_composicao)
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    if ciclo_encontrado:
        # print(f"Ciclo encontrado: {' -> '.join(ciclo)}")
        errors.append(f"{name_file_composition}: Ciclo encontrado: [{' -> '.join(ciclo)}].")
    
    erros_niveis = verificar_erros_niveis(df_composicao, df_descricao)
    if erros_niveis:
        for pai, filho in erros_niveis:
            if (filho is not None) and (pai is not None): 
                linha_relacionada = df_composicao[(df_composicao['codigo_pai'] == int(pai)) & (df_composicao['codigo_filho'] == int(filho))].index.tolist()[0]
                index_linha = linha_relacionada + 2
                
                # Forma 2: composicao.xlsx, linha {}: O indicador {} (nível {}) não pode ser pai do indicador {} (nível {}).
                nivel_pai = df_descricao[df_descricao['codigo'] == int(pai)]['nivel'].values[0]
                nivel_filho = df_descricao[df_descricao['codigo'] == int(filho)]['nivel'].values[0]
                errors.append(f"{name_file_composition}, linha {index_linha}: O indicador {pai} (nível {nivel_pai}) não pode ser pai do indicador {filho} (nível {nivel_filho}).")
    return not errors, errors, warnings
