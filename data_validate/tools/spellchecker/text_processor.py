#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import re
class TextProcessor:
    """Processador de texto para limpeza e preprocessamento"""

    @staticmethod
    def is_acronym(text: str) -> bool:
        """Verifica se o texto é um acrônimo"""
        return text.isupper() and len(text) > 1

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocessa o texto para verificação ortográfica"""
        # Remove texto após "Fontes:" ou "Fonte:"
        text = re.split("Fontes:|Fonte:", text)[0]
        # Remove HTML, parênteses, pontuação e números
        text = re.sub(r'<.*?>|\(.*?\)|[^\w\s]|\d+', ' ', text)
        return text

    @staticmethod
    def has_multiple_spaces(text: str) -> bool:
        """Verifica se há dois ou mais espaços seguidos"""
        return bool(re.search(r'[ \t\f\v]{2,}', text))
