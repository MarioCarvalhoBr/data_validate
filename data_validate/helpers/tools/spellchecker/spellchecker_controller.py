#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from data_validate.helpers.tools.spellchecker.dictionary_manager import (
    DictionaryManager,
)
from data_validate.helpers.tools.spellchecker.text_processor import TextProcessor

if TYPE_CHECKING:
    from enchant import Dict as EnchantDict


class SpellCheckerController:
    """Main spell-checking service for text quality validation.

    Caches per-word spell-check results (PERF-006) to avoid redundant dictionary
    lookups across the validation run.
    """

    def __init__(self, dictionary_manager: DictionaryManager):
        self.dictionary_manager = dictionary_manager
        self.text_processor = TextProcessor()
        self.dictionary: EnchantDict | None = None
        # Word-level lookup cache (PERF-006): avoids calling the enchant
        # dictionary more than once per unique word for the lifetime of this
        # controller. Memory bound is roughly the number of unique tokens
        # seen across the run (typical sheets have < 5k unique words), never
        # cleared mid-run since a run only ever validates one dictionary.
        self._check_cache: dict[str, bool] = {}

    def find_spelling_errors(self, text: str) -> list[str]:
        """Find spelling errors in the given text.

        Args:
            text: Input string to check.

        Returns:
            List of misspelled words found."""
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
                # `self.dictionary` is `None` when the backend failed to initialise; calling
                # `.check` on it then raises `AttributeError` by design (SPELL-005) — this
                # `cast` is typing-only narrowing, not a new guard, and preserves that.
                is_correct = cast("EnchantDict", self.dictionary).check(word)
                self._check_cache[word] = is_correct

            if not is_correct:
                errors.append(word)

        return errors

    def evaluate_text_quality(self, text: str) -> tuple[bool, list[str]]:
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

    def build_quality_findings(
        self,
        has_multiple_spaces: bool,
        spelling_errors: list[str],
        column: str,
        row_index: int,
    ) -> list[tuple[int, str, str, list[str] | None]]:
        """Turn precomputed quality signals into structured `(row, column, kind, payload)` findings.

        ARC-017 Phase 3 Port 8: `rules/spell.py`'s `SPELL-002`…`004` consume this structured
        result instead of a pre-formatted Portuguese string, so the rule (not this backend
        module) chooses the catalog key and renders the final message (`.claude/rules/i18n.md`).

        Args:
            has_multiple_spaces: Whether the text has two or more consecutive spaces.
            spelling_errors: Misspelled words found in the text, in the order
                `find_spelling_errors` produced them (duplicates and order preserved).
            column: Column name the text came from.
            row_index: Zero-based row index.

        Returns:
            List of `(row_index, column, kind, payload)` tuples, `kind` one of
            `"multiple_spaces"` (`payload` is `None`) or `"misspelled_words"` (`payload` is the
            `spelling_errors` list); empty when neither signal is set; both entries are present,
            multiple-spaces first, when both signals are set for the same row/column.
        """
        findings: list[tuple[int, str, str, list[str] | None]] = []
        if has_multiple_spaces:
            findings.append((row_index, column, "multiple_spaces", None))
        if spelling_errors:
            findings.append((row_index, column, "misspelled_words", list(spelling_errors)))
        return findings
