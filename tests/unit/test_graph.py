import networkx as nx

from src.myparser.graph import verificar_ciclos
from src.myparser.graph import verificar_grafos_desconectados
from src.myparser.graph import imprimir_grafo

def test_imprimir_grafo_with_no_edges():
    G = nx.DiGraph()
    result = imprimir_grafo(G)
    assert result == ""

def test_imprimir_grafo_with_one_edge():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    result = imprimir_grafo(G)
    assert result == "1 -> 2"

def test_imprimir_grafo_with_multiple_edges():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    result = imprimir_grafo(G)
    assert result == "1 -> 2, 2 -> 3"

def test_imprimir_grafo_with_self_loop():
    G = nx.DiGraph()
    G.add_edge(1, 1)
    result = imprimir_grafo(G)
    assert result == "1 -> 1"
    
def test_verificar_grafos_desconectados_with_disconnected_graphs():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(4, 5)
    disconnected_graphs = verificar_grafos_desconectados(G)
    assert len(disconnected_graphs) == 1
    assert len(disconnected_graphs[0]) == 2

def test_verificar_grafos_desconectados_with_connected_graph():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    disconnected_graphs = verificar_grafos_desconectados(G)
    assert len(disconnected_graphs) == 0

def test_verificar_grafos_desconectados_with_multiple_disconnected_graphs():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(4, 5)
    G.add_edge(6, 7)
    disconnected_graphs = verificar_grafos_desconectados(G)
    assert len(disconnected_graphs) == 2
    assert len(disconnected_graphs[0]) == 2
    assert len(disconnected_graphs[1]) == 2

def test_verificar_ciclos_with_cycle():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 1)
    has_cycle, cycle = verificar_ciclos(G)
    assert has_cycle is True
    assert len(cycle) == 3

def test_verificar_ciclos_without_cycle():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    has_cycle, cycle = verificar_ciclos(G)
    assert has_cycle is False
    assert cycle is None

def test_verificar_ciclos_with_self_loop():
    G = nx.DiGraph()
    G.add_edge(1, 1)
    has_cycle, cycle = verificar_ciclos(G)
    assert has_cycle is True
    assert len(cycle) == 1