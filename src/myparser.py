# Libs
import pandas as pd
import os
import re

import src.util.graph as graph
import src.util.sp_values as sp_values
import src.util.sp_description as sp_description
import src.util.spellchecker as spellchecker
import src.util.structures_io as structures_io

def verify_spelling_text(path_folder, type_dict_spell):
    return spellchecker.run(path_folder, type_dict_spell)
    
def verify_structure_folder_files(path_folder):
    return structures_io.verify_structure_folder_files(path_folder)

def verify_sp_description_titles_uniques(path_sp_description):
    return sp_description.verify_sp_description_titles_uniques(path_sp_description)

def verify_sp_description_parser(path_sp_description):
    return sp_description.verify_sp_description_parser(path_sp_description)

def verify_sp_description_text_capitalize(path_sp_description):
    return sp_description.verify_sp_description_text_capitalize(path_sp_description)

def verify_graph_sp_description_composition(path_sp_description, path_ps_composition):
    return graph.run(path_sp_description, path_ps_composition)

def verify_ids_sp_description_values(path_sp_description, path_sp_values):
    is_correct, errors, warnings = sp_values.verify_ids_sp_description_values(path_sp_description, path_sp_values)
    return is_correct, errors, warnings