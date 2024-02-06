import src.myparser.graph as graph
import src.myparser.sp_values as sp_values
import src.myparser.sp_description as sp_description
import src.myparser.spellchecker as spellchecker
import src.myparser.structures_files as structures_files

def verify_spelling_text(path_folder, type_dict_spell):
    return spellchecker.run(path_folder, type_dict_spell)
    
def verify_structure_folder_files(path_folder):
    return structures_files.verify_structure_folder_files(path_folder)

def verify_sp_description_titles_length(path_sp_description):
    return sp_description.verify_sp_description_titles_length(path_sp_description)

def verify_sp_description_titles_uniques(path_sp_description):
    return sp_description.verify_sp_description_titles_uniques(path_sp_description)

def verify_sp_description_parser(path_sp_description):
    return sp_description.verify_sp_description_parser(path_sp_description)

def verify_sp_description_text_capitalize(path_sp_description):
    return sp_description.verify_sp_description_text_capitalize(path_sp_description)

def verify_graph_sp_description_composition(path_sp_description, path_ps_composition):
    return graph.run(path_sp_description, path_ps_composition)

def verify_ids_sp_description_values(path_sp_description, path_sp_values):
    return sp_values.verify_ids_sp_description_values(path_sp_description, path_sp_values)