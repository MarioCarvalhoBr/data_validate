#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import pandas as pd
from typing import List, Tuple

from src.helpers.tools.spellchecker.dictionary_manager import (
    DictionaryManager,
)
from src.helpers.tools.spellchecker.spellchecker_controller import (
    SpellCheckerController,
)
from src.helpers.tools.spellchecker.dataframe_processor import (
    DataFrameProcessor,
)


class SpellChecker:
    """Serviço principal para verificação ortográfica"""

    def __init__(self, lang_dict_spell: str = "pt_BR", list_words_user: List[str] = None):
        self.list_words_user = list_words_user
        if self.list_words_user is None:
            self.list_words_user = []
        self.lang_dict_spell = lang_dict_spell
        self.dictionary_manager = DictionaryManager(lang_dict_spell)
        self.spell_checker_controller = SpellCheckerController(self.dictionary_manager)
        self.df_processor = DataFrameProcessor(self.spell_checker_controller)

        self.errors_dictionary = []

        self._prepare_statement()

    def _prepare_statement(self) -> None:
        # Inicializa dicionário
        self.spell_checker_controller.dictionary = self.dictionary_manager.initialize_dictionary(self.list_words_user)

        # Valida dicionário
        validation_errors = self.dictionary_manager.validate_dictionary()
        if validation_errors:
            self.errors_dictionary.extend(validation_errors)

    def clean_files_generated(self) -> None:
        self.dictionary_manager.clean_temporary_files()

    def check_spelling_text(self, df: pd.DataFrame, file_name: str, columns_sheets: List[str]) -> Tuple[List[str], List[str]]:
        """Verifica ortografia em texto com tratamento melhorado de erros"""

        errors, warnings = [], []

        try:
            df = df.copy()
            if df.empty:
                return errors, warnings

            # Valida colunas
            valid_columns, column_warnings = self.df_processor.validate_columns(df, columns_sheets, file_name)
            # warnings.extend(column_warnings)

            # Processa DataFrame
            if valid_columns:
                processing_warnings = self.df_processor.process_dataframe(df, valid_columns, file_name)
                warnings.extend(processing_warnings)

        except Exception as e:
            errors.append(f"Erro ao processar o arquivo {file_name}: {e}")

        return errors, warnings
