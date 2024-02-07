from src.myparser.sp_description import verify_sp_description_parser_html_column_names
from src.myparser.sp_description import verify_sp_description_titles_uniques
from src.myparser.sp_description import verify_sp_description_text_capitalize
from src.myparser.sp_description import verify_sp_description_titles_length
from src.myparser.sp_description import verify_sp_description_levels
from src.myparser.sp_description import verify_sp_description_punctuation

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors


# Testes: Títulos únicos: verify_sp_description_titles_uniques
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
def test_count_errors_verify_sp_description_titles_length(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 1
    assert len(warnings) == 1


# Testes: Códigos html nas descrições simples: verify_sp_description_parser_html_column_names
def test_true_verify_sp_description_parser_html_column_names(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    # tests/unit/test_parser.py:16:27: E712 Comparison to `True` should be `cond is True` or `if cond:`
    assert result_test is True
def test_count_errors_verify_sp_description_parser_html_column_names(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    assert is_correct is True

    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 3
    assert len(warnings) == 3

    
# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques_data_gt(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_true_verify_sp_description_titles_uniques_data_errors(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_count_errors_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_titles_uniques(planilha_04_descricao)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

# Testes: Padrão para nomes dos indicadores: verify_sp_description_text_capitalize
def test_true_verify_sp_description_text_capitalize(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    __,__,warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert len(warnings) > 0
def test_count_errors_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    # Numero de warnings esperado == 9
    assert len(warnings) == 9
    # Numero de erros esperado == 0
    assert len(errors) == 0
    
# Testes: Níveis de indicadores: verify_sp_description_levels
def test_true_verify_sp_description_levels(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_levels(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_levels(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_levels(planilha_04_descricao)
    assert result_test is False
def test_count_errors_verify_sp_description_levels(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_levels(planilha_04_descricao)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# Testes: Pontuações obrigatórias e proibidas: verify_sp_description_punctuation
def test_true_verify_sp_description_punctuation(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_punctuation(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_description_punctuation(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 15
    assert len(warnings) == 15
