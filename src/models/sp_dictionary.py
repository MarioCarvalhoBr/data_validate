from typing import List, Dict, Any
import pandas as pd

from src.controllers.context.general_context import GeneralContext
from src.helpers.base.constant_base import ConstantBase
from src.models.sp_model_abc import SpModelABC
from src.helpers.tools.data_loader.api.facade import (
    DataLoaderModel,
)
from src.helpers.common.validation.column_validation import check_column_names
from src.helpers.common.formatting.error_formatting import (
    format_errors_and_warnings,
)


class SpDictionary(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "dicionario"
            self.SP_DESCRIPTION = "Planilha de dicionario"
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_WORD = pd.Series(dtype="str", name="palavra")

        ALL = [
            COLUMN_WORD.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(context, data_model, **kwargs)

        self.words_to_ignore: List[str] = []

        self.run()

    def pre_processing(self):
        """
        Lê as palavras do arquivo de dicionário.
        Cada linha do arquivo é considerada uma palavra a ser ignorada.
        Esta versão corrige o problema da primeira palavra ser tratada como cabeçalho
        pelo leitor de DataFrame, comum quando não há cabeçalho explícito no arquivo.
        """
        self.words_to_ignore = []
        if self.data_loader_model and self.data_loader_model.df_data is not None:
            df = self.data_loader_model.df_data

            if len(df.columns) > 0:
                remaining_words = []
                if not df.empty:
                    remaining_words = df.iloc[:, 0].astype(str).tolist()

                self.words_to_ignore = remaining_words

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def post_processing(self):
        pass

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
