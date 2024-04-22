from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe
from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS 

import pandas as pd
def criar_arvore(composicao):
    arvore = {}
    for _, row in composicao.iterrows():
        pai = str(row[SP_COMPOSITION_COLUMNS.CODIGO_PAI])
        filho = str(row[SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
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
    niveis = {(row[SP_DESCRIPTION_COLUMNS.CODIGO]): row[SP_DESCRIPTION_COLUMNS.NIVEL] for _, row in descricao.iterrows()}
    for _, row in composicao.iterrows():
        pai = (row[SP_COMPOSITION_COLUMNS.CODIGO_PAI])
        filho = (row[SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
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

def verify_tree_sp_description_composition_hierarchy(df_composicao, df_descricao):
    df_composicao = df_composicao.copy()
    df_descricao = df_descricao.copy()
    
    errors, warnings = [], []
    
    # Verifica se as colunas codigo_pai e codigo_filho existem
    if SP_COMPOSITION_COLUMNS.CODIGO_PAI not in df_composicao.columns or SP_COMPOSITION_COLUMNS.CODIGO_FILHO not in df_composicao.columns:
        errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Verificação de hierarquia de composição não realizada.")
        return not errors, errors, warnings
    
    df_composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0)
    df_composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1)
    
    # Verifica se a coluna codigo e nivel existem
    if SP_DESCRIPTION_COLUMNS.CODIGO not in df_descricao.columns or SP_DESCRIPTION_COLUMNS.NIVEL not in df_descricao.columns:
        errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de hierarquia de composição não realizada.")
        return not errors, errors, warnings
    
    df_descricao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(df_descricao, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL], 1)
    
    if not ((df_composicao[SP_COMPOSITION_COLUMNS.CODIGO_PAI] == 0)).any():
        errors.extend([f"{SP_COMPOSITION_COLUMNS.NAME_SP}: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' deve conter pelo menos um valor igual a 0 para ser a raiz da árvore."])

    # Fix para adicionar a raiz da árvore
    if not ((df_descricao[SP_DESCRIPTION_COLUMNS.CODIGO] == 0)).any():
        # Adiciona a a linha com codigo=0 e nivel=0																						
        df_descricao = pd.concat([df_descricao, pd.DataFrame([[0,0,0,0,0,0,0,0,0,0,0]], columns=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META])], ignore_index=True)
    
    arvore = criar_arvore(df_composicao)
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    if ciclo_encontrado:
        errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Ciclo encontrado: [{' -> '.join(ciclo)}].")
    
    erros_niveis = verificar_erros_niveis(df_composicao, df_descricao)
    if erros_niveis:
        for pai, filho in erros_niveis:
            if (filho is not None) and (pai is not None): 
                linha_relacionada = df_composicao[(df_composicao[SP_COMPOSITION_COLUMNS.CODIGO_PAI] == int(pai)) & (df_composicao[SP_COMPOSITION_COLUMNS.CODIGO_FILHO] == int(filho))].index.tolist()[0]
                index_linha = linha_relacionada + 2
                
                # Forma 2: composicao.xlsx, linha {}: O indicador {} (nível {}) não pode ser pai do indicador {} (nível {}).
                nivel_pai = df_descricao[df_descricao[SP_DESCRIPTION_COLUMNS.CODIGO] == int(pai)][SP_DESCRIPTION_COLUMNS.NIVEL].values[0]
                nivel_filho = df_descricao[df_descricao[SP_DESCRIPTION_COLUMNS.CODIGO] == int(filho)][SP_DESCRIPTION_COLUMNS.NIVEL].values[0]
                errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}, linha {index_linha}: O indicador {pai} (nível {nivel_pai}) não pode ser pai do indicador {filho} (nível {nivel_filho}).")
    return not errors, errors, warnings
