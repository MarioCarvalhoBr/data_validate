from src.myparser.sp_proportionalities import verify_sum_prop_influence_factor_values

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_PROPORTIONALITIES_COLUMNS

# DATA FRAMES - GROUND TRUTH
from tests.unit.test_constants import df_sp_proportionalities_data_ground_truth_01

# DATA FRAMES - ERROS 01
from tests.unit.test_constants import df_sp_proportionalities_errors_01

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



