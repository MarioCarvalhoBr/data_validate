#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
class ConstantBase:
    """Class base to create immutable constants after initialization"""

    def __init__(self):
        self._initialized = False

    def _finalize_initialization(self):
        self._initialized = True

    def __setattr__(self, name, value):
        # Allow setting during initialization
        if not hasattr(self, "_initialized") or not self._initialized:
            super().__setattr__(name, value)
            return

        # After initialization, do not allow reassignment of constants
        if hasattr(self, name) and name != "_initialized":
            raise AttributeError(f"Cannot reassign constant {name}")
        super().__setattr__(name, value)

    def __repr__(self):
        attrs = []
        for attr in dir(self):
            if not attr.startswith("_"):
                attrs.append(f"{attr}={getattr(self, attr)}")
        class_name = self.__class__.__name__
        return f"{class_name}({', '.join(attrs)})"
