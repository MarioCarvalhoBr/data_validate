import networkx as nx
from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe, check_validate_columns
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS, SP_PROPORTIONALITIES_COLUMNS

'''
# Function to plot: 
import matplotlib.pyplot as plt
def plot_grafo(G, is_save=False):
    plt.figure(figsize=(24, 16))
    pos = nx.spring_layout(G)  # Posicionamento dos nós
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=2000, font_size=10, font_weight='bold')
    plt.title("Visualização do Grafo")
    if is_save:
        plt.savefig("grafo.pdf")
    plt.show()
'''

def get_codigos_ausentes_desc_comp(descricao, composicao):
    codigos_descricao = set(descricao[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str))
    codigos_pai = set(composicao[SP_COMPOSITION_COLUMNS.CODIGO_PAI].astype(str))
    codigos_filho = set(composicao[SP_COMPOSITION_COLUMNS.CODIGO_FILHO].astype(str))

    codigos_faltantes = (codigos_pai.union(codigos_filho) - codigos_descricao) - {'0'}
    return codigos_faltantes

def get_codigos_ausentes_comp_desc(composicao, descricao):
    codigos_descricao = set(descricao[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str))
    codigos_pai = set(composicao[SP_COMPOSITION_COLUMNS.CODIGO_PAI].astype(str))
    codigos_filho = set(composicao[SP_COMPOSITION_COLUMNS.CODIGO_FILHO].astype(str))

    codigos_faltantes = (codigos_descricao - codigos_pai.union(codigos_filho)) - {'0'}
    return codigos_faltantes
 
def montar_grafo(composicao):
    G = nx.DiGraph()
    for _, row in composicao.iterrows():
        G.add_edge(str(row[SP_COMPOSITION_COLUMNS.CODIGO_PAI]), str(row[SP_COMPOSITION_COLUMNS.CODIGO_FILHO]))
    return G
    
def imprimir_grafo(G):
    text_graph = []
    for origem, destino in G.edges():
        origem = float(origem)
        destino = float(destino)
        origem = int(origem) if origem.is_integer() else origem
        destino = int(destino) if destino.is_integer() else destino
        text_graph.append(f"{origem} -> {destino}")
    
    # Ordenação das sub-arvores usando o menor pai até o maior pai.
    text_graph = sorted(text_graph, key=lambda x: x, reverse=False)
    full_text_graph = ", ".join(text_graph)
    return full_text_graph
   
def check_ciclos(G):
    try:
        ciclo = nx.find_cycle(G)
        return True, ciclo
    except nx.NetworkXNoCycle:
        return False, None

def check_grafos_desconectados(G):
    subgrafos = [G.subgraph(c).copy() for c in nx.weakly_connected_components(G)]
    subgrafos.sort(key=len, reverse=True)
    return subgrafos[1:] if len(subgrafos) > 1 else []

def check_sp_description_titles_uniques(df):
    df = df.copy()
    errors = []

    if df.empty:
        return errors
    for column in [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]:
        
        # Verifica se a coluna existe
        if column not in df.columns:
            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de títulos únicos foi abortada porque a coluna '{column}' está ausente.")
            continue
        
        # Convert to string
        df[column] = df[column].astype(str).str.strip()
        duplicated = df[column].duplicated().any()

        if duplicated:
            titles_duplicated = df[df[column].duplicated()][column].tolist()
            # Rename columns to plural
            if column == SP_DESCRIPTION_COLUMNS.NOME_SIMPLES:
                column = SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_SIMPLES
            elif column == SP_DESCRIPTION_COLUMNS.NOME_COMPLETO:
                column = SP_DESCRIPTION_COLUMNS.PLURAL_NOMES_COMPLETOS

            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Existem {column.replace('_', ' ')} duplicados: {titles_duplicated}.")

    return errors
    
def get_indicadores_folhas(G):
    folhas = []
    for node in G.nodes():
        if G.out_degree(node) == 0:
            folhas.append(node)
    return folhas

