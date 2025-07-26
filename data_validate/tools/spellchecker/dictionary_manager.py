#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import os
import enchant
from enchant import Broker
from pathlib import Path
from typing import List


class DictionaryManager:
    """Gerenciador de dicionários Enchant"""

    def __init__(self, lang_dict_spell: str):
        self.lang_dict_spell = lang_dict_spell
        self.dictionary = None
        self.broker = None
        self._setup_paths()
        self._errors = []

    def _setup_paths(self) -> None:
        """Configura os caminhos dos arquivos de dicionário"""
        current_file = Path(__file__)
        static_path = current_file.parent.parent.parent.parent / 'data_validate/static'
        enchant_config_dir = static_path / 'dictionaries'

        # Define o diretório de configuração do Enchant
        os.environ["ENCHANT_CONFIG_DIR"] = str(enchant_config_dir)

    def validate_dictionary(self) -> List[str]:
        """Valida se o dicionário existe"""

        try:
            self.broker = Broker()
            if not self.broker.dict_exists(self.lang_dict_spell):
                self._errors.append(f"Dicionário {self.lang_dict_spell} não encontrado")
        except Exception as e:
            self._errors.append(f"Erro ao verificar dicionário: {e}")

        return self._errors

    def initialize_dictionary(self, list_words_user) -> enchant.Dict:
        """Inicializa o dicionário Enchant e adiciona palavras extras"""
        try:
            if not self.broker:
                self.broker = Broker()

            self.dictionary = self.broker.request_dict(self.lang_dict_spell)

            # Adiciona palavras extras do arquivo extra-words.dic
            self._load_extra_words()

            # Adiciona palavras do usuário
            for word in list_words_user:
                if word and not word.startswith('#'):
                    self.dictionary.add(word)

            return self.dictionary
        except Exception as e:
            self._errors.append(f"Erro ao inicializar dicionário {self.lang_dict_spell}: {e}")

    def _load_extra_words(self) -> None:
        """Carrega palavras extras do arquivo extra-words.dic"""
        try:
            current_file = Path(__file__)
            static_path = current_file.parent.parent.parent.parent / 'data_validate/static'
            extra_words_path = static_path / 'dictionaries' / 'extra-words.dic'

            if extra_words_path.exists():
                with open(extra_words_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        word = line.strip()
                        if word and not word.startswith('#'):  # Ignora linhas vazias e comentários
                            self.dictionary.add(word)
            else:
                self._errors.append("Arquivo extra-words.dic não encontrado. Reporte o erro ao administrador do sistema.")
        except Exception as e:
            # Log do erro mas não interrompe a execução
            self._errors.append(f"Aviso: Não foi possível carregar palavras extras: {e}")