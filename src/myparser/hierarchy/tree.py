import re
import pandas as pd
from src.util.utilities import read_excel_file, file_extension_check

def verificar_niveis_pai_filho(df_composicao):
    erros_niveis = [
        f"Erro de nível: Pai {row['codigo_pai']} (Nível {row['nivel_pai']}) e Filho {row['codigo_filho']} (Nível {row['nivel_filho']})"
        for _, row in df_composicao.iterrows() if row['nivel_filho'] - row['nivel_pai'] != 1
    ]
    return erros_niveis

# DFS: Depth-First Search ou Busca em Profundidade para verificar a existência de ciclos
def dfs(hierarquia, node, visitado, caminho_atual):
    if node in visitado:
        if node in caminho_atual:
            loop_index = caminho_atual.index(node)
            loop = caminho_atual[loop_index:]
            return True, f"Loop detectado: [{' -> '.join(map(str, loop))} -> {node}]"
        return False, None
    visitado.add(node)
    caminho_atual.append(node)
    for filho in hierarquia.get(node, []):
        loop_found, loop_message = dfs(hierarquia, filho, visitado, caminho_atual)
        if loop_found:
            return True, loop_message
    caminho_atual.pop()
    return False, None

def limpar_dados_numericos(df, name_file_composition):
    # Colunas para verificar se são numéricas
    colunas = ['codigo_pai', 'codigo_filho', 'nivel_pai', 'nivel_filho']
    erros = []

    # Verificar e eliminar linhas com valores não numéricos
    for coluna in colunas:
        # Verifica se a coluna contém valores não numéricos
        if not pd.to_numeric(df[coluna], errors='coerce').notnull().all():
            # Registra as linhas com valores não numéricos para a coluna atual
            linhas_invalidas = df[pd.to_numeric(df[coluna], errors='coerce').isnull()]
            if not linhas_invalidas.empty:
                erros.append(f"{name_file_composition}, linha {linhas_invalidas.index.tolist()[0]}: A coluna '{coluna}' deve conter apenas valores numéricos.")
            # Elimina linhas com valores não numéricos
            df = df[pd.to_numeric(df[coluna], errors='coerce').notnull()]

    if erros:
        # Se houver erros, adiciona uma mensagem geral
        erros.insert(0, f"{name_file_composition}: Os valores das colunas 'codigo_pai', 'codigo_filho', 'nivel_pai' e 'nivel_filho' devem ser numéricos.")
    
    return df, erros

def verify_tree_sp_composition_hierarchy(path_ps_composition):
    errors, warnings = [], []
    is_correct, error = file_extension_check(path_ps_composition)
    if not is_correct:
        return is_correct, [error], warnings
    
    df_composicao = read_excel_file(path_ps_composition)
    name_file_composition = path_ps_composition.split("/")[-1]

    # Limpar dados numéricos
    df_composicao, erros_numericos = limpar_dados_numericos(df_composicao, name_file_composition)

    if erros_numericos:
        errors.extend(erros_numericos)
    
    if not ((df_composicao['codigo_pai'] == 0) & (df_composicao['nivel_pai'] == 0)).any():
        # Imprimir a linha que o código_pai é 0 e o nível_pai é diferente de 0
        numero_da_linha = df_composicao[(df_composicao['codigo_pai'] == 0) & (df_composicao['nivel_pai'] != 0)].index[0] 
        errors.extend([f"{name_file_composition}, linha {numero_da_linha}: O valor da coluna 'nivel_pai' deve ser 0 (zero) quando o valor da coluna 'codigo_pai' for 0 (zero)."])

    hierarquia = {pai: list(filhos) for pai, filhos in df_composicao.groupby('codigo_pai')['codigo_filho']}
    
    erros_niveis = verificar_niveis_pai_filho(df_composicao)
    if erros_niveis:
        for erro in erros_niveis:
            # Use RE para extrair o número da linha
            dados = re.findall(r'\d+', erro)
            codigo_pai = int(dados[0])
            codigo_filho = int(dados[2])
            nivel_pai = int(dados[1])
            nivel_filho = int(dados[3])
            numero_da_linha = df_composicao[(df_composicao['codigo_pai'] == codigo_pai) & (df_composicao['codigo_filho'] == codigo_filho) & (df_composicao['nivel_pai'] == nivel_pai) & (df_composicao['nivel_filho'] == nivel_filho)].index[0]
            errors.append(f"{name_file_composition}, linha {numero_da_linha + 2}: {erro}.")

    loop_found, loop_message = dfs(hierarquia, 0, set(), [])
    if loop_found:
        errors.extend([f"{name_file_composition}: {loop_message}."])
    
    return not errors, errors, warnings
