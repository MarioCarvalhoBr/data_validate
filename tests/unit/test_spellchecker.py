from src.orchestrator import verify_spelling_text
from src.myparser.spellchecker import TypeDict

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors

    
# Testes: Verificar ortografia
def test_true_verify_spelling_text_full(): # Teste true
    type_dict_spell = TypeDict.FULL
    is_correct,errors, warnings = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert is_correct is True
    assert len(warnings) == 0
    assert len(errors) == 0

# Testes: Verificar ortografia: Tiny
def test_true_verify_spelling_text_tiny(): # Teste false
    type_dict_spell = TypeDict.TINY
    is_correct,errors, warnings = verify_spelling_text(path_input_data_ground_truth, type_dict_spell)
    assert is_correct is True
    assert len(warnings) == 16
    assert len(errors) == 0
def test_count_errors_verify_spelling_text_tiny(): # Teste false
    path_input_folder = path_input_data_errors
    type_dict_spell = TypeDict.TINY
    is_correct, errors, warnings = verify_spelling_text(path_input_folder, type_dict_spell)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 14
    assert len(warnings) == 14

# Testes: Verificar ortografia: Full
def test_true_verify_spelling_text_full_for_errors(): # Teste true
    type_dict_spell = TypeDict.FULL
    is_correct,errors, warnings = verify_spelling_text(path_input_data_errors, type_dict_spell)
    assert is_correct is True
    assert len(warnings) == 3
    assert len(errors) == 0

def test_count_errors_verify_spelling_text_full(): # Teste false
    path_input_folder = path_input_data_errors
    type_dict_spell = TypeDict.FULL
    is_correct, errors, warnings = verify_spelling_text(path_input_folder, type_dict_spell)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 3
    assert len(warnings) == 3