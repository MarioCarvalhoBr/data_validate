from src.myparser.spellchecker import run as verify_spelling_text


from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS 

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_scenario_gt, df_sp_temporal_reference_gt, df_sp_description_gt

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_scenario_errors_01, df_sp_temporal_reference_errors_01, df_sp_description_errors_01

# DATA FRAMES - ERROS 02
from tests.unit.test_constants import df_sp_scenario_errors_02, df_sp_temporal_reference_errors_02, df_sp_description_errors_02

# DATA FRAMES - ERROS 03
from tests.unit.test_constants import df_sp_scenario_errors_03, df_sp_temporal_reference_errors_03, df_sp_description_errors_03
    
def test_true_verify_spelling_text_pt_BR_gt(): # Teste true
    lang_dict_spell = "pt_BR"
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(df_sp_description_gt, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(df_sp_scenario_gt, SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(df_sp_temporal_reference_gt, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 0
    assert len(all_errors) == 0

def test_count_errors_verify_spelling_text_pt_BR_errors_1(): # Teste count errors
    lang_dict_spell = "pt_BR"
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(df_sp_description_errors_01, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(df_sp_scenario_errors_01, SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(df_sp_temporal_reference_errors_01, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 12
    assert len(all_errors) == 0

    assert all_warnings[0] == "descricao.xlsx, linha 1: Palavras com possíveis erros ortográficos na coluna desc_completa: ['meioz', 'çociedades']."
    assert all_warnings[1] == "descricao.xlsx, linha 2: Palavras com possíveis erros ortográficos na coluna desc_completa: ['crimáticas']."
    assert all_warnings[2] == "descricao.xlsx, linha 4: Palavras com possíveis erros ortográficos na coluna desc_completa: ['siztema']."
    assert all_warnings[3] == "descricao.xlsx, linha 5: Palavras com possíveis erros ortográficos na coluna desc_completa: ['MCTI', 'SPEI']."
    assert all_warnings[4] == "descricao.xlsx, linha 10: Palavras com possíveis erros ortográficos na coluna nome_completo: ['ruarais']."
    assert all_warnings[5] == "descricao.xlsx, linha 11: Palavras com possíveis erros ortográficos na coluna nome_completo: ['ruarais']."
    assert all_warnings[6] == "descricao.xlsx, linha 12: Palavras com possíveis erros ortográficos na coluna desc_completa: ['MCTI', 'SPEI']."
    assert all_warnings[7] == "cenarios.xlsx, linha 1: Palavras com possíveis erros ortográficos na coluna nome: ['Otiimmiztta']."
    assert all_warnings[8] == "cenarios.xlsx, linha 1: Palavras com possíveis erros ortográficos na coluna descricao: ['otiimmiztta']."
    assert all_warnings[9] == "cenarios.xlsx, linha 3: Palavras com possíveis erros ortográficos na coluna nome: ['Otiimmiztta']."
    assert all_warnings[10] == "cenarios.xlsx, linha 3: Palavras com possíveis erros ortográficos na coluna descricao: ['otiimmiztta']."
    assert all_warnings[11] == "referencia_temporal.xlsx, linha 2: Palavras com possíveis erros ortográficos na coluna descricao: ['Déccadda']."

def test_count_errors_verify_spelling_text_pt_BR_errors_2(): # Teste count errors
    lang_dict_spell = "pt_BR"
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(df_sp_description_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(df_sp_scenario_errors_02, SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(df_sp_temporal_reference_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    assert is_all_correct is True
    assert len(all_warnings) == 5
    assert len(all_errors) == 0

    assert all_warnings[0] == "descricao.xlsx, linha 2: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[1] == "descricao.xlsx, linha 4: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[2] == "descricao.xlsx, linha 5: Palavras com possíveis erros ortográficos na coluna desc_completa: ['MCTI', 'SPEI']."
    assert all_warnings[3] == "descricao.xlsx, linha 6: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[4] == "descricao.xlsx, linha 8: Palavras com possíveis erros ortográficos na coluna nome_simples: ['rcialização']."

def test_count_errors_verify_spelling_text_pt_BR_errors_3(): # Teste count errors
    lang_dict_spell = "pt_BR"
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(df_sp_description_errors_03, SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(df_sp_scenario_errors_03, SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(df_sp_temporal_reference_errors_03, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    assert is_all_correct is True
    assert len(all_warnings) == 5
    assert len(all_errors) == 0

    assert all_warnings[0] == "descricao.xlsx, linha 2: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[1] == "descricao.xlsx, linha 4: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[2] == "descricao.xlsx, linha 5: Palavras com possíveis erros ortográficos na coluna desc_completa: ['MCTI', 'SPEI']."
    assert all_warnings[3] == "descricao.xlsx, linha 6: Palavras com possíveis erros ortográficos na coluna nome_simples: ['LF']."
    assert all_warnings[4] == "descricao.xlsx, linha 8: Palavras com possíveis erros ortográficos na coluna nome_simples: ['rcialização']."
