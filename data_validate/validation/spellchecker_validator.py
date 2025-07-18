#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any

import pandas as pd

from config.config import NamesEnum
from controller.report import ReportList
from data_model import SpDictionary, SpDescription, SpTemporalReference, SpScenario
from tools.spellchecker.spellchecker import SpellChecker
from validation.data_context import DataContext
from validation.validator_model_abc import ValidatorModelABC

class SpellCheckerValidator(ValidatorModelABC):
    """
    Validates the content of the SpScenario spreadsheet.
    """

    def __init__(self, data_context: DataContext, report_list: ReportList, **kwargs: Dict[str, Any]):
        super().__init__(data_context=data_context, report_list=report_list, type_class=SpDictionary, **kwargs)

        # Configure
        self.lang_dict_spell = self._data_context.data_args.data_file.locale
        self.list_words_user = self._data_model.words_to_ignore
        self.spellchecker = SpellChecker(self.lang_dict_spell, self.list_words_user)

        # Run pipeline
        self.run()
    def validate_spellchecker_description(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        model = self._data_context.get_instance_of(SpDescription)
        dataframe = model.DATA_MODEL_IMPORTER.df_data.copy()
        filename = model.FILENAME

        columns_to_check = [
            SpDescription.RequiredColumn.COLUMN_SIMPLE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_NAME.name,
            SpDescription.RequiredColumn.COLUMN_SIMPLE_DESC.name,
            SpDescription.RequiredColumn.COLUMN_COMPLETE_DESC.name,
        ]

        errors_spellchecker, warnings_spellchecker = self.spellchecker.check_spelling_text(df=dataframe, file_name=filename, columns_sheets=columns_to_check)

        errors.extend(errors_spellchecker)
        warnings.extend(warnings_spellchecker)

        return errors, warnings

    def validate_spellchecker_temporal_reference(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        model = self._data_context.get_instance_of(SpTemporalReference)
        dataframe = model.DATA_MODEL_IMPORTER.df_data.copy()
        filename = model.FILENAME

        columns_to_check = [
            SpTemporalReference.RequiredColumn.COLUMN_DESCRIPTION.name,
        ]

        errors_spellchecker, warnings_spellchecker = self.spellchecker.check_spelling_text(df=dataframe, file_name=filename, columns_sheets=columns_to_check)

        errors.extend(errors_spellchecker)
        warnings.extend(warnings_spellchecker)

        return errors, warnings

    def validate_spellchecker_scenario(self) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        model = self._data_context.get_instance_of(SpScenario)
        dataframe = model.DATA_MODEL_IMPORTER.df_data.copy()
        filename = model.FILENAME

        columns_to_check = [
            SpScenario.RequiredColumn.COLUMN_NAME.name,
            SpScenario.RequiredColumn.COLUMN_DESCRIPTION.name,
        ]

        errors_spellchecker, warnings_spellchecker = self.spellchecker.check_spelling_text(df=dataframe,
                                                                                           file_name=filename,
                                                                                           columns_sheets=columns_to_check)

        errors.extend(errors_spellchecker)
        warnings.extend(warnings_spellchecker)

        return errors, warnings

    def run(self) -> Tuple[List[str], List[str]]:
        """Runs all content validations for SpScenario."""

        validations = []
        if not self._data_context.data_args.data_action.no_spellchecker:
            validations.append((self.validate_spellchecker_description, NamesEnum.SPELL.value))
            validations.append((self.validate_spellchecker_temporal_reference, NamesEnum.SPELL.value))

            if self._data_model.LIST_SCENARIOS:
                validations.append((self.validate_spellchecker_scenario, NamesEnum.SPELL.value))

        # BUILD REPORTS
        self.build_reports(validations)

        return self._errors, self._warnings