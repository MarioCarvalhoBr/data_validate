from src.myparser.sp_description import verify_sp_description_parser_html_column_names
from src.myparser.sp_description import verify_sp_description_titles_uniques
from src.myparser.sp_description import verify_sp_description_text_capitalize
from src.myparser.sp_description import verify_sp_description_titles_length
from src.myparser.sp_description import verify_sp_description_levels
from src.myparser.sp_description import verify_sp_description_punctuation
from src.myparser.sp_description import verify_sp_description_codes_uniques
from src.myparser.sp_description import verify_sp_description_cr_lf

from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS 

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_description_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_description_errors_01

# DATA FRAMES - ERROS 02
from tests.unit.test_constants import df_sp_scenario_errors_02, df_sp_temporal_reference_errors_02, df_sp_description_errors_02

# DATA FRAMES - ERROS 03
    

import pandas as pd

def test_verify_sp_description_parser_html_column_names_missing_column_default():
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(df, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)

    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1
    assert warnings[0] == f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos HTML nas descrições simples foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.DESC_SIMPLES}' está ausente."

def test_true_errors_verify_sp_description_cr_lf_gt(): # Teste true
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_description_gt, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META], columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_warnings_verify_sp_description_cr_lf_errors_02(): # Teste true
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_description_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META], columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_description_cr_lf_errors_02(): # Teste false
    __, errors, warnings = verify_sp_description_cr_lf(df_sp_description_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META], columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 10
    assert len(warnings) == 10

def test_false_verify_sp_scenario_cr_lf_errors_02(): # Teste false
    # PARA SP_SCENARIO_COLUMNS
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_scenario_errors_02, SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0
def test_count_errors_verify_sp_scenario_cr_lf_errors_02(): # Teste false
    __, errors, warnings = verify_sp_description_cr_lf(df_sp_scenario_errors_02, SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 2
    assert len(warnings) == 2

def test_false_verify_sp_temporal_reference_cr_lf_errors_02(): # Teste false
    # PARA SP_TEMPORAL_REFERENCE_COLUMNS
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_temporal_reference_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_temporal_reference_cr_lf_errors_02(): # Teste false
    # PARA SP_TEMPORAL_REFERENCE_COLUMNS
    __, errors, warnings = verify_sp_description_cr_lf(df_sp_temporal_reference_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])
    # Numero de erros esperado == 0
    assert len(errors) == 0
    # Numero de warnings esperado == 1
    assert len(warnings) == 1

def test_true_verify_sp_description_titles_length_in_data_ground_truth():
    is_correct, errors, warnings = verify_sp_description_titles_length(df_sp_description_gt)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_ture_verify_sp_description_titles_length_in_data_errors():
    is_correct, errors, warnings = verify_sp_description_titles_length(df_sp_description_errors_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1

def test_count_errors_verify_sp_description_titles_length():
    is_correct, errors, warnings = verify_sp_description_titles_length(df_sp_description_errors_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1

def test_true_verify_sp_description_parser_html_column_names():
    result_test, __, __ = verify_sp_description_parser_html_column_names(df_sp_description_gt, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)
    assert result_test is True

def test_count_errors_verify_sp_description_parser_html_column_names():
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(df_sp_description_errors_01, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 3

    
# Testes: Títulos únicos: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques_data_gt():
    result_test, __, __ = verify_sp_description_titles_uniques(df_sp_description_gt)
    assert result_test is True

def test_true_verify_sp_description_titles_uniques_data_errors():
    result_test, __, __ = verify_sp_description_titles_uniques(df_sp_description_errors_01)
    assert result_test is True

def test_count_errors_verify_sp_description_titles_uniques():
    is_correct, errors, warnings = verify_sp_description_titles_uniques(df_sp_description_errors_01)
    assert len(errors) == 0
    assert len(warnings) == 2

# Testes: Padrão para nomes dos indicadores: verify_sp_description_text_capitalize
def test_true_verify_sp_description_text_capitalize():
    result_test, __, __ = verify_sp_description_text_capitalize(df_sp_description_gt)
    assert result_test is True

def test_false_verify_sp_description_text_capitalize():

    __, __, warnings = verify_sp_description_text_capitalize(df_sp_description_errors_01)
    assert len(warnings) > 0

def test_count_errors_verify_sp_description_text_capitalize():
    is_correct, errors, warnings = verify_sp_description_text_capitalize(df_sp_description_errors_01)
    assert len(warnings) == 9
    assert len(errors) == 0

# Testes: Níveis de indicadores: verify_sp_description_levels
def test_true_verify_sp_description_levels():
    result_test, __, __ = verify_sp_description_levels(df_sp_description_gt)
    assert result_test is True

def test_false_verify_sp_description_levels():
    result_test, __, __ = verify_sp_description_levels(df_sp_description_errors_01)
    assert result_test is False

def test_count_errors_verify_sp_description_levels():
    is_correct, errors, warnings = verify_sp_description_levels(df_sp_description_errors_01)
    assert len(errors) == 3
    assert len(warnings) == 0

# Testes: Pontuações obrigatórias e proibidas: verify_sp_description_punctuation
def test_true_verify_sp_description_punctuation():
    is_correct, errors, warnings = verify_sp_description_punctuation(df_sp_description_gt, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_punctuation():
    is_correct, errors, warnings = verify_sp_description_punctuation(df_sp_description_errors_01, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) > 0

def test_count_errors_verify_sp_description_punctuation():
    is_correct, errors, warnings = verify_sp_description_punctuation(df_sp_description_errors_01, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert len(errors) == 0
    assert len(warnings) == 4

# Testes: Unicidade dos códigos: verify_sp_description_codes_uniques
def test_true_verify_sp_description_codes_uniques():
    is_correct, errors, warnings = verify_sp_description_codes_uniques(df_sp_description_gt)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_codes_uniques():
    is_correct, errors, warnings = verify_sp_description_codes_uniques(df_sp_description_errors_01)
    assert is_correct is False
    assert len(errors) > 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_codes_uniques():
    is_correct, errors, warnings = verify_sp_description_codes_uniques(df_sp_description_errors_01)
    assert len(errors) == 1
    assert len(warnings) == 0
