#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

"""
Context module for data models management.

This module defines the `DataModelsContext` class, which extends the `GeneralContext`
to manage the lifecycle and access to spreadsheet data models during the validation process.
"""

from typing import List, Any, Dict
from typing import Type, Optional

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.models.sp_model_abc import SpModelABC


class DataModelsContext(GeneralContext):
    """
    Context manager for spreadsheet data models.

    This class holds the state of loaded data models, aggregation of errors and warnings,
    and reporting lists. It serves as a central point for accessing different model instances
    during the validation pipeline.

    Attributes:
        context (GeneralContext): The parent context containing configuration, logger, etc.
        models_to_use (List[Any]): List of initialized model instances.
        data (Dict): Dictionary to store processed data.
        errors (List): List to aggregate validation errors.
        warnings (List): List to aggregate validation warnings.
        report_list (List): List to store report entries.
    """

    def __init__(
        self,
        context: GeneralContext,
        models_to_use: List[Any] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the DataModelsContext.

        Args:
            context (GeneralContext): The parent application context.
            models_to_use (List[Any], optional): List of models to be managed. Defaults to None.
            **kwargs: Additional keyword arguments passed to the parent `GeneralContext`.
        """
        super().__init__(
            data_args=context.data_args,
            **kwargs,
        )

        self.context = context
        self.models_to_use = models_to_use or []

        self.data = {}
        self.errors = []
        self.warnings = []
        self.report_list = []

    def get_instance_of(self, model_class: Type[SpModelABC]) -> Optional[SpModelABC]:
        """
        Retrieves an instance of a specific model class from the context.

        Args:
            model_class (Type[SpModelABC]): The class of the model to look up.

        Returns:
            Optional[SpModelABC]: The instance of the specified model class if found,
            otherwise None.
        """
        for model in self.models_to_use:
            # case A: model is already an instance
            if isinstance(model, model_class):
                # print(f"Model instance found: {model.__class__.__name__}")
                return model

        return None
