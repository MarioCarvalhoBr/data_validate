#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

"""
Context module for data models management.

This module defines the `DataModelContext` class, which extends the `GeneralContext`
to manage the lifecycle and access to spreadsheet data models during the validation process.
"""

from typing import List, Any
from typing import Type, Optional

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.models.sp_model_abc import SpModelABC


class DataModelContext:
    """
    Context manager for spreadsheet data models.

    This class holds the state of loaded data models and serves as a central point
    for accessing different model instances during the validation pipeline.

    Attributes:
        context (GeneralContext): The parent context containing configuration, logger, etc.
        initialized_models (List[Any]): List of initialized model instances.
    """

    def __init__(
        self,
        context: GeneralContext,
        initialized_models: List[Any] = None,
    ):
        """
        Initialize the DataModelContext.

        Args:
            context (GeneralContext): The parent application context.
            initialized_models (List[Any], optional): List of models to be managed. Defaults to None.
        """
        self.context = context
        self.initialized_models = initialized_models or []

    def get_instance_of(self, model_class: Type[SpModelABC]) -> Optional[SpModelABC]:
        """
        Retrieves an instance of a specific model class from the context.

        Args:
            model_class (Type[SpModelABC]): The class of the model to look up.

        Returns:
            Optional[SpModelABC]: The instance of the specified model class if found,
            otherwise None.
        """
        for model in self.initialized_models:
            # case A: model is already an instance
            if isinstance(model, model_class):
                # print(f"Model instance found: {model.__class__.__name__}")
                return model

        return None
