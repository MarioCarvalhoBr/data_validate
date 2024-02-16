import pandas as pd
from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors
from src.myparser.hierarchy.tree import verify_tree_sp_composition_hierarchy, verificar_niveis_pai_filho, dfs, limpar_dados_numericos

# Testes: Hierarquia como árvore #3
def test_true_verify_tree_sp_composition_hierarchy(): # Teste true
    planilha_05_composicao = path_input_data_ground_truth + "/5_composicao/composicao.xlsx"
    result_test,__,__ = verify_tree_sp_composition_hierarchy(planilha_05_composicao)
    assert result_test is True
def test_false_verify_tree_sp_composition_hierarchy(): # Teste false
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    result_test,__,__ = verify_tree_sp_composition_hierarchy(planilha_05_composicao)
    assert result_test is False
def test_count_errors_verify_tree_sp_composition_hierarchy(): # Teste false
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    is_correct, errors, warnings = verify_tree_sp_composition_hierarchy(planilha_05_composicao)
    # Numero de erros esperado == 5
    assert len(errors) == 5
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

def test_verificar_niveis_pai_filho_with_correct_levels():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'nivel_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'nivel_filho': [2, 3, 4]
    })
    erros_niveis = verificar_niveis_pai_filho(df)
    assert len(erros_niveis) == 0

def test_verificar_niveis_pai_filho_with_incorrect_levels():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'nivel_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'nivel_filho': [3, 4, 5]
    })
    erros_niveis = verificar_niveis_pai_filho(df)
    assert len(erros_niveis) == 3
    assert erros_niveis[0] == "Erro de nível: Pai 1 (Nível 1) e Filho 2 (Nível 3)"
    assert erros_niveis[1] == "Erro de nível: Pai 2 (Nível 2) e Filho 3 (Nível 4)"
    assert erros_niveis[2] == "Erro de nível: Pai 3 (Nível 3) e Filho 4 (Nível 5)"

def test_dfs_with_no_loop():
    hierarquia = {1: [2, 3], 2: [4], 3: [], 4: []}
    visitado = set()
    caminho_atual = []
    loop_found, loop_message = dfs(hierarquia, 1, visitado, caminho_atual)
    assert loop_found is False
    assert loop_message is None

def test_dfs_with_loop():
    hierarquia = {1: [2], 2: [3], 3: [1]}
    visitado = set()
    caminho_atual = []
    loop_found, loop_message = dfs(hierarquia, 1, visitado, caminho_atual)
    assert loop_found is True
    assert loop_message == "Loop detectado: [1 -> 2 -> 3 -> 1]"

def test_dfs_with_self_loop():
    hierarquia = {1: [1]}
    visitado = set()
    caminho_atual = []
    loop_found, loop_message = dfs(hierarquia, 1, visitado, caminho_atual)
    assert loop_found is True
    assert loop_message == "Loop detectado: [1 -> 1]"

def test_limpar_dados_numericos_with_no_errors():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'nivel_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'nivel_filho': [2, 3, 4]
    })
    df, erros = limpar_dados_numericos(df, 'test_file')
    assert len(erros) == 0
    assert len(df) == 3

def test_limpar_dados_numericos_with_non_numeric_values():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 'three'],
        'nivel_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'nivel_filho': [2, 3, 4]
    })
    df, erros = limpar_dados_numericos(df, 'test_file')
    assert len(erros) == 2
    assert erros[0] == "test_file: Os valores das colunas 'codigo_pai', 'codigo_filho', 'nivel_pai' e 'nivel_filho' devem ser numéricos."
    assert erros[1] == "test_file, linha 2: A coluna 'codigo_pai' deve conter apenas valores numéricos."
    assert len(df) == 2

def test_limpar_dados_numericos_with_multiple_errors():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 'three'],
        'nivel_pai': [1, 'two', 3],
        'codigo_filho': [2, 3, 'four'],
        'nivel_filho': [2, 3, 'four']
    })
    df, erros = limpar_dados_numericos(df, 'test_file')
    assert len(erros) == 3
    assert erros[0] == "test_file: Os valores das colunas 'codigo_pai', 'codigo_filho', 'nivel_pai' e 'nivel_filho' devem ser numéricos."
    assert erros[1] == "test_file, linha 2: A coluna 'codigo_pai' deve conter apenas valores numéricos."
    assert erros[2] == "test_file, linha 1: A coluna 'nivel_pai' deve conter apenas valores numéricos."

    assert len(df) == 1
