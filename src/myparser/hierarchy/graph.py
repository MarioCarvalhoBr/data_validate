import networkx as nx
from src.util.utilities import read_excel_file, dataframe_clean_numeric_values_less_than, check_file_exists

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

# Function to plot: 
'''
def plot_grafo(G, is_save=False):
    plt.figure(figsize=(24, 16))
    pos = nx.spring_layout(G)  # Posicionamento dos nós
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=2000, font_size=10, font_weight='bold')
    plt.title("Visualização do Grafo")
    if is_save:
        plt.savefig("grafo.pdf")
    plt.show()
'''
    
def imprimir_grafo(G):
    text_graph = ""
    for origem, destino in G.edges():
        origem = float(origem)
        destino = float(destino)
        origem = int(origem) if origem.is_integer() else origem
        destino = int(destino) if destino.is_integer() else destino
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

def verify_graph_sp_description_composition(path_sp_description, path_sp_composition):
    errors = []
    warnings = []
    is_valid = True

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
    
    composicao = read_excel_file(path_sp_composition)
    name_file_composition = path_sp_composition.split("/")[-1]

    # Verificar se as colunas com código existem
    if 'codigo_pai' not in composicao.columns or 'codigo_filho' not in composicao.columns:
        errors.append(f"{name_file_composition}: Verificação de hierarquia de composição como grafo não realizada.")
        return False, errors, warnings
    
    # Limpando os dados
    composicao, _ = dataframe_clean_numeric_values_less_than(composicao, name_file_composition, ['codigo_pai'], 0)
    composicao, _ = dataframe_clean_numeric_values_less_than(composicao, name_file_composition, ['codigo_filho'], 1)
    
    descricao = read_excel_file(path_sp_description)
    # Verifica se as colunas com código existem
    if 'codigo' not in descricao.columns or 'nivel' not in descricao.columns:
        return False, errors, warnings
    
    name_file_description = path_sp_description.split("/")[-1]
    # Limpando os dados
    descricao, _ = dataframe_clean_numeric_values_less_than(descricao, name_file_description, ['codigo', 'nivel'], 1)
    
    codigos_faltantes = verificar_codigos_ausentes_desc_comp(descricao, composicao)
    if codigos_faltantes:
        # Remove '{}'
        codigos_faltantes = str(codigos_faltantes)[1:-1]
        
        # Remove ''
        codigos_faltantes = codigos_faltantes.replace("'", "")
        
        # Códigos falantes ordenados em ordem ascendente
        codigos_faltantes = sorted(codigos_faltantes.split(", "), key=lambda x: int(x), reverse=False)
        
        # Remove as ''
        codigos_faltantes = [int(codigo) for codigo in codigos_faltantes]

        errors.append(f"{name_file_description}: Indicadores no arquivo {name_file_composition} que não estão descritos: {str(codigos_faltantes)}.")
        is_valid = False
    
    codigos_faltantes = []
    codigos_faltantes = verificar_codigos_ausentes_comp_desc(composicao, descricao)
    if codigos_faltantes:
        # Remove '{}'
        codigos_faltantes = str(codigos_faltantes)[1:-1]
        
        # Remove ''
        codigos_faltantes = codigos_faltantes.replace("'", "")
        
        # Códigos falantes ordenados em ordem ascendente
        codigos_faltantes = sorted(codigos_faltantes.split(", "), key=lambda x: int(x), reverse=False)
        
        # Remove as ''
        codigos_faltantes = [int(codigo) for codigo in codigos_faltantes]

        errors.append(f"{name_file_composition}: Indicadores no arquivo {name_file_description} que não fazem parte da estrutura hierárquica: {str(codigos_faltantes)}.")
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
        errors.append(f"{name_file_composition}: Ciclo encontrado: [{text_graph}].")
        is_valid = False

    grafos_desconectados = verificar_grafos_desconectados(G)
    if grafos_desconectados:
        is_valid = False
        text_init = f"{name_file_composition}: Indicadores desconectados encontrados: "
        lista_grafos_desconectados = []
        for i, grafo in enumerate(grafos_desconectados):
            text_graph = "[" + imprimir_grafo(grafo) + "]"
            lista_grafos_desconectados.append(text_graph)    
        errors.append(text_init + ", ".join(lista_grafos_desconectados) + ".")
    
    return is_valid, errors, warnings
