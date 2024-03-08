from src.myparser.sp_scenario import verify_sp_scenario_parser_html_column_names
from src.myparser.sp_scenario import verify_sp_scenario_titles_uniques
from src.myparser.sp_scenario import verify_sp_scenario_text_capitalize
from src.myparser.sp_scenario import verify_sp_scenario_titles_length
from src.myparser.sp_scenario import verify_sp_scenario_levels
from src.myparser.sp_scenario import verify_sp_scenario_punctuation
from src.myparser.sp_scenario import verify_sp_scenario_codes_uniques

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors
import os


# Testes: Pontuações obrigatórias e proibidas: verify_sp_scenario_punctuation
def test_true_verify_sp_scenario_punctuation(): # Teste true
    planilha_04_descricao = path_input_data_ground_truth + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_04_descricao, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_scenario_punctuation(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_04_descricao,  ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_scenario_punctuation(): # Teste false
    planilha_04_descricao = path_input_data_errors + "/4_descricao/descricao.xlsx"
    is_correct, errors, warnings = verify_sp_scenario_punctuation(planilha_04_descricao,  ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 4
    assert len(warnings) == 4
