import re
import pandas as pd
import hunspell

def load_dictionary(path):
    with open(path, 'r', encoding='utf-8') as file:
        return {word.strip().lower() for word in file}

def preprocess_text(text):
    text = re.split("Fontes:|Fonte:", text)[0]
    text = re.sub(r'<.*?>|\(.*?\)|[^\w\s]|\d+', ' ', text)

    return text

def find_spelling_errors(text, meu_analizador):
    words = text.split()
    return [word for word in words if not meu_analizador.spell(word.strip())]

def verify_text(column_name, text, meu_analizador, index, sheet_name):
    errors = verify_sintax_ortography(text, meu_analizador)
    if errors:
        return f"{sheet_name}, linha {index + 1}: Palavras com possíveis erros ortográficos na coluna {column_name}: {errors}."
    return ""

def verify_sintax_ortography(text, meu_analizador):
    preprocessed_text = preprocess_text(text)
    return find_spelling_errors(preprocessed_text, meu_analizador)

def process_sheet(df, columns, meu_analizador, sheet_name):
    warnings = []
    for index, row in df.iterrows():
        for column in columns:
            text = row[column]
            # Verifique se o texto está vazio ou nan 
            if pd.isna(text) or text == "":
                text = ""
            warning = verify_text(column, text, meu_analizador, index, sheet_name)
            if warning:
                warnings.append(warning)
    return warnings

def run(df, file_name, columns_sheets, lang_dict_spell):
    df = df.copy()
    errors, warnings = [], []
    
    try:
        PATH_DIC = f'dictionaries/{lang_dict_spell}/{lang_dict_spell}.dic'
        PATH_AFF = f'dictionaries/{lang_dict_spell}/{lang_dict_spell}.aff'
        
        meu_analizador = hunspell.HunSpell(PATH_DIC, PATH_AFF)
       
        # Add extra dic to the main dictionary
        extra_dic = 'dictionaries/extra-words.dic'
        meu_analizador.add_dic(extra_dic)

        
        # Verifica se todas as colunas existem em df
        columns_sheets = [column for column in columns_sheets if column in df.columns]
        
        sheet_warnings = process_sheet(df, columns_sheets, meu_analizador, file_name)
        warnings.extend(sheet_warnings)
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {file_name}: {e}")

    return not errors, errors, warnings
