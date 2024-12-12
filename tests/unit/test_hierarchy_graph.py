import networkx as nx
import pandas as pd
from src.myparser.hierarchy.graph import check_ciclos
from src.myparser.hierarchy.graph import check_grafos_desconectados
from src.myparser.hierarchy.graph import imprimir_grafo
from src.myparser.hierarchy.graph import verify_graph_sp_description_composition
from src.myparser.hierarchy.graph import verify_unique_titles_description_composition
from src.myparser.hierarchy.graph import verify_graph_sp_description_composition_values_proportionalities_leafs

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_proportionalities_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_description_errors_01, df_sp_composition_errors_01

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04, df_sp_composition_errors_04
# DATA FRAMES  - ERROS 10
from tests.unit.test_constants import df_sp_description_errors_10, df_sp_composition_errors_10
# DATA FRAMES - ERROS 14
from tests.unit.test_constants import df_sp_description_errors_14, df_sp_composition_errors_14
# DATA FRAMES - ERROR 15:
from tests.unit.test_constants import df_sp_description_errors_15, df_sp_composition_errors_15, df_sp_values_errors_15, df_sp_proportionalities_errors_15

from tests.unit.test_constants import SP_DESCRIPTION_COLUMNS


# Testes: verify_unique_titles_description_composition
def test_true_verify_sp_description_titles_uniques_data_data_ground_truth_01():
    is_correct, errors, warnings = verify_unique_titles_description_composition(df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_titles_uniques_data_errors_14():
    is_correct, errors, warnings = verify_unique_titles_description_composition(df_sp_description_errors_14, df_sp_composition_errors_14)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 4

    assert warnings[0] == "descricao.xlsx: Existem nomes simples duplicados: ['Seca']."
    assert warnings[1] == "descricao.xlsx: Existem nomes completos duplicados: ['Índice de risco de impacto para seca']."
    assert warnings[2] == "descricao.xlsx: Existem nomes simples duplicados: ['Sensibilidade']."
    assert warnings[3] == "descricao.xlsx: Existem nomes completos duplicados: ['Índice de sensibilidade']."

def test_verify_ids_sp_description_values_column_missing():
    df_description = pd.DataFrame({
        'other_column': ['a', 'b', 'c']
    })
    df_composition = pd.DataFrame({
        'codigo_pai': ['1', '1', '1'],
        'codigo_filho': ['2', '3', '4']
    })
    
    errors = []
    warnings = []

    result, errors, warnings = verify_graph_sp_description_composition(df_description, df_composition)

    expected_error = f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação não realizada, pois as colunas '{SP_DESCRIPTION_COLUMNS.CODIGO}' e '{SP_DESCRIPTION_COLUMNS.NIVEL}' não foram encontradas."
    
    assert result is False
    assert errors == [expected_error]
    assert warnings == []

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

def test_count_errors_verify_graph_sp_description_composition_errors_10():
    is_correct, errors, warnings = verify_graph_sp_description_composition(df_sp_description_errors_10, df_sp_composition_errors_10)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
    # Exibir o o sub-grafo de forma ordenada
    assert errors[0] == "composicao.xlsx: Indicadores desconectados encontrados: [1 -> 2, 2 -> 4, 2 -> 5]."

# Testes: verify_graph_sp_description_composition_values_proportionalities_leafs
def test_true_verify_graph_sp_description_composition_values_proportionalities_leafs_data_ground_truth_01():
    is_correct, errors, warnings = verify_graph_sp_description_composition_values_proportionalities_leafs(df_sp_description_data_ground_truth_01, df_sp_composition_data_ground_truth_01, df_sp_values_data_ground_truth_01, df_sp_proportionalities_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_graph_sp_description_composition_values_proportionalities_leafs_errors_15():
    is_correct, errors, warnings = verify_graph_sp_description_composition_values_proportionalities_leafs(df_sp_description_errors_15, df_sp_composition_errors_15, df_sp_values_errors_15, df_sp_proportionalities_errors_15)
    assert is_correct is False
    assert len(errors) == 4
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: Indicador folha '4' não possui dados associados."
    assert errors[1] == "valores.xlsx: Indicador folha '9' não possui dados associados."
    assert errors[2] == "proporcionalidades.xlsx: Indicador folha '8' não possui dados associados."
    assert errors[3] == "proporcionalidades.xlsx: Indicador folha '9' não possui dados associados."

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
    
def test_check_grafos_desconectados_with_disconnected_graphs():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(4, 5)
    disconnected_graphs = check_grafos_desconectados(G)
    assert len(disconnected_graphs) == 1
    assert len(disconnected_graphs[0]) == 2

def test_check_grafos_desconectados_with_connected_graph():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    disconnected_graphs = check_grafos_desconectados(G)
    assert len(disconnected_graphs) == 0

def test_check_grafos_desconectados_with_multiple_disconnected_graphs():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(4, 5)
    G.add_edge(6, 7)
    disconnected_graphs = check_grafos_desconectados(G)
    assert len(disconnected_graphs) == 2
    assert len(disconnected_graphs[0]) == 2
    assert len(disconnected_graphs[1]) == 2

def test_check_ciclos_with_cycle():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 1)
    has_cycle, cycle = check_ciclos(G)
    assert has_cycle is True
    assert len(cycle) == 3

def test_check_ciclos_without_cycle():
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    has_cycle, cycle = check_ciclos(G)
    assert has_cycle is False
    assert cycle is None

def test_check_ciclos_with_self_loop():
    G = nx.DiGraph()
    G.add_edge(1, 1)
    has_cycle, cycle = check_ciclos(G)
    assert has_cycle is True
    assert len(cycle) == 1
