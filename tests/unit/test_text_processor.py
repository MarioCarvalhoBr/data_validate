from src.myparser.text_processor import capitalize_nouns_keep_articles_prepositions
from src.myparser.text_processor import capitalize_text

def test_capitalize_nouns_keep_articles_prepositions_1():
    text = "o rato roeu a roupa do rei de roma"
    expected = "O Rato Roeu a Roupa do Rei de Roma"
    result = capitalize_nouns_keep_articles_prepositions(text)
    assert result == expected

def test_capitalize_nouns_keep_articles_prepositions_2():
    text = "o rato roeu a roupa do rei de roma"
    expected = "O rato roeu a roupa do rei de roma"
    result = capitalize_nouns_keep_articles_prepositions(text)
    assert result != expected

def test_capitalize_nouns_keep_articles_prepositions_3():
    text = "o rato roeu a roupa do rei de roma"
    expected = "O Rato roeu a roupa do rei de roma"
    result = capitalize_nouns_keep_articles_prepositions(text)
    assert result != expected
    
def test_capitalize_text_1():
    text = "o rato roeu a roupa do rei de roma"
    expected = "O rato roeu a roupa do rei de roma"
    result = capitalize_text(text)
    assert result == expected
def test_capitalize_text_2():
    text = "O Rato Roeu a Roupa do Rei de Roma"
    expected = "O rato roeu a roupa do rei de roma"
    result = capitalize_text(text)
    assert result == expected

def test_capitalize_text_3():
    text = "O Rato Roeu a Roupa do Rei de Roma"
    expected = "O Rato Roeu a Roupa do Rei de Roma"
    result = capitalize_text(text)
    assert result != expected