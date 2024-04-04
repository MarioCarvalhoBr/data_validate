import re
import enum
import os
from src.util.utilities import read_excel_file
import pandas as pd

class TypeDict(enum.Enum):
    TINY = 1
    FULL = 2

def load_dictionary(path):
    with open(path, 'r', encoding='utf-8') as file:
        return {word.strip().lower() for word in file}

def preprocess_text(text):
    text = re.split("Fontes:|Fonte:", text)[0]
    text = re.sub(r'<.*?>|\(.*?\)|[^\w\s]|\d+', ' ', text)

    return text

def find_spelling_errors(text, dictionary):
    words = text.split()
    return [word for word in words if word.lower() not in dictionary]

def verify_text(column_name, text, dictionary, type_dict_spell, index, sheet_name):
    errors = verify_sintax_ortography(text, type_dict_spell, dictionary)
    if errors:
        return f"{sheet_name}, linha {index + 1}: Palavras com possíveis erros ortográficos na coluna {column_name}: {errors}."
    return ""

def verify_sintax_ortography(text, type_dict_spell, dictionary):
    preprocessed_text = preprocess_text(text)
    return find_spelling_errors(preprocessed_text, dictionary)

def process_sheet(df, columns, dictionary, type_dict_spell, sheet_name):
    warnings = []
    for index, row in df.iterrows():
        for column in columns:
            text = row[column]
            # Verifique se o texto está vazio ou nan 
            if pd.isna(text) or text == "":
                text = ""
            warning = verify_text(column, text, dictionary, type_dict_spell, index, sheet_name)
            if warning:
                warnings.append(warning)
    return warnings

def run(path, columns_sheets, type_dict_spell):
    # print(f'Running spellchecker on {path}. Sheets info: {columns_sheets}. Type dict spell: {type_dict_spell}')
    errors, warnings = [], []
    dict_path = 'dictionaries/pt_BR/tiny.txt' if type_dict_spell == TypeDict.TINY else 'dictionaries/pt_BR/full.txt'
    dictionary = load_dictionary(dict_path)

    file_name = os.path.basename(path)

    try:
        df = read_excel_file(path)
        sheet_warnings = process_sheet(df, columns_sheets, dictionary, type_dict_spell, file_name)
        warnings.extend(sheet_warnings)
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {file_name}: {e}")

    return not errors, errors, warnings
