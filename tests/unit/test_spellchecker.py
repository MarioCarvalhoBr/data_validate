from src.myparser.spellchecker import run as verify_spelling_text

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01, path_input_data_errors_02, path_input_data_errors_03

    
def test_true_verify_spelling_text_pt_BR_gt(): # Teste true
    lang_dict_spell = "pt_BR"
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    path_sp_description = path_input_data_ground_truth + "/descricao.xlsx"
    path_sp_scenario = path_input_data_ground_truth + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_ground_truth + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], lang_dict_spell)

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
    
    path_sp_description = path_input_data_errors_01 + "/descricao.xlsx"
    path_sp_scenario = path_input_data_errors_01 + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_errors_01 + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], lang_dict_spell)

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
    
    path_sp_description = path_input_data_errors_02 + "/descricao.xlsx"
    path_sp_scenario = path_input_data_errors_02 + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_errors_02 + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], lang_dict_spell)

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
    
    path_sp_description = path_input_data_errors_03 + "/descricao.xlsx"
    path_sp_scenario = path_input_data_errors_03 + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_errors_03 + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], lang_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], lang_dict_spell)

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
