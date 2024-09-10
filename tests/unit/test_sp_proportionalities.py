from src.myparser.sp_proportionalities import verify_sum_prop_influence_factor_values, verify_ids_sp_description_proportionalities, verify_repeated_columns_parent_sp_description_proportionalities, verify_parent_child_relationships, verify_ids_values_proportionalities

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_scenario_data_ground_truth_01, df_sp_composition_data_ground_truth_01, df_sp_values_data_ground_truth_01

# DATA FRAMES - GROUND TRUTH 02
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_02_no_scenario, df_sp_description_data_ground_truth_02_no_scenario, df_sp_scenario_data_ground_truth_02_no_scenario, df_sp_composition_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario

# DATA FRAMES - GROUND TRUTH 03
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_03_csv, df_sp_description_data_ground_truth_03_csv, df_sp_scenario_data_ground_truth_03_csv, df_sp_composition_data_ground_truth_03_csv, df_sp_values_data_ground_truth_03_csv


# DATA FRAMES - ERROS 09
from tests.unit.test_constants import df_sp_proportionalities_errors_09, df_sp_description_errors_09, df_sp_scenario_errors_09

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_proportionalities_errors_01

# DATA FRAMES - ERROS 11
from tests.unit.test_constants import df_sp_proportionalities_errors_11, df_sp_scenario_errors_11, df_sp_composition_errors_11

# DATA FRAMES - ERROS 06
from tests.unit.test_constants import df_sp_proportionalities_errors_06, df_sp_scenario_errors_06

# DATA FRAMES - ERROS 12
from tests.unit.test_constants import df_sp_proportionalities_errors_12, df_sp_values_errors_12


