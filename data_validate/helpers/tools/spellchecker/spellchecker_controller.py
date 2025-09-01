#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

from typing import List

from data_validate.helpers.tools.spellchecker.dictionary_manager import (
    DictionaryManager,
)
from data_validate.helpers.tools.spellchecker.text_processor import TextProcessor


class SpellCheckerController:
    """Verificador ortográfico principal"""

    def __init__(self, dictionary_manager: DictionaryManager):
        self.dictionary_manager = dictionary_manager
        self.text_processor = TextProcessor()
        self.dictionary = None

    def find_spelling_errors(self, text: str) -> List[str]:
        """Encontra erros ortográficos no texto"""
        preprocessed_text = self.text_processor.preprocess_text(text)
        words = preprocessed_text.split()
        errors = []

        for word in words:
            word = word.strip()
            if not word:
                continue

            if self.text_processor.is_acronym(word):
                continue

            if not self.dictionary.check(word):
                errors.append(word)

        return errors

    def check_text_quality(
        self, text: str, column: str, row_index: int, sheet_name: str
    ) -> List[str]:
        """Verifica a qualidade do texto (espaços e ortografia)"""
        warnings = []

        # Verifica espaços múltiplos
        if self.text_processor.has_multiple_spaces(text):
            warnings.append(
                f"{sheet_name}, linha {row_index + 2}: "
                f"Há dois ou mais espaços seguidos na coluna {column}."
            )

        # Verifica ortografia
        spelling_errors = self.find_spelling_errors(text)
        if spelling_errors:
            warnings.append(
                f"{sheet_name}, linha {row_index + 2}: "
                f"Palavras com possíveis erros ortográficos na coluna {column}: {spelling_errors}."
            )

        return warnings
