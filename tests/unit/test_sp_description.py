from src.myparser.sp_description import verify_sp_description_parser_html_column_names
from src.myparser.sp_description import verify_sp_description_titles_uniques
from src.myparser.sp_description import verify_sp_description_text_capitalize
from src.myparser.sp_description import verify_sp_description_titles_length

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
def test_verify_sp_description_titles_length_with_non_existing_file():
    try:
        verify_sp_description_titles_length('non_existing_file.xlsx')
    except FileNotFoundError as e:
        assert str(e) == "[Errno 2] No such file or directory: 'non_existing_file.xlsx'"
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
def test_false_verify_sp_description_parser_html_column_names(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    assert result_test is False
def test_count_errors_verify_sp_description_parser_html_column_names(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    # Numero de erros esperado == 3
    assert len(errors) == 3
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

    
# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is False
def test_count_errors_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_description_titles_uniques(planilha_04_descricao)
    # Numero de erros esperado == 2
    assert len(errors) == 2
    # Numero de warnings esperado == 0
    assert len(warnings) == 0
    

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
    # Numero de warnings esperado == 10
    assert len(warnings) == 10
    # Numero de erros esperado == 0
    assert len(errors) == 0
    