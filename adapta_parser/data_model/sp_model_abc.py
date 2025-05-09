# src/validacao/validator_abc.py
from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import List, Dict, Any
import pandas as pd
import os
from pathlib import Path

from controller.data_importer.api.facade import DataModelImporter


class SpModelABC(ABC):
    INFO = MappingProxyType({
        "EXTENSIONS": [".csv", ".xlsx"],
        "CSV": ".csv",
        "XLSX": ".xlsx",
    })
    def __init__(self, data_model: DataModelImporter):
        # Config vars
        self.FILENAME = data_model.filename
        self.DATA_MODEL = data_model

    @abstractmethod
    def pre_processing(self):
        """
        Defines an abstract method for pre-processing. This method is intended to be implemented
        by subclasses to perform necessary operations prior to executing the primary logic or task.

        This serves as a placeholder for subclass-specific preprocessing logic, and forces derived
        classes to provide their own implementation.

        :raises NotImplementedError: If the method is not overridden in a subclass.
        """
        pass

    @abstractmethod
    def expected_structure_columns(self) -> List[str]:
        """
        Retorna a estrutura esperada das colunas.

        Returns:
            List[str]: Lista de nomes de colunas esperadas.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Executa o processamento do arquivo.
        """
        pass

    def __str__(self):
        """
        Retorna uma representação em string do objeto.

        Returns:
            str: Representação em string do objeto.
        """
        return f"SpModelABC(FILENAME: {self.FILENAME}):\n" + \
               f"  DATA_MODEL: {self.DATA_MODEL}\n"