# Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Comprehensive unit tests for ConstantBase class.

This module provides complete test coverage for the ConstantBase class,
testing initialization, attribute setting protection, and string representation.
"""

from typing import Any, Dict, List, Tuple
import pytest

from data_validate.helpers.base.constant_base import ConstantBase


class TestConstantBase:
    """Test suite for ConstantBase core functionality."""

    def test_init_creates_uninitialized_instance(self) -> None:
        """Test that __init__ creates instance with _initialized set to False."""
        constant = ConstantBase()
        
        assert hasattr(constant, "_initialized")
        assert constant._initialized is False

    def test_finalize_initialization_sets_initialized_flag(self) -> None:
        """Test that _finalize_initialization sets _initialized to True."""
        constant = ConstantBase()
        assert constant._initialized is False
        
        constant._finalize_initialization()
        
        assert constant._initialized is True

    def test_attribute_setting_before_initialization(self) -> None:
        """Test that attributes can be set before finalization."""
        constant = ConstantBase()
        
        # Should allow setting attributes before finalization
        constant.TEST_CONSTANT = "test_value"
        constant.NUMERIC_CONSTANT = 42
        constant.BOOLEAN_CONSTANT = True
        
        assert constant.TEST_CONSTANT == "test_value"
        assert constant.NUMERIC_CONSTANT == 42
        assert constant.BOOLEAN_CONSTANT is True

    def test_attribute_setting_after_initialization(self) -> None:
        """Test that new attributes can be set after finalization."""
        constant = ConstantBase()
        constant._finalize_initialization()
        
        # Should allow setting new attributes after finalization
        constant.NEW_CONSTANT = "new_value"
        
        assert constant.NEW_CONSTANT == "new_value"

    def test_attribute_reassignment_protection_after_initialization(self) -> None:
        """Test that existing attributes cannot be reassigned after finalization."""
        constant = ConstantBase()
        constant.PROTECTED_CONSTANT = "original_value"
        constant._finalize_initialization()
        
        # Should raise AttributeError when trying to reassign
        with pytest.raises(AttributeError, match="Cannot reassign constant PROTECTED_CONSTANT"):
            constant.PROTECTED_CONSTANT = "new_value"
        
        # Original value should remain unchanged
        assert constant.PROTECTED_CONSTANT == "original_value"

    def test_private_attribute_setting_behavior(self) -> None:
        """Test behavior with private attributes (starting with underscore)."""
        constant = ConstantBase()
        constant._finalize_initialization()
        
        # Should allow setting private attributes
        constant._private_attr = "private_value"
        
        assert constant._private_attr == "private_value"

    def test_initialized_flag_reassignment_allowed(self) -> None:
        """Test that _initialized flag can be reassigned (special behavior)."""
        constant = ConstantBase()
        constant._finalize_initialization()
        
        # _initialized should be allowed to be reassigned (special case)
        constant._initialized = False
        assert constant._initialized is False
        
        # Can be set back to True
        constant._initialized = True
        assert constant._initialized is True

    def test_setattr_without_initialized_attribute(self) -> None:
        """Test __setattr__ behavior when _initialized attribute doesn't exist yet."""
        constant = ConstantBase()
        
        # Remove _initialized to test the hasattr check
        delattr(constant, "_initialized")
        
        # Should allow setting attributes when _initialized doesn't exist
        constant.TEST_ATTR = "test_value"
        
        assert constant.TEST_ATTR == "test_value"

    def test_repr_with_no_public_attributes(self) -> None:
        """Test __repr__ with no public attributes."""
        constant = ConstantBase()
        
        result = repr(constant)
        
        assert result == "ConstantBase()"

    def test_repr_with_single_attribute(self) -> None:
        """Test __repr__ with single public attribute."""
        constant = ConstantBase()
        constant.SINGLE_ATTR = "single_value"
        
        result = repr(constant)
        
        assert result == "ConstantBase(SINGLE_ATTR=single_value)"

    def test_repr_with_multiple_attributes(self) -> None:
        """Test __repr__ with multiple public attributes."""
        constant = ConstantBase()
        constant.ATTR_A = "value_a"
        constant.ATTR_B = 100
        constant.ATTR_C = True
        
        result = repr(constant)
        
        # Check that all attributes are present (order may vary)
        assert "ConstantBase(" in result
        assert "ATTR_A=value_a" in result
        assert "ATTR_B=100" in result
        assert "ATTR_C=True" in result
        assert result.endswith(")")

    def test_repr_excludes_private_attributes(self) -> None:
        """Test that __repr__ excludes private attributes."""
        constant = ConstantBase()
        constant.PUBLIC_ATTR = "public"
        constant._private_attr = "private"
        constant.__dunder_attr = "dunder"
        
        result = repr(constant)
        
        assert "PUBLIC_ATTR=public" in result
        assert "_private_attr" not in result
        assert "__dunder_attr" not in result


