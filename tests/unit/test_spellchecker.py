from src.orchestrator import verify_spelling_text
from src.myparser.spellchecker import TypeDict

from tests.unit.test_constants import path_input_data_ground_truth, path_input_data_errors_01

    
# Testes: Verificar ortografia
def test_true_verify_spelling_text_full(): # Teste true
    type_dict_spell = TypeDict.FULL
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    path_sp_description = path_input_data_ground_truth + "/descricao.xlsx"
    path_sp_scenario = path_input_data_ground_truth + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_ground_truth + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 0
    assert len(all_errors) == 0

# Testes: Verificar ortografia: Tiny
def test_true_verify_spelling_text_tiny(): # Teste false
    type_dict_spell = TypeDict.TINY
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    path_sp_description = path_input_data_ground_truth + "/descricao.xlsx"
    path_sp_scenario = path_input_data_ground_truth + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_ground_truth + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 16
    assert len(all_errors) == 0
    
def test_count_errors_verify_spelling_text_tiny(): # Teste false
    type_dict_spell = TypeDict.TINY
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    path_sp_description = path_input_data_errors_01 + "/descricao.xlsx"
    path_sp_scenario = path_input_data_errors_01 + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_errors_01 + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 22
    assert len(all_errors) == 0

# Testes: Verificar ortografia: Full
def test_count_errors_verify_spelling_text_full(): # Teste true
    type_dict_spell = TypeDict.FULL
    
    is_all_correct = True
    all_errors = []
    all_warnings = []
    
    path_sp_description = path_input_data_errors_01 + "/descricao.xlsx"
    path_sp_scenario = path_input_data_errors_01 + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_data_errors_01 + "/referencia_temporal.xlsx"

    is_correct_desc, errors_spell_desc, warnings_spell_desc = verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_desc
    all_errors.extend(errors_spell_desc)
    all_warnings.extend(warnings_spell_desc)
    
    is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = verify_spelling_text(path_sp_scenario, ["nome", "descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_scenario
    all_errors.extend(errors_spell_scenario)
    all_warnings.extend(warnings_spell_scenario)

    is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = verify_spelling_text(path_sp_temporal_reference, ["descricao"], type_dict_spell)

    is_all_correct = is_all_correct and is_correct_temporal_reference
    all_errors.extend(errors_spell_temporal_reference)
    all_warnings.extend(warnings_spell_temporal_reference)
    
    
    assert is_all_correct is True
    assert len(all_warnings) == 10
    assert len(all_errors) == 0
