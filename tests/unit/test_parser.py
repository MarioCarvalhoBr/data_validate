from src.myparser import verify_sp_description_parser
from src.myparser import verify_structure_folder_files
from src.myparser import verify_spelling_text
from src.myparser import print_versions
from src.util.spellchecker import TypeDict

# Import pytest
import pytest
print("pytest version:", pytest.__version__)

# Pasta raiz
path_input_data_ground_truth = "input_data/data_ground_truth"
path_input_data_errors = "input_data/data_errors"

# Testes: Issue #5: Códigos html nas descrições simples
def test_true_verify_sp_description_parser(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser(planilha_04_descricao)
    # tests/unit/test_parser.py:16:27: E712 Comparison to `True` should be `cond is True` or `if cond:`
    assert result_test is True
def test_false_verify_sp_description_parser(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser(planilha_04_descricao)
    assert result_test is False

# Testes: Issue #39: Estrutura da pasta de arquivos
def test_true_verify_structure_folder_files(): # Teste true
    result_test,__,__ = verify_structure_folder_files(path_input_data_ground_truth)
    assert result_test is True
def test_false_verify_structure_folder_files(): # Teste false
    result_test,__,__ = verify_structure_folder_files(path_input_data_errors)
    assert result_test is False
    
# Testes: Issue #24: Verificar ortografia
def test_true_verify_spelling_text(): # Teste true
    type_dict_spell = TypeDict.FULL
    result_test,__,__ = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert result_test is True
def test_false_verify_spelling_text(): # Teste false
    type_dict_spell = TypeDict.TINY
    result_test,__,__ = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert result_test is False
    
def test_verstion():
    print_versions()
    assert True is True