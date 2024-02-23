import src.myparser.hierarchy.graph as graph
import src.myparser.hierarchy.tree as tree
import src.myparser.sp_values as sp_values
import src.myparser.sp_description as sp_description
import src.myparser.spellchecker as spellchecker
import src.myparser.structures_files as structures_files
import src.myparser.info as info

def verify_spelling_text(path_folder, type_dict_spell):
    return spellchecker.run(path_folder, type_dict_spell)
    
def verify_structure_folder_files(path_folder):
    return structures_files.verify_structure_folder_files(path_folder)

def verify_sp_description_titles_length(path_sp_description):
    return sp_description.verify_sp_description_titles_length(path_sp_description)

def verify_sp_description_titles_uniques(path_sp_description):
    return sp_description.verify_sp_description_titles_uniques(path_sp_description)

def verify_sp_description_parser_html_column_names(path_sp_description):
    return sp_description.verify_sp_description_parser_html_column_names(path_sp_description)

def verify_sp_description_text_capitalize(path_sp_description):
    return sp_description.verify_sp_description_text_capitalize(path_sp_description)

def verify_graph_sp_description_composition(path_sp_description, path_ps_composition):
    return graph.verify_graph_sp_description_composition(path_sp_description, path_ps_composition)

def verify_ids_sp_description_values(path_sp_description, path_sp_values):
    return sp_values.verify_ids_sp_description_values(path_sp_description, path_sp_values)

def verify_sp_description_levels(path_sp_description):
    return sp_description.verify_sp_description_levels(path_sp_description)

def verify_sp_description_punctuation(path_sp_description):
    return sp_description.verify_sp_description_punctuation(path_sp_description)

def verify_sp_description_codes_uniques(path_sp_description):
    return sp_description.verify_sp_description_codes_uniques(path_sp_description)

def verify_tree_sp_description_composition_hierarchy(path_ps_composition, path_ps_description):
    return tree.verify_tree_sp_description_composition_hierarchy(path_ps_composition, path_ps_description)

def verify_version():
    return info.print_versions()

def get_spellchecker():
    return spellchecker
