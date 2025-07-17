#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

import pandas as pd
from typing import List, Tuple

from tools.spellchecker.spellchecker import SpellChecker


class DataFrameProcessor:
    """Processador de DataFrame para verificação ortográfica"""

    def __init__(self, spell_checker: SpellChecker):
        self.spell_checker = spell_checker

    def validate_columns(self, df: pd.DataFrame, columns: List[str], file_name: str) -> Tuple[List[str], List[str]]:
        """Valida se as colunas existem no DataFrame"""
        existing_columns = set(df.columns)
        target_columns = set(columns)
        missing_columns = target_columns - existing_columns

        warnings = []
        if missing_columns:
            warnings.append(
                f"{file_name}: A verificação de ortografia foi abortada "
                f"para as colunas: {list(missing_columns)}."
            )

        valid_columns = list(target_columns & existing_columns)
        return valid_columns, warnings

    def process_dataframe(self, df: pd.DataFrame, columns: List[str], sheet_name: str) -> List[str]:
        """Processa o DataFrame usando operações vetorizadas"""
        warnings = []

        for column in columns:
            # Filtra linhas não vazias
            mask = df[column].notna() & (df[column] != "")
            if not mask.any():
                continue

            # Processa cada linha válida
            for idx in df[mask].index:
                text = str(df.loc[idx, column])
                text_warnings = self.spell_checker.check_text_quality(
                    text, column, idx, sheet_name
                )
                warnings.extend(text_warnings)

        return warnings
