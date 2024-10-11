import re
import pandas as pd
import hunspell
from src.myparser.text_processor import is_acronym

def load_dictionary(path):
    with open(path, 'r', encoding='utf-8') as file:
        return {word.strip().lower() for word in file}

def process_sheet(df, columns, meu_analizador, sheet_name):
    warnings = []
    for index, row in df.iterrows():
        for column in columns:
            text = row[column]
            # Verifique se o texto está vazio ou nan 
            if pd.isna(text) or text == "":
                text = ""
            warning = check_text(column, text, meu_analizador, index, sheet_name)
            if warning:
                warnings.append(warning)
    return warnings

def check_text(column_name, text, meu_analizador, index, sheet_name):
    
    errors = check_sintax_ortography(text, meu_analizador)
    if errors:
        return f"{sheet_name}, linha {index + 2}: Palavras com possíveis erros ortográficos na coluna {column_name}: {errors}."
    return ""

def check_sintax_ortography(text, meu_analizador):
    preprocessed_text = preprocess_text(text)
    return find_spelling_errors(preprocessed_text, meu_analizador)

def preprocess_text(text):
    text = re.split("Fontes:|Fonte:", text)[0]
    text = re.sub(r'<.*?>|\(.*?\)|[^\w\s]|\d+', ' ', text)

    return text

def find_spelling_errors(text, meu_analizador):
    words = text.split()
    errors = []
    for word in words:
        word = str(word).strip()
        # Verifica se a palavra é um acrônimo
        if is_acronym(word):
            continue
        if not meu_analizador.spell(word):
            errors.append(word)
    return errors

def verify_spelling_text(df, file_name, columns_sheets, lang_dict_spell):
    errors, warnings = [], []
    try:
        df = df.copy()
        if df.empty:
            return True, errors, warnings
    
        PATH_DIC = f'dictionaries/{lang_dict_spell}/{lang_dict_spell}.dic'
        PATH_AFF = f'dictionaries/{lang_dict_spell}/{lang_dict_spell}.aff'
        
        meu_analizador = hunspell.HunSpell(PATH_DIC, PATH_AFF)
       
        # Add extra dic to the main dictionary
        extra_dic = 'dictionaries/extra-words.dic'
        meu_analizador.add_dic(extra_dic)
        
        missing_columns = set(columns_sheets) - set(df.columns)
        missing_columns = [str(column) for column in missing_columns]
        if missing_columns:
            warnings.append(f"{file_name}: A verificação de ortografia foi abortada para as colunas: {missing_columns}.")

        # Clean columns_sheets that are not in df
        columns_sheets = [column for column in columns_sheets if column in df.columns]
        
        sheet_warnings = process_sheet(df, columns_sheets, meu_analizador, file_name)
        warnings.extend(sheet_warnings)
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {file_name}: {e}")

    return not errors, errors, warnings
