import pandas as pd

from src.myparser.sp_description import verify_sp_description_parser_html_column_names
from src.myparser.sp_description import verify_sp_description_titles_uniques
from src.myparser.sp_description import verify_sp_description_text_capitalize
from src.myparser.sp_description import verify_sp_description_titles_length
from src.myparser.sp_description import verify_sp_description_levels
from src.myparser.sp_description import verify_sp_description_punctuation
from src.myparser.sp_description import verify_sp_description_codes_uniques
from src.myparser.sp_description import verify_sp_description_cr_lf
from src.myparser.sp_description import verify_sp_description_codes_sequential

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_description_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_description_errors_01

# DATA FRAMES - ERROS 02
from tests.unit.test_constants import df_sp_scenario_errors_02, df_sp_temporal_reference_errors_02, df_sp_description_errors_02

# DATA FRAMES - ERROS 04
from tests.unit.test_constants import df_sp_description_errors_04

# Testes: verify_sp_description_codes_sequential
def test_true_verify_sp_description_codes_sequential_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_codes_sequential(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0
    
def test_count_errors_verify_sp_description_codes_sequential_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_codes_sequential(df_sp_description_errors_01)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx: Verificação de códigos sequenciais foi abortada porque a coluna 'codigo' contém valores inválidos."

def test_count_errors_verify_sp_description_codes_sequential_data_errors_02():
    is_correct, errors, warnings = verify_sp_description_codes_sequential(df_sp_description_errors_02)
    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx: A coluna 'codigo' deve começar em 1."
    assert errors[1] == "descricao.xlsx: A coluna 'codigo' deve conter valores sequenciais (1, 2, 3, ...)."

# Testes: verify_sp_description_cr_lf
def test_true_errors_verify_sp_description_cr_lf_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_description_data_ground_truth_01, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META], columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_cr_lf_errors_02():
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_description_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=[SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META], columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 10

def test_false_verify_sp_scenario_cr_lf_errors_02():
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_scenario_errors_02, SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 2

def test_false_verify_sp_temporal_reference_cr_lf_errors_02():
    is_correct, errors, warnings = verify_sp_description_cr_lf(df_sp_temporal_reference_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO])

    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1

# Testes: verify_sp_description_titles_length
def test_true_verify_sp_description_titles_length_in_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_titles_length(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_verify_sp_description_titles_length_in_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_titles_length(df_sp_description_errors_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1

    assert warnings[0] == "descricao.xlsx, linha 10: Nome simples fora do padrão. Esperado: Até 40 caracteres. Encontrado: 43 caracteres."

# Testes: verify_sp_description_parser_html_column_names
def test_true_verify_sp_description_parser_html_column_names_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(df_sp_description_data_ground_truth_01, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_parser_html_column_names_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(df_sp_description_errors_01, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 3

def test_verify_sp_description_parser_html_column_names_missing_column_default():
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

    is_correct, errors, warnings = verify_sp_description_parser_html_column_names(df, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES)

    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 1
    assert warnings[0] == f"{SP_DESCRIPTION_COLUMNS.NAME_SP}: Verificação de códigos HTML nas descrições simples foi abortada porque a coluna '{SP_DESCRIPTION_COLUMNS.DESC_SIMPLES}' está ausente."
    
# Testes: verify_sp_description_titles_uniques
def test_true_verify_sp_description_titles_uniques_data_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_titles_uniques(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_sp_description_titles_uniques_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_titles_uniques(df_sp_description_errors_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 2

# Testes: verify_sp_description_text_capitalize
def test_true_verify_sp_description_text_capitalize_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_text_capitalize(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_text_capitalize_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_text_capitalize(df_sp_description_errors_01)
    assert is_correct is True
    assert len(warnings) == 9
    assert len(errors) == 0

def test_count_errors_verify_sp_description_text_capitalize_data_errors_04():
    is_correct, errors, warnings = verify_sp_description_text_capitalize(df_sp_description_errors_04)
    assert is_correct is True
    assert len(warnings) == 2
    assert len(errors) == 0

    assert warnings[0] == 'descricao.xlsx, linha 3: Nome simples fora do padrão. Esperado: "IDEB séries finais". Encontrado: "IDEB séries Finais".'
    assert warnings[1] == 'descricao.xlsx, linha 4: Nome simples fora do padrão. Esperado: "Vulnerabilidade do IDEB". Encontrado: "Vulnerabilidade Do IDEB".'

# Testes: verify_sp_description_levels
def test_true_verify_sp_description_levels_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_levels(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_levels_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_levels(df_sp_description_errors_01)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx, linha 4: Nível do indicador não é um número inteiro maior que 0."
    assert errors[1] == "descricao.xlsx, linha 5: Nível do indicador não é um número inteiro maior que 0."
    assert errors[2] == "descricao.xlsx, linha 12: Nível do indicador não é um número inteiro maior que 0."

def test_count_errors_verify_sp_description_levels_data_errors_04():
    is_correct, errors, warnings = verify_sp_description_levels(df_sp_description_errors_04)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx, linha 2: Nível do indicador não é um número inteiro maior que 0."
    assert errors[1] == "descricao.xlsx, linha 3: Nível do indicador não é um número inteiro maior que 0."
    assert errors[2] == "descricao.xlsx, linha 4: Nível do indicador não é um número inteiro maior que 0."

# Testes: verify_sp_description_punctuation
def test_true_verify_sp_description_punctuation_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_punctuation(df_sp_description_data_ground_truth_01, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_description_punctuation_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_punctuation(df_sp_description_errors_01, ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 4

# Testes: verify_sp_description_codes_uniques
def test_true_verify_sp_description_codes_uniques_data_ground_truth_01():
    is_correct, errors, warnings = verify_sp_description_codes_uniques(df_sp_description_data_ground_truth_01)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_false_verify_sp_description_codes_uniques_data_errors_01():
    is_correct, errors, warnings = verify_sp_description_codes_uniques(df_sp_description_errors_01)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0
