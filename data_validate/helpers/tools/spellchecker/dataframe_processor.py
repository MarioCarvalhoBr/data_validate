#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from typing import cast

import pandas as pd

from data_validate.helpers.tools.spellchecker.spellchecker_controller import (
    SpellCheckerController,
)


class DataFrameProcessor:
    """Process DataFrames to find spelling and formatting quality issues.

    Evaluates each unique text value per column exactly once (PERF-006),
    then emits findings for every row/column/signal combination.
    """

    def __init__(self, spell_checker: SpellCheckerController):
        self.spell_checker = spell_checker

    def find_quality_findings(
        self, df: pd.DataFrame, columns: list[str]
    ) -> list[tuple[int, str, str, list[str] | None]]:
        """Evaluate each text column for spelling/formatting quality issues (ARC-017 Phase 3 Port 8).

        Evaluates each unique text per column exactly once (PERF-006), then emits one
        `(row_index, column, kind, payload)` finding per row/column/signal, in original row
        order — `rules/spell.py`'s `SPELL-002`…`004` consume this instead of a pre-formatted
        Portuguese string.

        Args:
            df: DataFrame to scan (already filtered to the model's own working frame).
            columns: Column names to check.

        Returns:
            List of `(row_index, column, kind, payload)` tuples; see
            `SpellCheckerController.build_quality_findings` for `kind`/`payload`'s shape.
        """
        findings: list[tuple[int, str, str, list[str] | None]] = []

        for column in columns:
            mask = df[column].notna() & (df[column] != "")
            if not mask.any():
                continue

            texts = df.loc[mask, column].astype(str)
            quality_by_text = {text: self.spell_checker.evaluate_text_quality(text) for text in texts.unique()}

            for idx, text in texts.items():
                has_multiple_spaces, spelling_errors = quality_by_text[text]
                findings.extend(
                    self.spell_checker.build_quality_findings(
                        has_multiple_spaces, spelling_errors, column, cast(int, idx)
                    )
                )

        return findings
