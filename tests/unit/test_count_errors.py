from src.myparser import verify_structure_folder_files
from src.myparser import verify_sp_description_parser
from src.myparser import verify_sp_description_titles_uniques
from src.myparser import verify_sp_description_text_capitalize
from src.myparser import verify_graph_sp_description_composition

# Diretórios de entrada para os testes
path_input_data_ground_truth = "input_data/data_ground_truth"
path_input_data_errors = "input_data/data_errors"

# Testes: Issue #5: Códigos html nas descrições simples
def test_count_errors_verify_sp_description_parser(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_parser(planilha_04_descricao)
    # Numero de erros esperado == 3
    assert len(errors) == 3
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# Testes: Issue #39: Estrutura da pasta de arquivos
def test_count_errors_verify_structure_folder_files(): # Teste false
    is_correct, errors, warnings = verify_structure_folder_files(path_input_data_errors)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
    
# Testes: Issue #36: Títulos únicos
def test_count_errors_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_titles_uniques(planilha_04_descricao)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# Testes: Issue #1: Padrão para nomes dos indicadores
def test_count_errors_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    # Numero de warnings esperado == 4
    assert len(warnings) == 4
    # Numero de erros esperado == 0
    assert len(errors) == 0

# Testes: 6 - Hierarquia como grafo conexo
def test_count_errors_verify_graph_sp_description_composition(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    is_correct, errors, warnings = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    # Numero de erros esperado == 4
    assert len(errors) == 4
    # Numero de warnings esperado == 0
    assert len(warnings) == 0