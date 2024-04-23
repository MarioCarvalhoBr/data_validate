from src.myparser.text_processor import capitalize_nouns_keep_articles_prepositions
from src.myparser.text_processor import capitalize_text, capitalize_text_keep_acronyms

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

def test_capitalize_text_keep_acronyms_1():
    text = "this is a test"
    expected = "This is a test"
    result = capitalize_text_keep_acronyms(text)
    assert result == expected

def test_capitalize_text_keep_acronyms_2():
    text = "this is a TEST"
    expected = "This is a TEST"
    result = capitalize_text_keep_acronyms(text)
    assert result == expected

def test_capitalize_text_keep_acronyms_3():
    text = ""
    expected = ""
    result = capitalize_text_keep_acronyms(text)
    assert result == expected
