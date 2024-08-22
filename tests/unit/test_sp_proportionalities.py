from src.myparser.sp_proportionalities import verify_sum_prop_influence_factor_values, verify_ids_sp_description_proportionalities, verify_repeated_columns_parent_sp_description_proportionalities

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS, SP_DESCRIPTION_COLUMNS, SP_SCENARIO_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_01, df_sp_description_data_ground_truth_01, df_sp_scenario_data_ground_truth_01

# DATA FRAMES - GROUND TRUTH 02
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_02_no_scenario, df_sp_description_data_ground_truth_02_no_scenario, df_sp_scenario_data_ground_truth_02_no_scenario

# DATA FRAMES - GROUND TRUTH 03
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_03_csv, df_sp_description_data_ground_truth_03_csv, df_sp_scenario_data_ground_truth_03_csv


# DATA FRAMES - ERROS 09
from tests.unit.test_constants import df_sp_proportionalities_errors_09, df_sp_description_errors_09, df_sp_scenario_errors_09

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_proportionalities_errors_01

# DATA FRAMES - ERROS 11
from tests.unit.test_constants import df_sp_proportionalities_errors_11, df_sp_scenario_errors_11

# DATA FRAMES - ERROS 06
from tests.unit.test_constants import df_sp_proportionalities_errors_06, df_sp_scenario_errors_06


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

    assert errors[0] == "proporcionalidades.xlsx: O indicador pai '2-2015' deveria possuir os seguintes filhos: ['5-2030-O', '5-2050-O', '5-2030-P']. Entretanto, foram encontrados os filhos ['5-2030-O', '5-2050-O', '5-2030-P', '5-2030-O', '2-2030-O', '5-2050-O']."

def test_count_errors_verify_repeated_columns_parent_sp_description_proportionalities_data_errors_06():
    is_correct, errors, warnings = verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities_errors_06, df_sp_scenario_errors_06, SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx",".csv"), SP_SCENARIO_COLUMNS.NAME_SP)
    assert is_correct is False
    assert len(errors) == 1
    assert len(warnings) == 0

    assert errors[0] == "proporcionalidades.csv: O indicador pai '2-2015' deveria possuir os seguintes filhos: ['5-2030-O', '5-2050-O', '5-2030-P']. Entretanto, foram encontrados os filhos ['5-2030-O', '5-2050-O', '5-2030-P', '5-2030-O', '2-2030-O', '5-2050-O']."
