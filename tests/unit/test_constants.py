
# Imports libs
import os
from src.util.utilities import read_excel_file
from src.myparser.structures_files import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS 

# Diretórios de entrada para os testes
path_input_data_ground_truth = "input_data/data_ground_truth"
path_input_data_errors_01 = "input_data/data_errors_01"
path_input_data_errors_02 = "input_data/data_errors_02"
path_input_data_errors_03 = "input_data/data_errors_03"
path_input_data_errors_04 = "input_data/data_errors_04"

# 1. DATA FRAMES - GROUND TRUTH: path_input_data_ground_truth
df_sp_scenario_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_gt = read_excel_file(os.path.join(path_input_data_ground_truth, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 2. DATA FRAMES - ERROS 01: path_input_data_errors_01
df_sp_scenario_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_01 = read_excel_file(os.path.join(path_input_data_errors_01, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 3. DATA FRAMES - ERROS 02: path_input_data_errors_02
df_sp_scenario_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_02 = read_excel_file(os.path.join(path_input_data_errors_02, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 4. DATA FRAMES - ERROS 03: path_input_data_errors_03
df_sp_scenario_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_03 = read_excel_file(os.path.join(path_input_data_errors_03, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

# 5. DATA FRAMES - ERROS 04: path_input_data_errors_04
df_sp_scenario_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_SCENARIO_COLUMNS.NAME_SP))
df_sp_temporal_reference_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
df_sp_description_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_DESCRIPTION_COLUMNS.NAME_SP))
df_sp_composition_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_COMPOSITION_COLUMNS.NAME_SP))
df_sp_values_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_VALUES_COLUMNS.NAME_SP))
df_sp_proportionalities_errors_04 = read_excel_file(os.path.join(path_input_data_errors_04, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
