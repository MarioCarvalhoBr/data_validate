#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from data_validate.helpers.tools.spellchecker.dataframe_processor import (
    DataFrameProcessor,
)
from data_validate.helpers.tools.spellchecker.dictionary_manager import (
    DictionaryManager,
)
from data_validate.helpers.tools.spellchecker.spellchecker_controller import (
    SpellCheckerController,
)


@dataclass(frozen=True)
class SpellingFinding:
    """One structured spelling-quality finding (ARC-017 Phase 3 Port 8).

    Attributes:
        row_index: Zero-based row index the finding belongs to.
        column: Column name the finding belongs to.
        kind: `"multiple_spaces"` or `"misspelled_words"`.
        words: Misspelled words (order/duplicates preserved), empty for `"multiple_spaces"`.
    """

    row_index: int
    column: str
    kind: str
    words: tuple[str, ...] = field(default_factory=tuple)


class SpellChecker:
    """Main spell-checking service for validation bundles.

    Integrates dictionary management and DataFrame processing to check
    multiple sheets and columns for spelling and formatting quality issues.
    """

    def __init__(self, lang_dict_spell: str = "pt_BR", list_words_user: list[str] | None = None):
        self.list_words_user: list[str] = list_words_user if list_words_user is not None else []
        self.lang_dict_spell = lang_dict_spell
        self.dictionary_manager = DictionaryManager(lang_dict_spell)
        self.spell_checker_controller = SpellCheckerController(self.dictionary_manager)
        self.df_processor = DataFrameProcessor(self.spell_checker_controller)

        self.errors_dictionary: list[str] = []

        self._prepare_statement()

    def _prepare_statement(self) -> None:
        # Initialize dictionary with user words.
        self.spell_checker_controller.dictionary = self.dictionary_manager.initialize_dictionary(self.list_words_user)

        # Validate dictionary and collect any initialization errors.
        validation_errors = self.dictionary_manager.validate_dictionary()
        if validation_errors:
            self.errors_dictionary.extend(validation_errors)

    def clean_files_generated(self) -> None:
        self.dictionary_manager.clean_temporary_files()

    def check_spelling_text_structured(
        self, df: pd.DataFrame, columns_sheets: list[str]
    ) -> tuple[tuple[SpellingFinding, ...], str | None]:
        """Structured spelling/quality check for a sheet (ARC-017 Phase 3 Port 8, SPELL-005).

        `rules/spell.py`'s `SPELL-002`…`004` call this: no pre-formatted Portuguese string is
        built here (the rule renders every message through
        the i18n catalog, `.claude/rules/i18n.md`), and no `file_name`/missing-column bookkeeping
        is duplicated — the rule already resolves the file name and already filters
        `columns_sheets` down to columns that exist on `df` before calling this.

        Deliberate broad catch (SPELL-005, `.claude/rules/security.md`): the business rule this
        method implements is "any exception while checking a sheet is caught and reported as one
        error for the file", exactly mirroring `rules/engine.py::Engine._run_one`'s own justified
        broad catch — the failure modes here (a corrupt cell value, a `None` dictionary when the
        backend failed to initialise, an enchant/C-extension error) are not enumerable in advance,
        and the whole point of SPELL-005 is that none of them crash the run; each is instead
        surfaced to the sector team as a distinct issue.

        Args:
            df: The sheet's own working frame (already the model's `self.frame`, not a class
                placeholder).
            columns_sheets: Column names to check; the caller has already filtered out any
                column missing from `df` (this method does not re-check that).

        Returns:
            A `(findings, error)` pair: `findings` is empty and `error` is `None` when `df` is
            empty or no requested column has any non-empty text; otherwise `findings` holds every
            `SpellingFinding` in row order and `error` is `None`, unless processing raised, in
            which case `findings` is empty and `error` is `str(exception)`.
        """
        try:
            df = df.copy()
            if df.empty:
                return (), None

            raw_findings = self.df_processor.find_quality_findings(df, columns_sheets)
            return (
                tuple(
                    SpellingFinding(row_index=int(row_index), column=column, kind=kind, words=tuple(payload or ()))
                    for row_index, column, kind, payload in raw_findings
                ),
                None,
            )
        except Exception as e:
            # Deliberate broad catch: see this method's docstring (SPELL-005).
            return (), str(e)
