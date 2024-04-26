import networkx as nx

from src.myparser.hierarchy.graph import verificar_ciclos
from src.myparser.hierarchy.graph import verificar_grafos_desconectados
from src.myparser.hierarchy.graph import imprimir_grafo
from src.myparser.hierarchy.graph import verify_graph_sp_description_composition

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_description_errors_01, df_sp_composition_errors_01

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04, df_sp_composition_errors_04

def test_true_verify_graph_sp_description_composition_data_ground_truth_01():
    is_correct, errors, warnings = verify_graph_sp_description_composition(df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_graph_sp_description_composition_errors_01():
    is_correct, errors, warnings = verify_graph_sp_description_composition(df_sp_description_errors_01, df_sp_composition_errors_01)
    assert is_correct is False
    assert len(errors) == 4
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx: Indicadores no arquivo composicao.xlsx que não estão descritos: [55, 77, 5001, 5002, 5010, 5022, 5033]."
    assert errors[1] == "composicao.xlsx: Indicadores no arquivo descricao.xlsx que não fazem parte da estrutura hierárquica: [5005]."
    assert errors[2] == "composicao.xlsx: Ciclo encontrado: [5000 -> 5001, 5001 -> 5000]."
    assert errors[3] == "composicao.xlsx: Indicadores desconectados encontrados: [5033 -> 5010]."

def test_count_errors_verify_graph_sp_description_composition_errors_04():
    is_correct, errors, warnings = verify_graph_sp_description_composition(df_sp_description_errors_04, df_sp_composition_errors_04)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx: Indicadores no arquivo composicao.xlsx que não estão descritos: [2, 5000, 5001]."
    assert errors[1] == "composicao.xlsx: Indicadores no arquivo descricao.xlsx que não fazem parte da estrutura hierárquica: [5002]."
    assert errors[2] == "composicao.xlsx: Indicadores desconectados encontrados: [5004 -> 5006, 5004 -> 5007]."
    
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
