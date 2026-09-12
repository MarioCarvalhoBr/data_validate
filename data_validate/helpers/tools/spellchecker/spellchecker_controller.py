#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from typing import Dict, List, Tuple

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
        # Word-level lookup cache (PERF-006): avoids calling the enchant
        # dictionary more than once per unique word for the lifetime of this
        # controller. Memory bound is roughly the number of unique tokens
        # seen across the run (typical sheets have < 5k unique words), never
        # cleared mid-run since a run only ever validates one dictionary.
        self._check_cache: Dict[str, bool] = {}

    def find_spelling_errors(self, text: str) -> List[str]:
        """Encontra erros ortográficos no texto"""
        # Input string
        preprocessed_text = self.text_processor.sanitize_text(text)
        words = preprocessed_text.split()
        errors = []

        for word in words:
            word = word.strip()
            if not word:
                continue

            if self.text_processor.is_acronym(word):
                continue

            is_correct = self._check_cache.get(word)
            if is_correct is None:
                is_correct = self.dictionary.check(word)
                self._check_cache[word] = is_correct

            if not is_correct:
                errors.append(word)

        return errors

    def evaluate_text_quality(self, text: str) -> Tuple[bool, List[str]]:
        """Compute the row-independent text-quality signals for `text`.

        Both signals (multiple-spaces and spelling errors) depend only on
        the text content, never on which row/column it came from, so a
        caller processing many rows that share the same text (e.g.
        `DataFrameProcessor`) can compute this once per unique text and
        reuse the result for every row (PERF-006).

        Args:
            text: Input string.

        Returns:
            Tuple of (has_multiple_spaces, spelling_errors).
        """
        has_multiple_spaces = self.text_processor.has_multiple_spaces(text)
        spelling_errors = self.find_spelling_errors(text)
        return has_multiple_spaces, spelling_errors

    def format_quality_warnings(
        self,
        has_multiple_spaces: bool,
        spelling_errors: List[str],
        column: str,
        row_index: int,
        sheet_name: str,
    ) -> List[str]:
        """Format row-specific warning messages from precomputed quality signals.

        Args:
            has_multiple_spaces: Whether the text has two or more consecutive spaces.
            spelling_errors: Misspelled words found in the text.
            column: Column name the text came from.
            row_index: Zero-based row index (converted to a 1-based spreadsheet
                line number for the message).
            sheet_name: Name of the sheet/file being validated.

        Returns:
            List of formatted warning messages, empty if there is nothing to report.
        """
        warnings = []

        if has_multiple_spaces:
            warnings.append(
                f"{sheet_name}, linha {row_index + 2}: Há dois ou mais espaços seguidos na coluna {column}."
            )

        if spelling_errors:
            warnings.append(
                f"{sheet_name}, linha {row_index + 2}: "
                f"Palavras com possíveis erros ortográficos na coluna {column}: {spelling_errors}."
            )

        return warnings

    def check_text_quality(self, text: str, column: str, row_index: int, sheet_name: str) -> List[str]:
        """Verifica a qualidade do texto (espaços e ortografia)"""
        has_multiple_spaces, spelling_errors = self.evaluate_text_quality(text)
        return self.format_quality_warnings(has_multiple_spaces, spelling_errors, column, row_index, sheet_name)
