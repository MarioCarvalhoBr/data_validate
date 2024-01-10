import re
import enum

class TypeDict(enum.Enum):
    TINY = 1
    FULL = 2

def load_dictionary(path):
    with open(path, 'r', encoding='utf-8') as file:
        return [word.strip().lower() for word in file]

def preprocess_text(text):
    # Remover texto após "Fontes:" ou "Fonte:"
    text = text.split("Fontes:")[0]
    text = text.split("Fonte:")[0]

    # Remover tags HTML, abreviações, caracteres especiais e números
    text = re.sub('<.*?>', '', text)
    text = re.sub('\\(.*?\\)', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)

    return text

def find_spelling_errors(text, dictionary):
    words = text.split()
    return [word for word in words if word.lower() not in dictionary]

'''
All words in the dictionary are found in the following sources:
# https://www.academia.org.br/nossa-lingua/busca-no-vocabulario
'''
def verify_sintax_ortography(text, type_dict_spell):
    # Definir o caminho do dicionário com base no tipo
    dict_path = 'dictionaries/pt_BR/tiny.txt' if type_dict_spell == TypeDict.TINY else 'dictionaries/pt_BR/full.txt'
    dictionary = load_dictionary(dict_path)

    preprocessed_text = preprocess_text(text)
    errors = find_spelling_errors(preprocessed_text, dictionary)

    return errors