# Teste: verify_sp_scenario_punctuation
def test_true_verify_sp_scenario_punctuation_data_ground_truth_01():
    is_correct, errors, warnings = verify_sum_prop_influence_factor_values(df_sp_proportionalities_data_ground_truth_01, True, SP_PROPORTIONALITIES_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_sp_scenario_punctuation_data_errors_01():
    is_correct, errors, warnings = verify_sum_prop_influence_factor_values(df_sp_proportionalities_errors_01, True, SP_PROPORTIONALITIES_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 6
    assert len(warnings) == 3

    assert warnings[0] == "proporcionalidades.xlsx, linha 4: A soma dos valores para o indicador pai 5008-2010 é 0.999, e não 1."
    assert warnings[1] == "proporcionalidades.xlsx, linha 5: A soma dos valores para o indicador pai 5008-2010 é 1.001, e não 1."
    assert warnings[2] == "proporcionalidades.xlsx, linha 4: Existem valores com mais de 3 casas decimais na planilha, serão consideradas apenas as 3 primeiras casas decimais."

    assert errors[0] == "proporcionalidades.xlsx, linha 3: A soma dos valores para o indicador pai 5008-2010 é 1.548, e não 1."
    assert errors[1] == "proporcionalidades.xlsx, linha 3: A soma dos valores para o indicador pai 5010-2010 é 0.462, e não 1."
    assert errors[2] == "proporcionalidades.xlsx, linha 5: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '5010-2010' e indicador filho '5030-2010'."
    assert errors[3] == "proporcionalidades.xlsx, linha 5: A soma dos valores para o indicador pai 5010-2010 é 0.902, e não 1."
    assert errors[4] == "proporcionalidades.xlsx, linha 6: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '5010-2010' e indicador filho '5030-2010'."
    assert errors[5] == "proporcionalidades.xlsx, linha 6: A soma dos valores para o indicador pai 5010-2010 é 0.902, e não 1."


# Testes: def verify_ids_sp_description_proportionalities
def test_true_verify_ids_sp_description_proportionalities_data_ground_truth_01():
    is_correct, errors, warnings = verify_ids_sp_description_proportionalities(df_sp_description= df_sp_description_data_ground_truth_01, df_sp_proportionalities= df_sp_proportionalities_data_ground_truth_01, df_sp_scenario= df_sp_scenario_data_ground_truth_01, name_sp_description= SP_DESCRIPTION_COLUMNS.NAME_SP, name_sp_proportionalities= SP_PROPORTIONALITIES_COLUMNS.NAME_SP, name_sp_scenario= SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_sp_description_proportionalities_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_ids_sp_description_proportionalities(df_sp_description= df_sp_description_data_ground_truth_02_no_scenario, df_sp_proportionalities= df_sp_proportionalities_data_ground_truth_02_no_scenario, df_sp_scenario= df_sp_scenario_data_ground_truth_02_no_scenario, name_sp_description= SP_DESCRIPTION_COLUMNS.NAME_SP, name_sp_proportionalities= SP_PROPORTIONALITIES_COLUMNS.NAME_SP, name_sp_scenario= SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_sp_description_proportionalities_data_ground_truth_03():
    is_correct, errors, warnings = verify_ids_sp_description_proportionalities(df_sp_description=df_sp_description_data_ground_truth_03_csv, df_sp_proportionalities=df_sp_proportionalities_data_ground_truth_03_csv, df_sp_scenario=df_sp_scenario_data_ground_truth_03_csv, name_sp_description=SP_DESCRIPTION_COLUMNS.NAME_SP, name_sp_proportionalities=SP_PROPORTIONALITIES_COLUMNS.NAME_SP, name_sp_scenario=SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_ids_sp_description_proportionalities_data_errors_09():
    is_correct, errors, warnings =verify_ids_sp_description_proportionalities(df_sp_description=df_sp_description_errors_09, df_sp_proportionalities=df_sp_proportionalities_errors_09, df_sp_scenario=df_sp_scenario_errors_09, name_sp_description=SP_DESCRIPTION_COLUMNS.NAME_SP, name_sp_proportionalities=SP_PROPORTIONALITIES_COLUMNS.NAME_SP, name_sp_scenario=SP_SCENARIO_COLUMNS.NAME_SP)

    assert is_correct is False
    assert len(errors) == 2
    assert len(warnings) == 0

    assert errors[0] == "descricao.xlsx: Códigos dos indicadores ausentes em proporcionalidades.xlsx: [2, 4, 5, 7, 8, 9]."
    assert errors[1] == "proporcionalidades.xlsx: Códigos dos indicadores ausentes em descricao.xlsx: [5024, 5025, 5026, 5027, 5028, 5029, 5030, 5031, 5008, 5009, 5010, 5021, 5022, 5023]."


# verify_repeated_columns_parent_sp_description_proportionalities (df_sp_proportionalities, df_sp_scenario, name_sp_proportionalities, name_sp_scenario):
def test_true_verify_repeated_columns_parent_sp_description_proportionalities_data_ground_truth_01():
    
    is_correct, errors, warnings = verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities_data_ground_truth_01, df_sp_scenario_data_ground_truth_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_repeated_columns_parent_sp_description_proportionalities_data_errors_11():
    is_correct, errors, warnings = verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities_errors_11, df_sp_scenario_errors_11, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

    assert errors[0] == "proporcionalidades.xlsx: O indicador pai '2-2015' está repetido na planilha."

def test_count_errors_verify_repeated_columns_parent_sp_description_proportionalities_data_errors_06():
    is_correct, errors, warnings = verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities_errors_06, df_sp_scenario_errors_06, SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx",".csv"), SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

    assert errors[0] == "proporcionalidades.csv: O indicador pai '2-2015' está repetido na planilha."

# Testes para def verify_parent_child_relationships(df_sp_proportionalities, df_sp_composition, name_sp_proportionalities, name_sp_composition):
def test_true_verify_parent_child_relationships_data_ground_truth_01():
    is_correct, errors, warnings = verify_parent_child_relationships(df_sp_proportionalities_data_ground_truth_01, df_sp_composition_data_ground_truth_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_COMPOSITION_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_parent_child_relationships_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_parent_child_relationships(df_sp_proportionalities_data_ground_truth_02_no_scenario, df_sp_composition_data_ground_truth_02_no_scenario, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_COMPOSITION_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_parent_child_relationships_data_ground_truth_03():
    is_correct, errors, warnings = verify_parent_child_relationships(df_sp_proportionalities_data_ground_truth_03_csv, df_sp_composition_data_ground_truth_03_csv, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_COMPOSITION_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0
def test_count_errors_verify_parent_child_relationships_data_errors_11():
    is_correct, errors, warnings = verify_parent_child_relationships(df_sp_proportionalities_errors_11, df_sp_composition_errors_11, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_COMPOSITION_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 3
    assert len(warnings) == 0

    assert errors[0] == "proporcionalidades.xlsx: Deve existir pelo menos uma relação do indicador filho '4' com o indicador pai '2-2015' conforme especificado em composicao.xlsx."
    assert errors[1] == "proporcionalidades.xlsx: O indicador pai '99' (em '99-2050-P') não está presente na coluna 'codigo_pai' da planilha composicao.xlsx."
    assert errors[2] == "proporcionalidades.xlsx: O indicador '88' (em '88-2050-O') não é filho do indicador '3' (em '3-2015') conforme especificado em composicao.xlsx."

# Testes para def verify_ids_values_proportionalities(df_sp_proportionalities, df_sp_values, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP))
def test_true_verify_ids_values_proportionalities_data_ground_truth_01(): 
    is_correct, errors, warnings = verify_ids_values_proportionalities(df_sp_proportionalities_data_ground_truth_01, df_sp_values_data_ground_truth_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_values_proportionalities_data_ground_truth_02_no_scenario():
    is_correct, errors, warnings = verify_ids_values_proportionalities(df_sp_proportionalities_data_ground_truth_02_no_scenario, df_sp_values_data_ground_truth_02_no_scenario, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_true_verify_ids_values_proportionalities_data_ground_truth_03():
    is_correct, errors, warnings = verify_ids_values_proportionalities(df_sp_proportionalities_data_ground_truth_03_csv, df_sp_values_data_ground_truth_03_csv, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)
    assert is_correct is True
    assert len(errors) == 0
    assert len(warnings) == 0

def test_count_errors_verify_ids_values_proportionalities_data_errors_12():
    is_correct, errors, warnings = verify_ids_values_proportionalities(df_sp_proportionalities_errors_12, df_sp_values_errors_12, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 18
    assert len(warnings) == 0

    assert errors[0] == "valores.xlsx: O indicador '4-2015' não está presente na planilha proporcionalidades.xlsx."
    assert errors[1] == "valores.xlsx: O indicador '5-2015' não está presente na planilha proporcionalidades.xlsx."
    assert errors[2] == "valores.xlsx: O indicador '5-2030-O' não está presente na planilha proporcionalidades.xlsx."
    assert errors[3] == "valores.xlsx: O indicador '5-2050-O' não está presente na planilha proporcionalidades.xlsx."
    assert errors[4] == "valores.xlsx: O indicador '7-2015' não está presente na planilha proporcionalidades.xlsx."
    assert errors[5] == "valores.xlsx: O indicador '8-2015' não está presente na planilha proporcionalidades.xlsx."
    assert errors[6] == "valores.xlsx: O indicador '9-2015' não está presente na planilha proporcionalidades.xlsx."
    assert errors[7] == "proporcionalidades.xlsx: O indicador '3-2030-O' não está presente na planilha valores.xlsx."
    assert errors[8] == "proporcionalidades.xlsx: O indicador '3-2050-O' não está presente na planilha valores.xlsx."
    assert errors[9] == "proporcionalidades.xlsx: O indicador '4-2030-P' não está presente na planilha valores.xlsx."
    assert errors[10] == "proporcionalidades.xlsx: O indicador '4-2050-O' não está presente na planilha valores.xlsx."
    assert errors[11] == "proporcionalidades.xlsx: O indicador '6-2030-O' não está presente na planilha valores.xlsx."
    assert errors[12] == "proporcionalidades.xlsx: O indicador '6-2050-O' não está presente na planilha valores.xlsx."
    assert errors[13] == "proporcionalidades.xlsx: O indicador '7-2030-P' não está presente na planilha valores.xlsx."
    assert errors[14] == "proporcionalidades.xlsx: O indicador '7-2050-P' não está presente na planilha valores.xlsx."
    assert errors[15] == "proporcionalidades.xlsx: O indicador '8-2030-O' não está presente na planilha valores.xlsx."
    assert errors[16] == "proporcionalidades.xlsx: O indicador '9-2030-O' não está presente na planilha valores.xlsx."
    assert errors[17] == "proporcionalidades.xlsx: O indicador '9-2050-O' não está presente na planilha valores.xlsx."
