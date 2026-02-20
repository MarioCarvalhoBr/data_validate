#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

# File: data_loader/config.py
"""
Singleton de configuração central de arquivos.
"""


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    """
    Define quais arquivos são esperados, seu tipo de cabeçalho e separador CSV.
    """

    def __init__(self):
        # nome_base: (obrigatório: bool, tipo_cabeçalho: 'single'|'double'|'qml', separador_csv: str|None)
        self.file_specs = {
            "descricao": (True, "single", "|"),
            "composicao": (True, "single", "|"),
            "valores": (True, "single", "|"),
            "referencia_temporal": (True, "single", "|"),
            "proporcionalidades": (False, "double", "|"),
            "cenarios": (False, "single", "|"),
            "legenda": (False, "single", "|"),
            "dicionario": (False, "single", "|"),
        }
        self.extensions = [".csv", ".xlsx", ".qml"]


config = Config()
