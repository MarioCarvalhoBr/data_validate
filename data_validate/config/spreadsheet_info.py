#  Copyright (c) 2026 Mário Carvalho (https://github.com/MarioCarvalhoBr).

from typing import List, Dict

from data_validate.helpers.base.constant_base import ConstantBase


class SpreadsheetInfo(ConstantBase):
    """Enum: Constants related to model settings, including spreadsheet names and allowed file extensions."""

    def __init__(self):
        """
        Initialize SpreadsheetInfo with spreadsheet names and allowed file extensions.
        """
        super().__init__()

        # NAMES Spreadsheet Names
        self.SP_NAME_DESCRIPTION: str = "descricao"
        self.SP_NAME_COMPOSITION: str = "composicao"
        self.SP_NAME_VALUES: str = "valores"
        self.SP_NAME_TEMPORAL_REFERENCE: str = "referencia_temporal"
        self.SP_NAME_PROPORTIONALITIES: str = "proporcionalidades"
        self.SP_NAME_SCENARIOS: str = "cenarios"
        self.SP_NAME_LEGEND: str = "legenda"
        self.SP_NAME_DICTIONARY: str = "dicionario"

        # FILES
        self.CSV: str = ".csv"
        self.XLSX: str = ".xlsx"
        self.ALLOWED_EXTENSIONS: List[str] = [self.CSV, self.XLSX]
        """List[str]: Allowed file extensions for input files."""

        # Expected and optional files with their respective extensions
        self.EXPECTED_FILES: Dict[str, List[str]] = {
            self.SP_NAME_DESCRIPTION: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_COMPOSITION: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_VALUES: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_TEMPORAL_REFERENCE: self.ALLOWED_EXTENSIONS,
        }
        """dict: Dictionary of expected file identifiers and their allowed extensions."""

        self.OPTIONAL_FILES: Dict[str, List[str]] = {
            self.SP_NAME_PROPORTIONALITIES: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_SCENARIOS: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_LEGEND: self.ALLOWED_EXTENSIONS,
            self.SP_NAME_DICTIONARY: self.ALLOWED_EXTENSIONS,
        }

        self._finalize_initialization()
        """dict: Dictionary of optional file identifiers and their allowed extensions."""


SHEET = SpreadsheetInfo()
