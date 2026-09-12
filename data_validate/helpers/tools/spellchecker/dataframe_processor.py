#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from typing import List, Tuple

import pandas as pd

from data_validate.helpers.tools.spellchecker.spellchecker_controller import (
    SpellCheckerController,
)


class DataFrameProcessor:
    """Processador de DataFrame para verificação ortográfica"""

    def __init__(self, spell_checker: SpellCheckerController):
        self.spell_checker = spell_checker

    def validate_columns(self, df: pd.DataFrame, columns: List[str], file_name: str) -> Tuple[List[str], List[str]]:
        """Valida se as colunas existem no DataFrame"""
        existing_columns = set(df.columns)
        target_columns = set(columns)
        missing_columns = target_columns - existing_columns

        warnings = []
        if missing_columns:
            warnings.append(
                f"{file_name}: A verificação de ortografia foi abortada para as colunas: {list(missing_columns)}."
            )

        valid_columns = list(target_columns & existing_columns)
        return valid_columns, warnings

    def process_dataframe(self, df: pd.DataFrame, columns: List[str], sheet_name: str) -> List[str]:
        """Processa o DataFrame usando operações vetorizadas"""
        warnings = []

        for column in columns:
            # Filter non-empty rows
            mask = df[column].notna() & (df[column] != "")
            if not mask.any():
                continue

            # Evaluate each unique text only once (PERF-006): quality signals
            # (multiple spaces, spelling errors) depend only on the text
            # content, not on the row it came from, so duplicate texts are
            # only sent to the spell checker/dictionary once per column.
            texts = df.loc[mask, column].astype(str)
            quality_by_text = {text: self.spell_checker.evaluate_text_quality(text) for text in texts.unique()}

            # Iterate rows in the original order, looking up each row's
            # precomputed result, so warnings keep the same per-row messages
            # and ordering as before the dedup.
            for idx, text in texts.items():
                has_multiple_spaces, spelling_errors = quality_by_text[text]
                text_warnings = self.spell_checker.format_quality_warnings(
                    has_multiple_spaces, spelling_errors, column, idx, sheet_name
                )
                warnings.extend(text_warnings)

        return warnings