def verify_graph_sp_description_composition(descricao, composicao):
    errors, warnings = [], []
    try:
        descricao = descricao.copy()
        composicao = composicao.copy()

        # Se for empty, retorna True
        if descricao.empty or composicao.empty:
            return True, errors, warnings

        # Validação das colunas esperadas
        __, errors_description = check_validate_columns(SP_DESCRIPTION_COLUMNS.NAME_SP, descricao.columns.tolist(), [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL])
        __, errors_composition = check_validate_columns(SP_COMPOSITION_COLUMNS.NAME_SP, composicao.columns.tolist(), [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
        errors.extend(errors_description)
        errors.extend(errors_composition)
        if errors:
            return not errors, errors, warnings
        
        # Limpando os dados
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0)
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1)
        
        # Limpando os dados
        descricao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(descricao, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL], 1)
        
        codigos_faltantes = get_codigos_ausentes_desc_comp(descricao, composicao)
        if codigos_faltantes:
            # Remove '{}'
            codigos_faltantes = str(codigos_faltantes)[1:-1]
            
            # Remove ''
            codigos_faltantes = codigos_faltantes.replace("'", "")
            
            # Códigos falantes ordenados em ordem ascendente
            codigos_faltantes = sorted(codigos_faltantes.split(", "), key=lambda x: int(x), reverse=False)
            
            # Remove as ''
            codigos_faltantes = [int(codigo) for codigo in codigos_faltantes]

            errors.append(f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Indicadores no arquivo {SP_COMPOSITION_COLUMNS.NAME_SP} que não estão descritos: {str(codigos_faltantes)}.")
        
        codigos_faltantes = []
        codigos_faltantes = get_codigos_ausentes_comp_desc(composicao, descricao)
        if codigos_faltantes:
            # Remove '{}'
            codigos_faltantes = str(codigos_faltantes)[1:-1]
            
            # Remove ''
            codigos_faltantes = codigos_faltantes.replace("'", "")
            
            # Códigos falantes ordenados em ordem ascendente
            codigos_faltantes = sorted(codigos_faltantes.split(", "), key=lambda x: int(x), reverse=False)
            
            # Remove as ''
            codigos_faltantes = [int(codigo) for codigo in codigos_faltantes]

            errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Indicadores no arquivo {SP_DESCRIPTION_COLUMNS.NAME_SP} que não fazem parte da estrutura hierárquica: {str(codigos_faltantes)}.")

        G = montar_grafo(composicao)
        existe_ciclo, ciclo = check_ciclos(G)
        if existe_ciclo:
            # errors.append("Ciclo encontrado: " + str(ciclo))
            # Imprimir o Ciclo na forma XXXX->XXXX->XXXX e YYYY->YYYY->YYYY
            text_graph = ""
            for origem, destino in ciclo:
                text_graph += f"{origem} -> {destino}, "
            # remove the last comma
            text_graph = text_graph[:-2]
            errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Ciclo encontrado: [{text_graph}].")

        grafos_desconectados = check_grafos_desconectados(G)
        if grafos_desconectados:
            text_init = f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Indicadores desconectados encontrados: "
            lista_grafos_desconectados = []
            for i, grafo in enumerate(grafos_desconectados):
                text_graph = "[" + imprimir_grafo(grafo) + "]"
                lista_grafos_desconectados.append(text_graph)    
            errors.append(text_init + ", ".join(lista_grafos_desconectados) + ".")
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_COMPOSITION_COLUMNS.NAME_SP}: {e}.")

    return not errors, errors, warnings

def verify_unique_titles_description_composition(descricao, composicao):
    errors, warnings = [], []
    try:
        descricao = descricao.copy()
        composicao = composicao.copy()

        # Se for empty, retorna True
        if descricao.empty or composicao.empty:
            return True, errors, warnings
        
        # Validação das colunas esperadas
        # Validação das colunas esperadas
        __, errors_description = check_validate_columns(SP_DESCRIPTION_COLUMNS.NAME_SP, descricao.columns.tolist(), [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL])
        __, errors_composition = check_validate_columns(SP_COMPOSITION_COLUMNS.NAME_SP, composicao.columns.tolist(), [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
        errors.extend(errors_description)
        errors.extend(errors_composition)
        if errors:
            return not errors, errors, warnings
        
        # Limpando os dados
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0)
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1)
        
        # Limpando os dados
        descricao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(descricao, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL], 1)
        
        codigos_faltantes = get_codigos_ausentes_desc_comp(descricao, composicao)
        if codigos_faltantes:
            return not errors, errors, warnings
        
        codigos_faltantes = get_codigos_ausentes_comp_desc(composicao, descricao)
        if codigos_faltantes:
            return not errors, errors, warnings

        # Montar o grafo
        G = montar_grafo(composicao)

        existe_ciclo, __ = check_ciclos(G)
        if existe_ciclo:
            return not errors, errors, warnings

        grafos_desconectados = check_grafos_desconectados(G)
        if grafos_desconectados:
            return not errors, errors, warnings
        
        # Verifica se existe pelo menos 1 nó pai == 1, senão, mostrar erro e solicitar correção
        if not G.has_node('1'):
            errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Nó raiz '1' não encontrado.")
            return not errors, errors, warnings
        
        # Convert the graph to a tree
        tree = nx.bfs_tree(G, '1')
        
        # Todos os filhos de 1
        filhos_1 = list(tree.neighbors('1'))

        # Para cada filho de 1, pegar toda a sub-arvore abaixo
        for filho in filhos_1:
            
            # Rodar um BFS a partir do filho
            sub_arvore = nx.bfs_tree(G, filho)
            
            # Monta uma lista somente com os código dos nós
            lista_nos = list(sub_arvore.nodes())

            # Busca todos um sub-dataframe de descrição com os códigos (SP_DESCRIPTION_COLUMNS.CODIGO) que estão na lista_nos
            sub_descricao = descricao[descricao[SP_DESCRIPTION_COLUMNS.CODIGO].astype(str).isin(lista_nos)]
            
            # Check if the titles are unique
            warnings_i = check_sp_description_titles_uniques(sub_descricao)
            warnings += warnings_i
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_COMPOSITION_COLUMNS.NAME_SP}: {e}.")

    return not errors, errors, warnings

