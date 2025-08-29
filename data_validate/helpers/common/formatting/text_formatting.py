#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
def capitalize_nouns_keep_articles_prepositions(text):
    # Lista de preposições e artigos em português
    prepositions = ['de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no',
                    'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das', 'à', 'seu', 'sua', 'ou',
                    'quando', 'muito', 'nos', 'já', 'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre',
                    'era', 'depois', 'sem', 'mesmo', 'aos', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'você', 'essa',
                    'num', 'nem', 'suas', 'meu', 'às', 'minha', 'numa', 'pelos', 'elas', 'qual', 'nós', 'lhe', 'deles',
                    'essas', 'esses', 'pelas', 'este', 'dele', 'tu', 'te', 'vocês', 'vos', 'lhes', 'meus', 'minhas',
                    'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta',
                    'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'aquilo', 'estou', 'está',
                    'estamos', 'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam',
                    'estivera', 'estivéramos', 'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos',
                    'estivessem', 'estiver', 'estivermos', 'estiverem', 'hei', 'há', 'havemos', 'hão', 'houve',
                    'houvemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 'houvesse',
                    'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos',
                    'houverão', 'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram',
                    'fui', 'foi', 'fomos', 'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos',
                    'fossem', 'for', 'formos', 'forem', 'serei', 'será']
    # Lista de artigos em português
    articles = ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas']

    # Capitaliza a primeira letra de cada palavra no texto
    text = text.title()

    # Descapitaliza os artigos e preposições
    for article in articles:
        text = text.replace(' ' + article.title() + ' ', ' ' + article + ' ')

    for preposition in prepositions:
        text = text.replace(' ' + preposition.title() + ' ', ' ' + preposition + ' ')

    return text


# Check if the text is an acronym
def is_acronym(text):
    return text.isupper() and len(text) > 1


# Capitalize the first letter of the text
def capitalize_text(text):
    return text.capitalize().strip()


def capitalize_text_keep_acronyms(text):
    words = text.split()  # Divide o texto em palavras
    capitalized_words = []

    for i, word in enumerate(words):
        # Verifica se a palavra é um acrônimo
        if is_acronym(word):
            capitalized_words.append(word)  # Mantém o acrônimo como está
        elif i == 0:
            capitalized_words.append(word.capitalize())  # Capitaliza a primeira palavra da frase
        else:
            capitalized_words.append(word.lower())  # As demais palavras são mantidas em minúsculas

    # Junta as palavras capitalizadas de volta em uma string
    return ' '.join(capitalized_words)