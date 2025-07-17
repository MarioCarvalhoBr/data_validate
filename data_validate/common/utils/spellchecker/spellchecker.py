#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

import re
import pandas as pd
import hunspell
from pathlib import Path
from typing import List, Tuple, Set
from dataclasses import dataclass


@dataclass
class SpellCheckResult:
    """Resultado da verificação ortográfica"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


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


class DictionaryManager:
    """Gerenciador de dicionários Hunspell"""

    def __init__(self, lang_dict_spell: str):
        self.lang_dict_spell = lang_dict_spell
        self.analyzer = None
        self._setup_paths()

    def _setup_paths(self) -> None:
        """Configura os caminhos dos arquivos de dicionário"""
        current_file = Path(__file__)
        static_path = current_file.parent.parent.parent.parent / 'static'

        self.dic_path = static_path / 'dictionaries/hunspell' / f'{self.lang_dict_spell}.dic'
        self.aff_path = static_path / 'dictionaries/hunspell' / f'{self.lang_dict_spell}.aff'
        self.extra_dic_path = static_path / 'dictionaries' / 'extra-words.dic'

    def validate_files(self) -> List[str]:
        """Valida se os arquivos de dicionário existem"""
        errors = []

        if not self.dic_path.exists():
            errors.append(f"Arquivo de dicionário não encontrado: {self.dic_path}")

        if not self.aff_path.exists():
            errors.append(f"Arquivo de afixos não encontrado: {self.aff_path}")

        return errors

    def initialize_analyzer(self) -> hunspell.HunSpell:
        """Inicializa o analisador Hunspell"""
        self.analyzer = hunspell.HunSpell(str(self.dic_path), str(self.aff_path))

        if self.extra_dic_path.exists():
            self.analyzer.add_dic(str(self.extra_dic_path))

        return self.analyzer


class SpellChecker:
    """Verificador ortográfico principal"""

    def __init__(self, dictionary_manager: DictionaryManager):
        self.dictionary_manager = dictionary_manager
        self.text_processor = TextProcessor()
        self.analyzer = None

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

            if not self.analyzer.spell(word):
                errors.append(word)

        return errors

    def check_text_quality(self, text: str, column: str, row_index: int, sheet_name: str) -> List[str]:
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


class SpellCheckService:
    """Serviço principal para verificação ortográfica"""

    def __init__(self, lang_dict_spell: str = 'pt_BR'):
        self.lang_dict_spell = lang_dict_spell
        self.dictionary_manager = DictionaryManager(lang_dict_spell)
        self.spell_checker = SpellChecker(self.dictionary_manager)
        self.df_processor = DataFrameProcessor(self.spell_checker)

    def verify_spelling_text(self, df: pd.DataFrame, file_name: str, columns_sheets: List[str]) -> SpellCheckResult:
        """Verifica ortografia em texto com tratamento melhorado de erros"""
        errors, warnings = [], []

        try:
            df = df.copy()
            if df.empty:
                return SpellCheckResult(is_valid=True, errors=errors, warnings=warnings)

            # Valida arquivos de dicionário
            validation_errors = self.dictionary_manager.validate_files()
            if validation_errors:
                errors.extend(validation_errors)
                return SpellCheckResult(is_valid=False, errors=errors, warnings=warnings)

            # Inicializa analisador
            self.spell_checker.analyzer = self.dictionary_manager.initialize_analyzer()

            # Valida colunas
            valid_columns, column_warnings = self.df_processor.validate_columns(
                df, columns_sheets, file_name
            )
            warnings.extend(column_warnings)

            # Processa DataFrame
            if valid_columns:
                processing_warnings = self.df_processor.process_dataframe(
                    df, valid_columns, file_name
                )
                warnings.extend(processing_warnings)

        except Exception as e:
            errors.append(f"Erro ao processar o arquivo {file_name}: {e}")

        return SpellCheckResult(is_valid=not errors, errors=errors, warnings=warnings)


def main():
    """Exemplo de uso"""
    df = pd.DataFrame({
        'texto_sem_erro': ['Esse texto não tem erros', 'Outro texto correto', 'Mais um texto sem erros'],
        'texto_com_erros_pt': ['Esse textoz tem um erro ortográfico', 'Outrozz texto com erros',
                               'Mais umumuuuu texto com erros'],
    })

    columns_sheets = ['texto_sem_erro', 'texto_com_erros_pt']
    file_name = 'example.xlsx'

    service = SpellCheckService('pt_BR')
    result = service.verify_spelling_text(df, file_name, columns_sheets)

    print("Valid:", result.is_valid)
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)


if __name__ == "__main__":
    main()