class TestConstantBaseDataDrivenTests:
    """Data-driven tests for ConstantBase using pytest parameterization."""

    @pytest.mark.parametrize(
        "attribute_name,attribute_value,expected_type",
        [
            ("STRING_CONST", "test_string", str),
            ("INTEGER_CONST", 42, int),
            ("FLOAT_CONST", 3.14, float),
            ("BOOLEAN_CONST", True, bool),
            ("LIST_CONST", [1, 2, 3], list),
            ("DICT_CONST", {"key": "value"}, dict),
            ("NONE_CONST", None, type(None)),
        ],
    )
    def test_attribute_setting_with_various_types(
        self, attribute_name: str, attribute_value: Any, expected_type: type
    ) -> None:
        """Test setting attributes with various data types."""
        constant = ConstantBase()
        
        setattr(constant, attribute_name, attribute_value)
        
        assert hasattr(constant, attribute_name)
        assert getattr(constant, attribute_name) == attribute_value
        assert isinstance(getattr(constant, attribute_name), expected_type)

    @pytest.mark.parametrize(
        "attributes_dict,expected_repr_parts",
        [
            (
                {"CONST_A": "value_a"},
                ["ConstantBase(", "CONST_A=value_a", ")"]
            ),
            (
                {"CONST_X": 999, "CONST_Y": "text"},
                ["ConstantBase(", "CONST_X=999", "CONST_Y=text", ")"]
            ),
            (
                {"BOOL_CONST": False, "NUM_CONST": 0, "STR_CONST": "empty"},
                ["ConstantBase(", "BOOL_CONST=False", "NUM_CONST=0", "STR_CONST=empty", ")"]
            ),
        ],
    )
    def test_repr_with_various_attribute_combinations(
        self, attributes_dict: Dict[str, Any], expected_repr_parts: List[str]
    ) -> None:
        """Test __repr__ with various attribute combinations."""
        constant = ConstantBase()
        
        # Set all attributes
        for attr_name, attr_value in attributes_dict.items():
            setattr(constant, attr_name, attr_value)
        
        result = repr(constant)
        
        # Check that all expected parts are present
        for part in expected_repr_parts:
            assert part in result

    @pytest.mark.parametrize(
        "initial_value,reassignment_value",
        [
            ("original_string", "new_string"),
            (100, 200),
            (True, False),
            ([1, 2], [3, 4]),
            ({"a": 1}, {"b": 2}),
            (None, "not_none"),
        ],
    )
    def test_reassignment_protection_with_various_types(
        self, initial_value: Any, reassignment_value: Any
    ) -> None:
        """Test reassignment protection with various data types."""
        constant = ConstantBase()
        constant.PROTECTED_ATTR = initial_value
        constant._finalize_initialization()
        
        # Should raise AttributeError for reassignment
        with pytest.raises(AttributeError, match="Cannot reassign constant PROTECTED_ATTR"):
            constant.PROTECTED_ATTR = reassignment_value
        
        # Original value should remain unchanged
        assert constant.PROTECTED_ATTR == initial_value


