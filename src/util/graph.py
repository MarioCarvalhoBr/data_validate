import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def ler_planilhas(path):
    planilha = pd.read_excel(path)
    return planilha

def verificar_codigos_ausentes_desc_comp(descricao, composicao):
    codigos_descricao = set(descricao['codigo'].astype(str))
    codigos_pai = set(composicao['codigo_pai'].astype(str))
    codigos_filho = set(composicao['codigo_filho'].astype(str))

    codigos_faltantes = (codigos_pai.union(codigos_filho) - codigos_descricao) - {'0'}
    return codigos_faltantes

def verificar_codigos_ausentes_comp_desc(composicao, descricao):
    codigos_descricao = set(descricao['codigo'].astype(str))
    codigos_pai = set(composicao['codigo_pai'].astype(str))
    codigos_filho = set(composicao['codigo_filho'].astype(str))

    codigos_faltantes = (codigos_descricao - codigos_pai.union(codigos_filho)) - {'0'}
    return codigos_faltantes


def plot_grafo(G, is_save=False):
    plt.figure(figsize=(24, 16))
    pos = nx.spring_layout(G)  # Posicionamento dos nós
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=2000, font_size=10, font_weight='bold')
    plt.title("Visualização do Grafo")
    if is_save:
        plt.savefig("grafo.pdf")
    plt.show()
    
def imprimir_grafo(G):
    text_graph = ""
    for origem, destino in G.edges():
        text_graph += f"{origem} -> {destino}, "
    # remove the last comma
    text_graph = text_graph[:-2]
    return text_graph
    
def montar_grafo(composicao):
    G = nx.DiGraph()
    for _, row in composicao.iterrows():
        G.add_edge(str(row['codigo_pai']), str(row['codigo_filho']))
    return G

def verificar_ciclos(G):
    try:
        ciclo = nx.find_cycle(G)
        return True, ciclo
    except nx.NetworkXNoCycle:
        return False, None

def verificar_grafos_desconectados(G):
    subgrafos = [G.subgraph(c).copy() for c in nx.weakly_connected_components(G)]
    subgrafos.sort(key=len, reverse=True)
    return subgrafos[1:] if len(subgrafos) > 1 else []

def run(path_sp_description, path_ps_composition):
    errors = []
    warnings = []
    is_valid = True
    
    # Execução do script
    descricao = ler_planilhas(path_sp_description)
    composicao = ler_planilhas(path_ps_composition)
    name_file_description = path_sp_description.split("/")[-1]
    name_file_composition = path_ps_composition.split("/")[-1]
    
    codigos_faltantes = verificar_codigos_ausentes_desc_comp(descricao, composicao)
    if codigos_faltantes:
        # Remove '{}'
        codigos_faltantes = str(codigos_faltantes)[1:-1]
        # Remove ''
        codigos_faltantes = codigos_faltantes.replace("'", "")
        errors.append(f"{name_file_description}: Indicadores do arquivo {name_file_composition} que não estão descritos: [{str(codigos_faltantes)}]")
        is_valid = False
    
    codigos_faltantes = []
    codigos_faltantes = verificar_codigos_ausentes_comp_desc(composicao, descricao)
    if codigos_faltantes:
        # Remove '{}'
        codigos_faltantes = str(codigos_faltantes)[1:-1]
        # Remove ''
        codigos_faltantes = codigos_faltantes.replace("'", "")
        errors.append(f"{name_file_composition}: Indicadores do arquivo {name_file_description} que não fazem parte da estrutura hierárquica: [{str(codigos_faltantes)}]")
        is_valid = False

    G = montar_grafo(composicao)
    existe_ciclo, ciclo = verificar_ciclos(G)
    if existe_ciclo:
        # errors.append("Ciclo encontrado: " + str(ciclo))
        # Imprimir o Ciclo na forma XXXX->XXXX->XXXX e YYYY->YYYY->YYYY
        text_graph = ""
        for origem, destino in ciclo:
            text_graph += f"{origem} -> {destino}, "
        # remove the last comma
        text_graph = text_graph[:-2]
        errors.append(f"{name_file_composition}: Ciclo encontrado no arquivo {name_file_composition}: [{text_graph}]")
        is_valid = False

    grafos_desconectados = verificar_grafos_desconectados(G)
    if grafos_desconectados:
        is_valid = False        
        for i, sg in enumerate(grafos_desconectados, 1):
            errors.append(f"{name_file_composition}: Indicadores desconectados encontrados: Indicadores " + str(i) + ": [" + imprimir_grafo(sg) + "]")
    
    return is_valid, errors, warnings