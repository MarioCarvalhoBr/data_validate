#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any, Type, Union

from data_validate.config.config import NamesEnum
from data_validate.controllers.report.model_report import ModelListReport
from data_validate.models import (
    SpDictionary,
    SpDescription,
    SpTemporalReference,
    SpScenario,
)
from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.validators.spreadsheets.base.validator_model_abc import (
    ValidatorModelABC,
)


class SpellCheckerValidator(ValidatorModelABC):
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
            type_class=SpDictionary,
            **kwargs,
        )

        # Configure
        self.dictionary: SpDictionary | None = self._data_models_context.get_instance_of(SpDictionary)
        self.lang_dict_spell = self._data_models_context.data_args.data_file.locale

        # From SpDictionary extract words to ignore
        self.list_words_user = self.dictionary.words_to_ignore

        # My spellchecker
        self.spellchecker = SpellChecker(self.lang_dict_spell, self.list_words_user)

        # Define column mappings for each model type
        self.model_columns_map: Dict[Type[Union[SpDescription, SpTemporalReference, SpScenario]], List[str]] = {
            SpDescription: [
                SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
                SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
                SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name,
                SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name,
            ],
            SpTemporalReference: [
                SpTemporalReference.RequiredColumn.COLUMN_DESCRIPTION.name,
            ],
            SpScenario: [
                SpScenario.RequiredColumn.COLUMN_NAME.name,
                SpScenario.RequiredColumn.COLUMN_DESCRIPTION.name,
            ],
        }

        # Run pipeline
        self.run()

    def validate_spellchecker(self, model_class: Type[Union[SpDescription, SpTemporalReference, SpScenario]]) -> Tuple[List[str], List[str]]:
        """
        Generic spellchecker validation method that works with any model class.

        Args:
            model_class: The model class to validate (e.g., SpDescription, SpTemporalReference, SpScenario)

        Returns:
            Tuple containing lists of errors and warnings
        """
        errors, warnings = [], []

        # Configure local instances
        self._data_model = self._data_models_context.get_instance_of(model_class)
        self._dataframe = self._data_model.data_loader_model.df_data.copy()
        self._filename = self._data_model.filename

        if self._dataframe.empty:
            return errors, warnings

        # Get columns to check for this model
        columns_to_check = self.model_columns_map.get(model_class, [])

        if not columns_to_check:
            # If no columns defined for this model, skip validation
            return errors, warnings

        # Check if the columns exist
        for column in columns_to_check:
            exists_column, msg_error_column = self._column_exists(column)
            if not exists_column:
                warnings.append(msg_error_column)
                continue

        # Perform spellcheck
        errors_spellchecker, warnings_spellchecker = self.spellchecker.check_spelling_text(
            df=self._dataframe,
            file_name=self._filename,
            columns_sheets=columns_to_check,
        )

        errors.extend(errors_spellchecker)
        warnings.extend(warnings_spellchecker)

        return errors, warnings

    def _prepare_statement(self):
        if self.spellchecker.errors_dictionary:
            self._errors.extend(self.spellchecker.errors_dictionary)

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""

        validations = []
        if not self._data_models_context.data_args.data_action.no_spellchecker:
            # Add validation for Description
            validations.append(
                (
                    lambda: self.validate_spellchecker(SpDescription),
                    NamesEnum.SPELL.value,
                )
            )

            # Add validation for Temporal Reference
            validations.append(
                (
                    lambda: self.validate_spellchecker(SpTemporalReference),
                    NamesEnum.SPELL.value,
                )
            )

            # Add validation for Scenario if scenarios exist
            if self._data_model.scenarios_list:
                validations.append(
                    (
                        lambda: self.validate_spellchecker(SpScenario),
                        NamesEnum.SPELL.value,
                    )
                )

        # BUILD REPORTS
        self.build_reports(validations)

        # Cleanup temporary files
        self.spellchecker.clean_files_generated()

        return self._errors, self._warnings