class TestConstantBaseEdgeCases:
    """Edge cases and boundary condition tests for ConstantBase."""

    def test_multiple_finalization_calls(self) -> None:
        """Test that multiple calls to _finalize_initialization are safe."""
        constant = ConstantBase()
        
        # Multiple calls should not cause issues
        constant._finalize_initialization()
        constant._finalize_initialization()
        constant._finalize_initialization()
        
        assert constant._initialized is True

    def test_attribute_with_special_characters(self) -> None:
        """Test attributes with special characters in names."""
        constant = ConstantBase()
        
        # These are valid Python attribute names
        constant.ATTR_WITH_UNDERSCORE = "underscore_value"
        constant.ATTR123 = "numeric_suffix"
        
        assert constant.ATTR_WITH_UNDERSCORE == "underscore_value"
        assert constant.ATTR123 == "numeric_suffix"

    def test_repr_with_very_long_attribute_values(self) -> None:
        """Test __repr__ with very long attribute values."""
        constant = ConstantBase()
        long_string = "a" * 1000
        constant.LONG_ATTR = long_string
        
        result = repr(constant)
        
        assert f"LONG_ATTR={long_string}" in result

    def test_repr_with_complex_nested_structures(self) -> None:
        """Test __repr__ with complex nested data structures."""
        constant = ConstantBase()
        complex_value = {
            "nested": {"deep": [1, 2, {"inner": "value"}]},
            "list": [{"dict": "in_list"}]
        }
        constant.COMPLEX_ATTR = complex_value
        
        result = repr(constant)
        
        assert "COMPLEX_ATTR=" in result
        assert str(complex_value) in result

    def test_attribute_deletion_not_prevented(self) -> None:
        """Test that attribute deletion is not prevented by ConstantBase."""
        constant = ConstantBase()
        constant.DELETABLE_ATTR = "delete_me"
        constant._finalize_initialization()
        
        # Deletion should work (ConstantBase only prevents reassignment)
        delattr(constant, "DELETABLE_ATTR")
        
        assert not hasattr(constant, "DELETABLE_ATTR")

    def test_inherited_attributes_behavior(self) -> None:
        """Test behavior with inherited attributes from parent classes."""
        
        class ChildConstant(ConstantBase):
            CLASS_ATTR = "class_level"
        
        child = ChildConstant()
        child.INSTANCE_ATTR = "instance_level"
        child._finalize_initialization()
        
        # Should include both class and instance attributes in repr
        result = repr(child)
        assert "ChildConstant(" in result
        assert "CLASS_ATTR=class_level" in result
        assert "INSTANCE_ATTR=instance_level" in result


class TestConstantBaseIntegration:
    """Integration tests for ConstantBase complete workflows."""

    def test_complete_constant_definition_workflow(self) -> None:
        """Test complete workflow of defining constants."""
        constant = ConstantBase()
        
        # Phase 1: Define constants before finalization
        constant.APP_NAME = "DataValidate"
        constant.VERSION = "1.0.0"
        constant.DEBUG_MODE = False
        constant.MAX_RETRIES = 3
        
        # Phase 2: Finalize to protect constants
        constant._finalize_initialization()
        
        # Phase 3: Verify constants are accessible
        assert constant.APP_NAME == "DataValidate"
        assert constant.VERSION == "1.0.0"
        assert constant.DEBUG_MODE is False
        assert constant.MAX_RETRIES == 3
        
        # Phase 4: Verify protection works
        with pytest.raises(AttributeError):
            constant.APP_NAME = "NewName"
        
        # Phase 5: Verify new attributes can still be added
        constant.NEW_SETTING = "added_later"
        assert constant.NEW_SETTING == "added_later"

    def test_multiple_instances_independence(self) -> None:
        """Test that multiple ConstantBase instances are independent."""
        constant1 = ConstantBase()
        constant2 = ConstantBase()
        
        # Set different attributes on each instance
        constant1.CONST_A = "value_a"
        constant2.CONST_B = "value_b"
        
        constant1._finalize_initialization()
        constant2._finalize_initialization()
        
        # Verify independence
        assert hasattr(constant1, "CONST_A")
        assert not hasattr(constant1, "CONST_B")
        assert hasattr(constant2, "CONST_B")
        assert not hasattr(constant2, "CONST_A")
        
        # Verify separate protection
        with pytest.raises(AttributeError):
            constant1.CONST_A = "new_value"
        
        with pytest.raises(AttributeError):
            constant2.CONST_B = "new_value"

    def test_practical_usage_pattern(self) -> None:
        """Test practical usage pattern similar to real-world usage."""
        
        class DatabaseConfig(ConstantBase):
            def __init__(self) -> None:
                super().__init__()
                self.HOST = "localhost"
                self.PORT = 5432
                self.DATABASE_NAME = "production_db"
                self.TIMEOUT_SECONDS = 30
                self.MAX_CONNECTIONS = 100
                self._finalize_initialization()
        
        config = DatabaseConfig()
        
        # Verify all constants are set
        assert config.HOST == "localhost"
        assert config.PORT == 5432
        assert config.DATABASE_NAME == "production_db"
        assert config.TIMEOUT_SECONDS == 30
        assert config.MAX_CONNECTIONS == 100
        
        # Verify protection
        with pytest.raises(AttributeError):
            config.HOST = "remote_host"
        
        # Verify repr
        result = repr(config)
        assert "DatabaseConfig(" in result
        assert "HOST=localhost" in result
        assert "PORT=5432" in result
