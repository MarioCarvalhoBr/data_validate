import pandas as pd
import os
from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors
from src.myparser.hierarchy.tree import verify_tree_sp_description_composition_hierarchy, dfs, criar_arvore
from src.myparser.hierarchy.tree import verificar_ciclos, verificar_erros_niveis

# Testes: Hierarquia como árvore #3
def test_true_verify_tree_sp_composition_hierarchy(): # Teste true
    planilha_05_composicao = path_input_data_ground_truth + "/5_composicao/composicao.xlsx"
    planilha_04_descricao = os.path.join(path_input_data_ground_truth, "4_descricao", "descricao.xlsx")
    result_test,__,__ = verify_tree_sp_description_composition_hierarchy(planilha_05_composicao, planilha_04_descricao)
    assert result_test is True
    
def test_false_verify_tree_sp_composition_hierarchy(): # Teste false
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    planilha_04_descricao = os.path.join(path_input_data_errors, "4_descricao", "descricao.xlsx")
    result_test,__,__ = verify_tree_sp_description_composition_hierarchy(planilha_05_composicao, planilha_04_descricao)
    assert result_test is False

def test_count_errors_verify_tree_sp_composition_hierarchy(): # Teste false
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    planilha_04_descricao = os.path.join(path_input_data_errors, "4_descricao", "descricao.xlsx")
    is_correct, errors, warnings = verify_tree_sp_description_composition_hierarchy(planilha_05_composicao, planilha_04_descricao)
    # Numero de erros esperado == 3
    assert len(errors) == 3
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

def test_criar_arvore_with_no_duplicates():
    composicao = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4]
    })
    arvore = criar_arvore(composicao)
    assert arvore == {'1': ['2'], '2': ['3'], '3': ['4']}

def test_criar_arvore_with_duplicates():
    composicao = pd.DataFrame({
        'codigo_pai': [1, 1, 2, 2, 3, 3],
        'codigo_filho': [2, 2, 3, 3, 4, 4]
    })
    arvore = criar_arvore(composicao)
    assert arvore == {'1': ['2', '2'], '2': ['3', '3'], '3': ['4', '4']}

def test_criar_arvore_with_string_values():
    composicao = pd.DataFrame({
        'codigo_pai': ['1,000', '2,000', '3,000'],
        'codigo_filho': ['2,000', '3,000', '4,000']
    })
    arvore = criar_arvore(composicao)
    assert arvore == {'1000': ['2000'], '2000': ['3000'], '3000': ['4000']}

def test_dfs_with_no_cycle():
    arvore = {'1': ['2'], '2': ['3'], '3': ['4']}
    visitado = set()
    caminho_atual = []
    ciclo_encontrado, ciclo = dfs(arvore, '1', visitado, caminho_atual)
    assert ciclo_encontrado is False
    assert ciclo == []

def test_dfs_with_cycle():
    arvore = {'1': ['2'], '2': ['3'], '3': ['1']}
    visitado = set()
    caminho_atual = []
    ciclo_encontrado, ciclo = dfs(arvore, '1', visitado, caminho_atual)
    assert ciclo_encontrado is True
    assert ciclo == ['1', '2', '3', '1']

def test_dfs_with_multiple_branches_and_no_cycle():
    arvore = {'1': ['2', '3'], '2': ['4'], '3': ['5']}
    visitado = set()
    caminho_atual = []
    ciclo_encontrado, ciclo = dfs(arvore, '1', visitado, caminho_atual)
    assert ciclo_encontrado is False
    assert ciclo == []

def test_dfs_with_multiple_branches_and_cycle():
    arvore = {'1': ['2', '3'], '2': ['4'], '3': ['1']}
    visitado = set()
    caminho_atual = []
    ciclo_encontrado, ciclo = dfs(arvore, '1', visitado, caminho_atual)
    assert ciclo_encontrado is True
    assert ciclo == ['1', '3', '1']

def test_verificar_ciclos_with_no_cycle():
    arvore = {'1': ['2'], '2': ['3'], '3': ['4']}
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    assert ciclo_encontrado is False
    assert ciclo == []

def test_verificar_ciclos_with_cycle():
    arvore = {'1': ['2'], '2': ['3'], '3': ['1']}
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    assert ciclo_encontrado is True
    assert ciclo == ['1', '2', '3', '1']

def test_verificar_ciclos_with_multiple_branches_and_no_cycle():
    arvore = {'1': ['2', '3'], '2': ['4'], '3': ['5']}
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    assert ciclo_encontrado is False
    assert ciclo == []

def test_verificar_ciclos_with_multiple_branches_and_cycle():
    arvore = {'1': ['2', '3'], '2': ['4'], '3': ['1']}
    ciclo_encontrado, ciclo = verificar_ciclos(arvore)
    assert ciclo_encontrado is True
    assert ciclo == ['1', '3', '1']

def test_verificar_erros_niveis_with_no_errors():
    composicao = pd.DataFrame({
        'codigo_pai': ['1000', '2000', '3000'],
        'codigo_filho': ['2000', '3000', '4000']
    })
    descricao = pd.DataFrame({
        'codigo': ['1000', '2000', '3000', '4000'],
        'nivel': [1, 2, 3, 4]
    })
    erros = verificar_erros_niveis(composicao, descricao)
    assert erros == []

def test_verificar_erros_niveis_with_errors():
    composicao = pd.DataFrame({
        'codigo_pai': ['1000', '2000', '3000'],
        'codigo_filho': ['2000', '3000', '4000']
    })
    descricao = pd.DataFrame({
        'codigo': ['1000', '2000', '3000', '4000'],
        'nivel': [1, 2, 2, 4]
    })
    erros = verificar_erros_niveis(composicao, descricao)
    assert erros == [('2000', '3000')]

def test_verificar_erros_niveis_with_missing_levels():
    composicao = pd.DataFrame({
        'codigo_pai': ['1000', '2000', '3000'],
        'codigo_filho': ['2000', '3000', '4000']
    })
    descricao = pd.DataFrame({
        'codigo': ['1000', '2000', '4000'],
        'nivel': [1, 2, 4]
    })
    erros = verificar_erros_niveis(composicao, descricao)
    assert erros == [(None, '3000'), ('3000', None)]

def test_verificar_erros_niveis_with_major_levels():
    composicao = pd.DataFrame({
        'codigo_pai': ['1000', '2000', '3000'],
        'codigo_filho': ['2000', '3000', '4000']
    })
    descricao = pd.DataFrame({
        'codigo': ['1000', '2000', '3000', '4000'],
        'nivel': [1, 2, 77, 88]
    })
    erros = verificar_erros_niveis(composicao, descricao)
    assert len(erros) == 0
