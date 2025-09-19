#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

from data_validate.config.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.helpers.common.validation.data_validation import (
    check_punctuation,
    check_unique_values,
)
from data_validate.models import SpScenario
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


class SpScenarioValidator(ValidatorModelABC):
    """
    Validates the content of the SpScenario spreadsheet.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpScenario,
            **kwargs,
        )

        # Run pipeline
        self.run()

    def validate_punctuation(self) -> Tuple[List[str], List[str]]:
        warnings = []

        columns_dont_punctuation = [SpScenario.RequiredColumn.COLUMN_NAME.name]
        columns_must_end_with_dot = [SpScenario.RequiredColumn.COLUMN_DESCRIPTION.name]

        list_columns = list(columns_dont_punctuation + columns_must_end_with_dot)
        for column in list_columns:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)

        _, punctuation_warnings = check_punctuation(
            self._dataframe,
            self._filename,
            columns_dont_punctuation,
            columns_must_end_with_dot,
        )
        warnings.extend(punctuation_warnings)
        return [], warnings

    def validate_unique_values(self) -> Tuple[List[str], List[str]]:
        errors = []

        columns_to_check = [
            SpScenario.RequiredColumn.COLUMN_NAME.name,
            SpScenario.RequiredColumn.COLUMN_SYMBOL.name,
        ]

        # Check if columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                errors.append(msg_error_column)

        __, unique_errors = check_unique_values(
            dataframe=self._dataframe,
            file_name=self._filename,
            columns_uniques=columns_to_check,
        )
        errors.extend(unique_errors)

        return errors, []

    def _prepare_statement(self):
        pass

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""

        validations = [
            (self.validate_punctuation, NamesEnum.MAND_PUNC_SCEN.value),
            (self.validate_unique_values, NamesEnum.UVR_SCEN.value),
        ]
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings
        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings
