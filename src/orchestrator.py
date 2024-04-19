import src.myparser.hierarchy.graph as graph
import src.myparser.hierarchy.tree as tree
import src.myparser.sp_values as sp_values
import src.myparser.sp_description as sp_description
import src.myparser.sp_scenario as sp_scenario
import src.myparser.sp_temporal_reference as sp_temporal_reference
import src.myparser.spellchecker as spellchecker
import src.myparser.structures_files as structures_files
import src.myparser.info as info

# VERIFICATORS
def verify_sp_description_cr_lf(df_sp, file_name,  columns_start_end=[], columns_anywhere=[]):
    return sp_description.verify_sp_description_cr_lf(df_sp, file_name, columns_start_end, columns_anywhere)

def verify_sp_description_empty_strings(df_sp_description, list_columns=[]):
    return sp_description.verify_sp_description_empty_strings(df_sp_description, list_columns)

def verify_sp_temporal_reference_unique_values(df_sp_scenario, columns_uniques):
    return sp_temporal_reference.verify_sp_temporal_reference_unique_values(df_sp_scenario, columns_uniques)

def verify_sp_scenario_unique_values(df_sp_scenario, columns_uniques):
    return sp_scenario.verify_sp_scenario_unique_values(df_sp_scenario, columns_uniques)

def verify_sp_temporal_reference_punctuation(df_sp_temporal_reference, columns_dont_punctuation, columns_must_end_with_dot):
    return sp_temporal_reference.verify_sp_temporal_reference_punctuation(df_sp_temporal_reference, columns_dont_punctuation, columns_must_end_with_dot)

def verify_files_data_clean(df, file_name, columns_to_clean, value):
    return structures_files.verify_files_data_clean(df, file_name, columns_to_clean, value)

def verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description, df_sp_values, df_sp_scenario, df_sp_temporal_reference):
    return sp_values.verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description, df_sp_values, df_sp_scenario, df_sp_temporal_reference)

def verify_spelling_text(df, file_name, sheets_info, lang_dict_spell):
    return spellchecker.run(df, file_name, sheets_info, lang_dict_spell)
    
def verify_structure_files_dataframe(df, file_name, expected_columns):
    return structures_files.verify_structure_files_dataframe(df, file_name, expected_columns)

def verify_structure_exepected_files_main_path(path_folder):
    return structures_files.verify_structure_exepected_files_main_path(path_folder)

def verify_sp_description_titles_length(df_sp_description):
    return sp_description.verify_sp_description_titles_length(df_sp_description)

def verify_sp_description_titles_uniques(df_sp_description):
    return sp_description.verify_sp_description_titles_uniques(df_sp_description)

def verify_sp_description_parser_html_column_names(df_sp_description, cloumn):
    return sp_description.verify_sp_description_parser_html_column_names(df_sp_description, cloumn)

def verify_sp_description_text_capitalize(df_sp_description):
    return sp_description.verify_sp_description_text_capitalize(df_sp_description)

def verify_graph_sp_description_composition(df_sp_description, df_sp_composition):
    return graph.verify_graph_sp_description_composition(df_sp_description, df_sp_composition)

def verify_ids_sp_description_values(df_sp_description, df_sp_values):
    return sp_values.verify_ids_sp_description_values(df_sp_description, df_sp_values)

def verify_sp_description_levels(df_sp_description):
    return sp_description.verify_sp_description_levels(df_sp_description)

def verify_sp_scenario_punctuation(df_sp_scenario, columns_dont_punctuation, columns_must_end_with_dot):
    return sp_scenario.verify_sp_scenario_punctuation(df_sp_scenario, columns_dont_punctuation, columns_must_end_with_dot)

def verify_sp_description_punctuation(df_sp_description, columns_dont_punctuation, columns_must_end_with_dot):
    return sp_description.verify_sp_description_punctuation(df_sp_description, columns_dont_punctuation, columns_must_end_with_dot)

def verify_sp_description_codes_uniques(df_sp_description):
    return sp_description.verify_sp_description_codes_uniques(df_sp_description)

def verify_tree_sp_description_composition_hierarchy(df_sp_composition, df_sp_description):
    return tree.verify_tree_sp_description_composition_hierarchy(df_sp_composition, df_sp_description)

# UTILITIES
def print_versions():
    return info.print_versions()
