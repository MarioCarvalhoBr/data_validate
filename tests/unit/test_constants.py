
# Imports libs
import os
from src.util.utilities import read_excel_file, read_file_proporcionalites
# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

# Estrutura esperada de colunas para cada arquivo
STRUCTURE_FILES_COLUMNS_DICT = {
    SP_SCENARIO_COLUMNS.NAME_SP: [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO, SP_SCENARIO_COLUMNS.SIMBOLO],
    SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO],
    
    SP_DESCRIPTION_COLUMNS.NAME_SP: [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META],
    
    SP_COMPOSITION_COLUMNS.NAME_SP: [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO],
    SP_VALUES_COLUMNS.NAME_SP: [SP_VALUES_COLUMNS.ID],
    SP_PROPORTIONALITIES_COLUMNS.NAME_SP: [SP_PROPORTIONALITIES_COLUMNS.ID]
}

STRUCTURE_FILES_TO_CLEAN_LIST = [
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1], # CORRIGIR para 0.x
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NIVEL], 1],
    [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CENARIO], -1],
    
    [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0],
    [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1],
    
    [SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO], 0]
]

# Diretórios de entrada para os testes
path_input_data_ground_truth_01 = "input_data/data_ground_truth_01"
path_input_data_ground_truth_02_no_scenario = "input_data/data_ground_truth_02_no_scenario"
path_input_data_ground_truth_03_csv = "input_data/data_ground_truth_03_csv"
path_input_data_ground_truth_04_csv_xlsx = "input_data/data_ground_truth_04_csv_xlsx"
path_input_data_ground_truth_05 = "input_data/data_ground_truth_05"
path_input_data_errors_00 = "input_data/data_errors_00"
path_input_data_errors_01 = "input_data/data_errors_01"
path_input_data_errors_02 = "input_data/data_errors_02"
path_input_data_errors_03 = "input_data/data_errors_03"
path_input_data_errors_04 = "input_data/data_errors_04"
path_input_data_errors_05 = "input_data/data_errors_05"
path_input_data_errors_06 = "input_data/data_errors_06"
path_input_data_errors_07 = "input_data/data_errors_07"
path_input_data_errors_08 = "input_data/data_errors_08"
path_input_data_errors_09 = "input_data/data_errors_09"
path_input_data_errors_10 = "input_data/data_errors_10"
path_input_data_errors_11 = "input_data/data_errors_11"


# 1. DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth_01
df_sp_scenario_data_ground_truth_01, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_01, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_data_ground_truth_01, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_01, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_data_ground_truth_01, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_01, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_data_ground_truth_01, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_01, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_data_ground_truth_01, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_01, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_data_ground_truth_01, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_ground_truth_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 1.2 DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth_02_no_scenario
df_sp_scenario_data_ground_truth_02_no_scenario, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_data_ground_truth_02_no_scenario, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_data_ground_truth_02_no_scenario, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_data_ground_truth_02_no_scenario, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_data_ground_truth_02_no_scenario, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_data_ground_truth_02_no_scenario, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_ground_truth_02_no_scenario, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 1.3 DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth_03_csv
df_sp_scenario_data_ground_truth_03_csv, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_03_csv, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_data_ground_truth_03_csv, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_03_csv, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_data_ground_truth_03_csv, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_03_csv, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_data_ground_truth_03_csv, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_03_csv, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_data_ground_truth_03_csv, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_03_csv, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_data_ground_truth_03_csv, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_ground_truth_03_csv, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 1.3 DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth_04_csv_xlsx
df_sp_scenario_data_ground_truth_04_csv_xlsx, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_data_ground_truth_04_csv_xlsx, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_data_ground_truth_04_csv_xlsx, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_data_ground_truth_04_csv_xlsx, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_data_ground_truth_04_csv_xlsx, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_data_ground_truth_04_csv_xlsx, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_ground_truth_04_csv_xlsx, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 1.3 DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth_05
df_sp_scenario_data_ground_truth_05, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_05, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_data_ground_truth_05, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_05, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_data_ground_truth_05, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_05, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_data_ground_truth_05, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_05, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_data_ground_truth_05, errors_read_file = read_excel_file(os.path.join(path_input_data_ground_truth_05, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_data_ground_truth_05, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_ground_truth_05, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 2. DATA FRAMES - ERROS 01: path_input_data_errors_01
df_sp_scenario_errors_01, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_01, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_01, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_01, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_01, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_01, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_01, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_01, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_01, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_01, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_01, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 3. DATA FRAMES - ERROS 02: path_input_data_errors_02
df_sp_scenario_errors_02, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_02, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_02, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_02, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_02, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_02, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_02, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_02, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_02, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_02, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 4. DATA FRAMES - ERROS 03: path_input_data_errors_03
df_sp_scenario_errors_03, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_03, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_03, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_03, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_03, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_03, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_03, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_03, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_03, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_03, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_03, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_03, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 5. DATA FRAMES - ERROS 04: path_input_data_errors_04
df_sp_scenario_errors_04, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_04, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_04, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_04, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_04, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_04, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_04, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_04, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_04, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_04, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_04, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_04, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 6. DATA FRAMES - ERROS 05: path_input_data_errors_05
df_sp_scenario_errors_05, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_05, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_05, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_05, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_05, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_05, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_05, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_05, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_05, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_05, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_05, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_05, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 7. DATA FRAMES - ERROS 06: path_input_data_errors_06
df_sp_scenario_errors_06, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_06, SP_SCENARIO_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_temporal_reference_errors_06, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_06, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_description_errors_06, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_06, SP_DESCRIPTION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_composition_errors_06, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_06, SP_COMPOSITION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_values_errors_06, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_06, SP_VALUES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_proportionalities_errors_06, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_06, SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))

