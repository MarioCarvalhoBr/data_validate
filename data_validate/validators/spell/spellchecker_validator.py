#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Spell checking validator module for validating textual content across spreadsheet models.

This module provides spell checking validation functionality for various spreadsheet
models including Description, Temporal Reference, and Scenario spreadsheets.
"""

from typing import List, Tuple, Dict, Any, Type, Union

from data_validate.config import NamesEnum
from data_validate.controllers.context.data_context import DataModelsContext
from data_validate.controllers.report.validation_report import ValidationReport
from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker
from data_validate.models import (
    SpDictionary,
    SpDescription,
    SpTemporalReference,
    SpScenario,
)
from data_validate.validators.spreadsheets.base.base_validator import BaseValidator


class SpellCheckerValidator(BaseValidator):
    """
    Validates textual content using spell checking across multiple spreadsheet models.

    This validator performs spell checking on text columns in Description, Temporal Reference,
    and Scenario spreadsheets. It uses a custom dictionary and user-defined words to ignore
    during validation.

    Attributes
    ----------
    dictionary : SpDictionary | None
        Dictionary model instance containing words to ignore during spell checking.
    lang_dict_spell : str
        Language code for spell checking dictionary.
    list_words_user : List[str]
        User-defined words to ignore during spell checking.
    spellchecker : SpellChecker
        Spell checker instance configured with language and custom dictionary.
    model_columns_map : Dict[Type[Union[SpDescription, SpTemporalReference, SpScenario]], List[str]]
        Mapping of model types to their respective columns that require spell checking.
    """

    def __init__(
        self,
        data_models_context: DataModelsContext,
        validation_reports: ValidationReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the spell checker validator.

        Args
        ----
        data_models_context : DataModelsContext
            Context containing all loaded spreadsheet models.
        validation_reports : ValidationReport
            Report aggregator for collecting validation results.
        **kwargs : Dict[str, Any]
            Additional keyword arguments passed to parent validator.
        """
        super().__init__(
            data_models_context=data_models_context,
            validation_reports=validation_reports,
            type_class=SpDictionary,
            **kwargs,
        )

        self.dictionary: SpDictionary | None = self._data_models_context.get_instance_of(SpDictionary)
        self.lang_dict_spell: str = self._data_models_context.data_args.data_file.locale

        self.list_words_user: List[str] = self.dictionary.words_to_ignore

        self.spellchecker: SpellChecker = SpellChecker(self.lang_dict_spell, self.list_words_user)

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

        self.run()

    def validate_spellchecker(self, model_class: Type[Union[SpDescription, SpTemporalReference, SpScenario]]) -> Tuple[List[str], List[str]]:
        """
        Perform spell checking validation on specified model class.

        Validates textual content in specified columns of the given model using the
        configured spell checker. Missing columns generate warnings, while spelling
        errors generate errors or warnings based on severity.

        Args
        ----
        model_class : Type[Union[SpDescription, SpTemporalReference, SpScenario]]
            The model class to validate (e.g., SpDescription, SpTemporalReference, SpScenario).

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List of error messages from spell checking
                - List of warning messages from spell checking

        Notes
        -----
        - Returns empty lists if the dataframe is empty
        - Returns empty lists if no columns are configured for the model
        - Warns about missing columns but continues validation for existing ones
        """
        errors, warnings = [], []

        # Configure local instances
        self._data_model = self._data_models_context.get_instance_of(model_class)
        self._dataframe = self._data_model.data_loader_model.raw_data.copy()
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

        errors.extend(sorted(errors_spellchecker))
        warnings.extend(sorted(warnings_spellchecker))

        return errors, warnings

    def _prepare_statement(self) -> None:
        """
        Prepare validation errors from dictionary initialization.

        Extends the internal errors list with any errors encountered during
        dictionary loading or initialization by the spell checker.

        Notes
        -----
        This method is called internally during validation preparation to collect
        any errors from the spell checker's dictionary initialization process.
        """
        if self.spellchecker.errors_dictionary:
            self._errors.extend(self.spellchecker.errors_dictionary)

    def run(self) -> Tuple[List[str], List[str]]:
        """
        Execute all spell checking validations across configured models.

        Orchestrates the spell checking validation process for Description, Temporal Reference,
        and optionally Scenario models if they exist and spell checking is enabled.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing:
                - List of all error messages from validation
                - List of all warning messages from validation

        Notes
        -----
        - Spell checking can be disabled via command line flag `--no-spellchecker`
        - Scenario validation only runs if scenarios exist in the dataset
        - Temporary spell checker files are cleaned up after validation completes
        - All validation results are aggregated into reports via `build_reports()`
        """
        validations = []
        if not self._data_models_context.data_args.data_action.no_spellchecker:
            validations.append(
                (
                    lambda: self.validate_spellchecker(SpDescription),
                    NamesEnum.SPELL.value,
                )
            )

            validations.append(
                (
                    lambda: self.validate_spellchecker(SpTemporalReference),
                    NamesEnum.SPELL.value,
                )
            )

            if self._data_model.scenarios:
                validations.append(
                    (
                        lambda: self.validate_spellchecker(SpScenario),
                        NamesEnum.SPELL.value,
                    )
                )

        self.build_reports(validations)

        self.spellchecker.clean_files_generated()

        return self._errors, self._warnings
