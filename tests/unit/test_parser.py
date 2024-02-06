from src.orchestrator import verify_structure_folder_files
from src.orchestrator import verify_sp_description_parser
from src.orchestrator import verify_spelling_text
from src.orchestrator import verify_sp_description_titles_uniques
from src.orchestrator import verify_sp_description_text_capitalize
from src.orchestrator import verify_graph_sp_description_composition
from src.orchestrator import verify_ids_sp_description_values
from src.myparser.sp_description import verify_sp_description_titles_length

from src.myparser.spellchecker import TypeDict
import src.myparser.libraries_versions as lv

# Diretórios de entrada para os testes
path_input_data_ground_truth = "input_data/data_ground_truth"
path_input_data_errors = "input_data/data_errors"


def test_true_verify_sp_description_titles_length_in_data_ground_truth(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    is_correct,errors, warnings  = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_ture_verify_sp_description_titles_length_in_data_errors(): # Teste true
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct,errors, warnings  = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1

def test_verify_sp_description_titles_length_with_non_existing_file():
    try:
        verify_sp_description_titles_length('non_existing_file.xlsx')
    except FileNotFoundError as e:
        assert str(e) == "[Errno 2] No such file or directory: 'non_existing_file.xlsx'"

# Testes: Códigos html nas descrições simples
def test_true_verify_sp_description_parser(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser(planilha_04_descricao)
    # tests/unit/test_parser.py:16:27: E712 Comparison to `True` should be `cond is True` or `if cond:`
    assert result_test is True
def test_false_verify_sp_description_parser(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser(planilha_04_descricao)
    assert result_test is False

# Testes: Estrutura da pasta de arquivos
def test_true_verify_structure_folder_files(): # Teste true
    result_test,__,__ = verify_structure_folder_files(path_input_data_ground_truth)
    assert result_test is True
def test_false_verify_structure_folder_files(): # Teste false
    result_test,errors,warnings = verify_structure_folder_files(path_input_data_errors)
    assert result_test is False
    
# Testes: Verificar ortografia
def test_true_verify_spelling_text_full(): # Teste true
    type_dict_spell = TypeDict.FULL
    is_correct,errors, warnings = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert is_correct is True
    assert len(warnings) == 0
    assert len(errors) == 0

# Testes: Verificar ortografia
def test_false_verify_spelling_text_full_for_errors(): # Teste true
    type_dict_spell = TypeDict.FULL
    is_correct,errors, warnings = verify_spelling_text(path_input_data_errors, type_dict_spell)
    assert is_correct is False
    assert len(warnings) == 3
    assert len(errors) == 2

def test_true_verify_spelling_text_tiny(): # Teste false
    type_dict_spell = TypeDict.TINY
    is_correct,errors, warnings = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert is_correct is True
    assert len(warnings) == 16
    assert len(errors) == 0
    
# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is False
    

# Testes: Padrão para nomes dos indicadores: verify_sp_description_text_capitalize
def test_true_verify_sp_description_text_capitalize(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    __,__,warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert len(warnings) > 0

# Testes: Hierarquia como grafo conexo
def test_true_verify_graph_sp_description_composition(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    planilha_05_composicao = path_input_data_ground_truth + "/5_composicao/composicao.xlsx"
    result_test,__,__ = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    assert result_test is True
def test_false_verify_graph_sp_description_composition(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_05_composicao = path_input_data_errors + "/5_composicao/composicao.xlsx"
    result_test,__,__ = verify_graph_sp_description_composition(planilha_04_descricao, planilha_05_composicao)
    assert result_test is False

# Testes: Relações entre indicadores da planilha de valores
def test_true_verify_ids_sp_description_values(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_ground_truth + "/8_valores/valores.xlsx"
    result_test,__,__ = verify_ids_sp_description_values(planilha_04_descricao, planilha_08_valores)
    assert result_test is True
def test_false_verify_ids_sp_description_values(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    planilha_08_valores = path_input_data_errors + "/8_valores/valores.xlsx"
    result_test,__,__ = verify_ids_sp_description_values(planilha_04_descricao, planilha_08_valores)
    assert result_test is False

def test_verstion():
    ret = lv.print_versions()
    assert ret is True