def verify_graph_sp_description_composition_values_proportionalities_leafs(descricao, composicao, valores, proporcionalidades):
    errors, warnings = [], []
    try:
        descricao = descricao.copy()
        composicao = composicao.copy()
        valores = valores.copy()

        # Se for empty, retorna True
        if descricao.empty or composicao.empty or valores.empty:
            return True, errors, warnings
        
        if not proporcionalidades.empty:
            proporcionalidades = proporcionalidades.copy()

        # Validação das colunas esperadas
        __, errors_description = check_validate_columns(SP_DESCRIPTION_COLUMNS.NAME_SP, descricao.columns.tolist(), [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL])
        __, errors_composition = check_validate_columns(SP_COMPOSITION_COLUMNS.NAME_SP, composicao.columns.tolist(), [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
        __, errors_values = check_validate_columns(SP_DESCRIPTION_COLUMNS.NAME_SP, valores.columns.tolist(), [SP_VALUES_COLUMNS.ID])
        errors.extend(errors_description)
        errors.extend(errors_composition)
        errors.extend(errors_values)
        if not proporcionalidades.empty:
            # SOMENTE COLUNAS NIVEL 2
            __, errors_prop = check_validate_columns(SP_PROPORTIONALITIES_COLUMNS.NAME_SP, proporcionalidades.columns.get_level_values(1).unique().tolist(), [SP_PROPORTIONALITIES_COLUMNS.ID])
            errors.extend(errors_prop)

        if errors:
            return not errors, errors, warnings
        
        # Limpando os dados
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0)
        composicao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(composicao, SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1)
        descricao, _ = clean_non_numeric_and_less_than_value_integers_dataframe(descricao, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL], 1)
        
        # Montar o grafo
        G = montar_grafo(composicao)
        folhas = get_indicadores_folhas(G) 
        
        # VALIDACAO PARA VALORES
        codigos_valores = valores.columns.tolist()
        codigo_valores = [codigo.split('-')[0] for codigo in codigos_valores]
        for folha in folhas:
            if folha not in codigo_valores:
                errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Indicador folha '{folha}' não tem dados associados na planilha {SP_VALUES_COLUMNS.NAME_SP}.")

        # VALIDACAO PARA PROPORCIONALIDADES (se existir)
        if not proporcionalidades.empty:
            # Lista com todos as colunas nivel 1
            level_two_columns = proporcionalidades.columns.get_level_values(1).unique().tolist()

            # Verifica se id existe em level_two_columns
            if SP_PROPORTIONALITIES_COLUMNS.ID in level_two_columns:
                level_two_columns.remove(SP_PROPORTIONALITIES_COLUMNS.ID)
            
            level_two_columns = [col for col in level_two_columns if not col.startswith('Unnamed')]
            level_two_columns = [col for col in level_two_columns if not col.startswith('unnamed')]
            
            level_two_columns = [col.split('-')[0] for col in level_two_columns]
            all_columns = list(set(level_two_columns))

            # Verifica se todos os códigos folhas estão presentes em level_one_columns
            for folha in folhas:
                if folha not in all_columns:
                    errors.append(f"{SP_COMPOSITION_COLUMNS.NAME_SP}: Indicador folha '{folha}' não tem dados associados na planilha {SP_PROPORTIONALITIES_COLUMNS.NAME_SP}.")
          
    except Exception as e:
            errors.append(f"Erro ao processar o arquivo {SP_COMPOSITION_COLUMNS.NAME_SP}: {e}.")

    return not errors, errors, warnings