# 8. DATA FRAMES - ERROS 07: path_input_data_errors_07
df_sp_scenario_errors_07, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_07, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_07, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_07, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_07, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_07, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_07, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_07, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_07, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_07, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_07, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_07, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 9. DATA FRAMES - ERROS 08: path_input_data_errors_08
df_sp_scenario_errors_08, errors_read_file_1 = read_excel_file(os.path.join(path_input_data_errors_08, SP_SCENARIO_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_proportionalities_errors_08, errors_read_file_2 = read_file_proporcionalites(os.path.join(path_input_data_errors_08, SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))


df_sp_temporal_reference_errors_08, errors_read_file_3 = read_excel_file(os.path.join(path_input_data_errors_08, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_description_errors_08, errors_read_file_4 = read_excel_file(os.path.join(path_input_data_errors_08, SP_DESCRIPTION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_composition_errors_08, errors_read_file_5 = read_excel_file(os.path.join(path_input_data_errors_08, SP_COMPOSITION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))
df_sp_values_errors_08, errors_read_file_6 = read_excel_file(os.path.join(path_input_data_errors_08, SP_VALUES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")))

all_errors_read_files_data_errors_08 = []
all_errors_read_files_data_errors_08.extend(errors_read_file_1)
all_errors_read_files_data_errors_08.extend(errors_read_file_2)
all_errors_read_files_data_errors_08.extend(errors_read_file_3)
all_errors_read_files_data_errors_08.extend(errors_read_file_4)
all_errors_read_files_data_errors_08.extend(errors_read_file_5)
all_errors_read_files_data_errors_08.extend(errors_read_file_6)

# 10. DATA FRAMES - ERROS 09: path_input_data_errors_09
df_sp_scenario_errors_09, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_09, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_09, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_09, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_09, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_09, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_09, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_09, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_09, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_09, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_09, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_09, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 11. DATA FRAMES - ERROS 10: path_input_data_errors_10
df_sp_scenario_errors_10, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_10, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_10, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_10, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_10, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_10, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_10, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_10, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_10, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_10, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_10, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_10, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 12. DATA FRAMES - ERROS 11: path_input_data_errors_11
df_sp_scenario_errors_11, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_11, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_11, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_11, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_11, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_11, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_11, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_11, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_11, errors_read_file = read_excel_file(os.path.join(path_input_data_errors_11, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_11, errors_read_file = read_file_proporcionalites(os.path.join(path_input_data_errors_11, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
