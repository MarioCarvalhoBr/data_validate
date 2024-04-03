import networkx as nx
import os
from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01

from src.myparser.hierarchy.graph import verificar_ciclos
from src.myparser.hierarchy.graph import verificar_grafos_desconectados
from src.myparser.hierarchy.graph import imprimir_grafo
from src.myparser.hierarchy.graph import verify_graph_sp_description_composition

# Testes: Hierarquia como grafo conexo
def test_true_verify_graph_sp_description_composition(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    planilha_05_composicao = path_input_data_ground_truth + "/composicao.xlsx"
    result_test,__,__ = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    assert result_test is True
def test_false_verify_graph_sp_description_composition(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    planilha_05_composicao = path_input_data_errors_01 + "/composicao.xlsx"
    result_test,__,__ = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    assert result_test is False
def test_count_errors_verify_graph_sp_description_composition(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    planilha_05_composicao = path_input_data_errors_01 + "/composicao.xlsx"
    is_correct, errors, warnings = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    # Numero de erros esperado == 4
    assert len(errors) == 4
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
    
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
