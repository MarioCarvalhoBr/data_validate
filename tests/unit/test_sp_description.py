from src.myparser.sp_description import verify_sp_description_parser_html_column_names
from src.myparser.sp_description import verify_sp_description_titles_uniques
from src.myparser.sp_description import verify_sp_description_text_capitalize
from src.myparser.sp_description import verify_sp_description_titles_length
from src.myparser.sp_description import verify_sp_description_levels
from src.myparser.sp_description import verify_sp_description_punctuation
from src.myparser.sp_description import verify_sp_description_codes_uniques
from src.myparser.sp_description import verify_sp_description_empty_strings
from src.myparser.sp_description import verify_sp_description_cr_lf

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01, path_input_data_errors_02
import os

# Testes: Caracteres CR e LF: verify_sp_description_cr_lf
def test_true_verify_sp_description_cr_lf(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_cr_lf(planilha_04_descricao, columns_start_end=['codigo', 'nivel', 'nome_simples', 'nome_completo', 'unidade', 'desc_simples', 'desc_completa', 'cenario', 'relacao', 'fontes', 'meta'], columns_anywhere=['nome_simples', 'nome_completo'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_cr_lf(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_02,  "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_cr_lf(planilha_04_descricao, columns_start_end=['codigo', 'nivel', 'nome_simples', 'nome_completo', 'unidade', 'desc_simples', 'desc_completa', 'cenario', 'relacao', 'fontes', 'meta'], columns_anywhere=['nome_simples', 'nome_completo'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_description_cr_lf(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_02,  "descricao.xlsx")
    _, errors, warnings = verify_sp_description_cr_lf(planilha_04_descricao, columns_start_end=['codigo', 'nivel', 'nome_simples', 'nome_completo', 'unidade', 'desc_simples', 'desc_completa', 'cenario', 'relacao', 'fontes', 'meta'], columns_anywhere=['nome_simples', 'nome_completo'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 10
    assert len(warnings) == 10

def test_false_verify_sp_scenario_cr_lf(): # Teste false
    planilha_05_cenario = os.path.join(path_input_data_errors_02, "cenarios.xlsx")
    is_correct, errors, warnings = verify_sp_description_cr_lf(planilha_05_cenario,columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_scenario_cr_lf(): # Teste false
    planilha_05_cenario = os.path.join(path_input_data_errors_02, "cenarios.xlsx")
    _, errors, warnings = verify_sp_description_cr_lf(planilha_05_cenario,columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

def test_false_verify_sp_temporal_reference_cr_lf(): # Teste false
    planilha_06_referencia_temporal = os.path.join(path_input_data_errors_02, "referencia_temporal.xlsx")
    is_correct, errors, warnings = verify_sp_description_cr_lf(planilha_06_referencia_temporal,columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_temporal_reference_cr_lf(): # Teste false
    planilha_06_referencia_temporal = os.path.join(path_input_data_errors_02, "referencia_temporal.xlsx")
    _, errors, warnings = verify_sp_description_cr_lf(planilha_06_referencia_temporal, columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 1
    assert len(warnings) == 1


# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_length_in_data_ground_truth(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    is_correct,errors, warnings  = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0
def test_ture_verify_sp_description_titles_length_in_data_errors(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct,errors, warnings  = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1
def test_count_errors_verify_sp_description_titles_length(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_titles_length(planilha_04_descricao)
    assert is_correct is True
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 1
    assert len(warnings) == 1


# Testes: Códigos html nas descrições simples: verify_sp_description_parser_html_column_names
def test_true_verify_sp_description_parser_html_column_names(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    result_test,__,__ = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    # tests/unit/test_parser.py:16:27: E712 Comparison to `True` should be `cond is True` or `if cond:`
    assert result_test is True
def test_count_errors_verify_sp_description_parser_html_column_names(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(planilha_04_descricao)
    assert is_correct is True

    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 3
    assert len(warnings) == 3

    
# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques_data_gt(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_true_verify_sp_description_titles_uniques_data_errors(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    result_test,__,__ = verify_sp_description_titles_uniques(planilha_04_descricao)
    assert result_test is True
def test_count_errors_verify_sp_description_titles_uniques(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_titles_uniques(planilha_04_descricao)
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

# Testes: Padrão para nomes dos indicadores: verify_sp_description_text_capitalize
def test_true_verify_sp_description_text_capitalize(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    result_test,__,__ = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    __,__,warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    assert len(warnings) > 0
def test_count_errors_verify_sp_description_text_capitalize(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_text_capitalize(planilha_04_descricao)
    # Numero de warnings esperado == 9
    assert len(warnings) == 9
    # Numero de erros esperado == 0
    assert len(errors) == 0
    
# Testes: Níveis de indicadores: verify_sp_description_levels
def test_true_verify_sp_description_levels(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    result_test,__,__ = verify_sp_description_levels(planilha_04_descricao)
    assert result_test is True
def test_false_verify_sp_description_levels(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    result_test,__,__ = verify_sp_description_levels(planilha_04_descricao)
    assert result_test is False
def test_count_errors_verify_sp_description_levels(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_levels(planilha_04_descricao)
    # Numero de erros esperado == 3
    assert len(errors) == 3
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# Testes: Pontuações obrigatórias e proibidas: verify_sp_description_punctuation
def test_true_verify_sp_description_punctuation(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_punctuation(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao,  ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_description_punctuation(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_punctuation(planilha_04_descricao,  ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 4
    assert len(warnings) == 4

# Testes: Unicidade dos códigos: verify_sp_description_codes_uniques
def test_true_verify_sp_description_codes_uniques(): # Teste true
    planilha_04_descricao = os.path.join(path_input_data_ground_truth,  "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_codes_uniques(planilha_04_descricao)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0
def test_false_verify_sp_description_codes_uniques(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_codes_uniques(planilha_04_descricao)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0
def test_count_errors_verify_sp_description_codes_uniques(): # Teste false
    planilha_04_descricao = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_codes_uniques(planilha_04_descricao)
    # Numero de erros esperado == 1
    assert len(errors) == 1
    # Numero de warnings esperado == 0
    assert len(warnings) == 0

# Test verify_sp_description_parser_html_column_names
def test_verify_sp_description_parser_html_column_names_with_valid_file():
    path_sp_description = os.path.join(path_input_data_ground_truth, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(path_sp_description)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_verify_sp_description_parser_html_column_names_with_invalid_file():
    path_sp_description = os.path.join(path_input_data_errors_01, "4_descricao", "descricao.csv")
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(path_sp_description)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_verify_sp_description_parser_html_column_names_with_missing_columns():
    path_sp_description = os.path.join(path_input_data_errors_01, "missing_columns.xlsx")
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(path_sp_description)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_verify_sp_description_parser_html_column_names_with_extra_columns():
    path_sp_description = os.path.join(path_input_data_errors_01, "extra_columns.xlsx")
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(path_sp_description)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

# verify_sp_description_empty_strings
def test_true_verify_sp_description_empty_strings():
    path_sp_description = os.path.join(path_input_data_ground_truth, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_empty_strings(path_sp_description)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_empty_strings():
    path_sp_description = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_empty_strings(path_sp_description)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_empty_strings():
    path_sp_description = os.path.join(path_input_data_errors_01, "descricao.xlsx")
    is_correct, errors, warnings = verify_sp_description_empty_strings(path_sp_description)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

def test_verify_sp_description_empty_strings_with_invalid_file():
    path_sp_description = os.path.join(path_input_data_errors_01, "4_descricao", "descricao.csv")
    is_correct, errors, warnings = verify_sp_description_empty_strings(path_sp_description)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0
