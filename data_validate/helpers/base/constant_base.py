#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing a base class for immutable constants.

This module defines the `ConstantBase` class, which allows attribute assignment
during initialization but prevents modification afterwards, ensuring data integrity
for configuration and constant values.
"""

from typing import Any


class ConstantBase:
    """
    Class base to create immutable constants after initialization.

    Allows attributes to be set only during the initialization phase. Once
    `_finalize_initialization` is called (or logic implies initialization is done),
    attributes become read-only.

    Attributes:
        _initialized (bool): Internal flag to track initialization state.
    """

    def __init__(self) -> None:
        """Initialize the constant base object."""
        self._initialized = False

    def _finalize_initialization(self) -> None:
        """Mark the object as fully initialized, preventing further attribute changes."""
        self._initialized = True

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set an attribute value.

        Allows setting attributes only if the object is not yet initialized.
        Raises an `AttributeError` if attempting to change attributes after initialization.

        Args:
            name (str): The name of the attribute.
            value (Any): The value of the attribute.

        Raises:
            AttributeError: If attempting to reassign a constant after initialization.
        """
        # Allow setting during initialization
        if not hasattr(self, "_initialized") or not self._initialized:
            super().__setattr__(name, value)
            return

        # After initialization, do not allow reassignment of constants
        if hasattr(self, name) and name != "_initialized":
            raise AttributeError(f"Cannot reassign constant {name}")
        super().__setattr__(name, value)

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Returns:
            str: String representation including all public attributes.
        """
        attrs = []
        for attr in dir(self):
            if not attr.startswith("_"):
                attrs.append(f"{attr}={getattr(self, attr)}")
        class_name = self.__class__.__name__
        return f"{class_name}({', '.join(attrs)})"
