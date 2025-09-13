# Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Comprehensive unit tests for data_args module.

This module provides complete test coverage for all classes in data_args.py:
- DataModelABC (abstract base class)
- DataFile (file-related arguments)
- DataAction (action-related arguments) 
- DataReport (report-related arguments)
- DataArgs (main argument parsing class)
"""

import argparse
import os
import tempfile
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import Mock, patch, MagicMock
import pytest

from data_validate.helpers.base.data_args import (
    DataModelABC,
    DataFile, 
    DataAction,
    DataReport,
    DataArgs,
)


class TestDataModelABC:
    """Test suite for DataModelABC abstract base class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that DataModelABC cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DataModelABC()

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        """Test that concrete subclass implementing abstract methods can be instantiated."""
        
        class ConcreteDataModel(DataModelABC):
            def _validate_arguments(self) -> None:
                pass
        
        # Should not raise any exception
        instance = ConcreteDataModel()
        assert isinstance(instance, DataModelABC)

    def test_subclass_without_implementation_raises_error(self) -> None:
        """Test that subclass without implementing abstract method raises error."""
        
        class IncompleteDataModel(DataModelABC):
            pass
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteDataModel()

    def test_abstract_method_signature(self) -> None:
        """Test that abstract method has correct signature."""
        
        class TestDataModel(DataModelABC):
            def _validate_arguments(self) -> None:
                return "validated"
        
        instance = TestDataModel()
        result = instance._validate_arguments()
        assert result == "validated"


class TestDataFile:
    """Test suite for DataFile class."""

    @pytest.fixture
    def temp_input_dir(self) -> Generator[str, None, None]:
        """Create temporary input directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def temp_output_dir(self) -> Generator[str, None, None]:
        """Create temporary output directory path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output")
            yield output_path

    def test_init_with_valid_paths(self, temp_input_dir: str, temp_output_dir: str) -> None:
        """Test DataFile initialization with valid paths."""
        data_file = DataFile(
            input_folder=temp_input_dir,
            output_folder=temp_output_dir,
            locale="pt_BR"
        )
        
        assert data_file.input_folder == temp_input_dir
        assert data_file.output_folder == temp_output_dir
        assert data_file.locale == "pt_BR"

    def test_init_with_invalid_input_folder(self, temp_output_dir: str) -> None:
        """Test DataFile initialization with non-existent input folder."""
        invalid_input = "/path/that/does/not/exist"
        
        with pytest.raises(ValueError, match="Input folder does not exist"):
            DataFile(
                input_folder=invalid_input,
                output_folder=temp_output_dir,
                locale="en_US"
            )

    def test_init_with_invalid_output_folder_extension(self, temp_input_dir: str) -> None:
        """Test DataFile initialization with output folder having file extension."""
        invalid_output = "/path/to/output.txt"
        
        with pytest.raises(ValueError, match="Output folder name is invalid"):
            DataFile(
                input_folder=temp_input_dir,
                output_folder=invalid_output,
                locale="pt_BR"
            )

    def test_init_with_output_folder_containing_dots(self, temp_input_dir: str) -> None:
        """Test DataFile initialization with output folder containing dots."""
        invalid_output = "/path/to/out.put"
        
        with pytest.raises(ValueError, match="Output folder name is invalid"):
            DataFile(
                input_folder=temp_input_dir,
                output_folder=invalid_output,
                locale="pt_BR"
            )

    def test_validate_arguments_called_during_init(self, temp_input_dir: str) -> None:
        """Test that _validate_arguments is called during initialization."""
        with patch.object(DataFile, '_validate_arguments') as mock_validate:
            DataFile(
                input_folder=temp_input_dir,
                output_folder="/valid/output",
                locale="pt_BR"
            )
            mock_validate.assert_called_once()

    def test_run_method_calls_validate(self, temp_input_dir: str) -> None:
        """Test that run method calls _validate_arguments."""
        data_file = DataFile.__new__(DataFile)  # Create without calling __init__
        data_file.input_folder = temp_input_dir
        data_file.output_folder = "/valid/output"
        data_file.locale = "pt_BR"
        
        with patch.object(data_file, '_validate_arguments') as mock_validate:
            data_file.run()
            mock_validate.assert_called_once()


class TestDataAction:
    """Test suite for DataAction class."""

    def test_init_with_all_boolean_values(self) -> None:
        """Test DataAction initialization with all boolean values."""
        data_action = DataAction(
            no_spellchecker=True,
            no_warning_titles_length=False,
            no_time=True,
            no_version=False,
            debug=True
        )
        
        assert data_action.no_spellchecker is True
        assert data_action.no_warning_titles_length is False
        assert data_action.no_time is True
        assert data_action.no_version is False
        assert data_action.debug is True

    def test_init_with_none_values_raises_error(self) -> None:
        """Test DataAction initialization with None values raises validation error."""
        with pytest.raises(ValueError, match="no_spellchecker must be a boolean value"):
            DataAction(
                no_spellchecker=None,
                no_warning_titles_length=False,
                no_time=False,
                no_version=False,
                debug=False
            )

    def test_validate_arguments_with_invalid_no_spellchecker(self) -> None:
        """Test validation error when no_spellchecker is not boolean."""
        with pytest.raises(ValueError, match="no_spellchecker must be a boolean value"):
            DataAction(
                no_spellchecker="invalid",
                no_warning_titles_length=True,
                no_time=True,
                no_version=True,
                debug=True
            )

    def test_validate_arguments_with_invalid_no_warning_titles_length(self) -> None:
        """Test validation error when no_warning_titles_length is not boolean."""
        with pytest.raises(ValueError, match="no_warning_titles_length must be a boolean value"):
            DataAction(
                no_spellchecker=True,
                no_warning_titles_length=123,
                no_time=True,
                no_version=True,
                debug=True
            )

    def test_validate_arguments_with_invalid_no_time(self) -> None:
        """Test validation error when no_time is not boolean."""
        with pytest.raises(ValueError, match="no_time must be a boolean value"):
            DataAction(
                no_spellchecker=True,
                no_warning_titles_length=True,
                no_time=[],
                no_version=True,
                debug=True
            )

    def test_validate_arguments_with_invalid_no_version(self) -> None:
        """Test validation error when no_version is not boolean."""
        with pytest.raises(ValueError, match="no_version must be a boolean value"):
            DataAction(
                no_spellchecker=True,
                no_warning_titles_length=True,
                no_time=True,
                no_version={},
                debug=True
            )

    def test_validate_arguments_with_invalid_debug(self) -> None:
        """Test validation error when debug is not boolean."""
        with pytest.raises(ValueError, match="debug must be a boolean value"):
            DataAction(
                no_spellchecker=True,
                no_warning_titles_length=True,
                no_time=True,
                no_version=True,
                debug=1.5
            )

    def test_run_method_calls_validate(self) -> None:
        """Test that run method calls _validate_arguments."""
        data_action = DataAction.__new__(DataAction)  # Create without calling __init__
        data_action.no_spellchecker = True
        data_action.no_warning_titles_length = False
        data_action.no_time = True
        data_action.no_version = False
        data_action.debug = True
        
        with patch.object(data_action, '_validate_arguments') as mock_validate:
            data_action.run()
            mock_validate.assert_called_once()


class TestDataReport:
    """Test suite for DataReport class."""

    def test_init_with_all_string_values(self) -> None:
        """Test DataReport initialization with all string values."""
        data_report = DataReport(
            sector="Agricultura",
            protocol="v1.0",
            user="test_user",
            file="test_file.xlsx"
        )
        
        assert data_report.sector == "Agricultura"
        assert data_report.protocol == "v1.0"
        assert data_report.user == "test_user"
        assert data_report.file == "test_file.xlsx"

    def test_init_with_none_values(self) -> None:
        """Test DataReport initialization with None values (allowed)."""
        data_report = DataReport(
            sector=None,
            protocol=None,
            user=None,
            file=None
        )
        
        assert data_report.sector is None
        assert data_report.protocol is None
        assert data_report.user is None
        assert data_report.file is None

    def test_init_with_mixed_values(self) -> None:
        """Test DataReport initialization with mixed values."""
        data_report = DataReport(
            sector="Saúde",
            protocol=None,
            user="admin",
            file=None
        )
        
        assert data_report.sector == "Saúde"
        assert data_report.protocol is None
        assert data_report.user == "admin"
        assert data_report.file is None

    def test_validate_arguments_does_nothing(self) -> None:
        """Test that _validate_arguments method exists but does nothing."""
        data_report = DataReport(
            sector="Test",
            protocol="Test", 
            user="Test",
            file="Test"
        )
        
        # Should not raise any exception
        result = data_report._validate_arguments()
        assert result is None

    def test_run_method_calls_validate(self) -> None:
        """Test that run method calls _validate_arguments."""
        data_report = DataReport.__new__(DataReport)  # Create without calling __init__
        data_report.sector = "Test"
        data_report.protocol = "Test"
        data_report.user = "Test" 
        data_report.file = "Test"
        
        with patch.object(data_report, '_validate_arguments') as mock_validate:
            data_report.run()
            mock_validate.assert_called_once()


class TestDataArgs:
    """Test suite for DataArgs main class."""

    @pytest.fixture
    def temp_input_dir(self) -> Generator[str, None, None]:
        """Create temporary input directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_language_manager(self) -> Mock:
        """Mock LanguageManager for testing."""
        return Mock()

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_init_with_mocked_args(
        self, 
        mock_parse_args: Mock, 
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test DataArgs initialization with mocked command line arguments."""
        # Setup mock
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = "pt_BR"
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = False
        mock_args.no_time = False
        mock_args.no_version = False
        mock_args.debug = False
        mock_args.sector = "Test"
        mock_args.protocol = "v1.0"
        mock_args.user = "test_user"
        mock_args.file = "test.xlsx"
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs(allow_abbrev=True)
        
        assert data_args.allow_abbrev is True
        assert data_args.data_file is not None
        assert data_args.data_action is not None
        assert data_args.data_report is not None

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_create_parser_method(self, mock_parse_args: Mock, mock_lm_class: Mock) -> None:
        """Test _create_parser method creates ArgumentParser correctly."""
        mock_lm_class.return_value = Mock()
        
        # Mock parse_args to avoid actual parsing and validation
        mock_args = Mock()
        mock_args.input_folder = "/tmp"  # Use existing directory
        mock_args.output_folder = "/test/output"
        mock_args.locale = "pt_BR"
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = False
        mock_args.no_time = False
        mock_args.no_version = False
        mock_args.debug = False
        mock_args.sector = None
        mock_args.protocol = None
        mock_args.user = None
        mock_args.file = None
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs(allow_abbrev=False)
        parser = data_args._create_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.allow_abbrev is False

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_get_dict_args_method(
        self, 
        mock_parse_args: Mock, 
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test get_dict_args method returns correct dictionary."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = "en_US"
        mock_args.no_spellchecker = True
        mock_args.no_warning_titles_length = True
        mock_args.no_time = True
        mock_args.no_version = True
        mock_args.debug = True
        mock_args.sector = "Educação"
        mock_args.protocol = "v2.0"
        mock_args.user = "admin"
        mock_args.file = "data.xlsx"
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs()
        result_dict = data_args.get_dict_args()
        
        expected_dict = {
            "input_folder": temp_input_dir,
            "output_folder": "/test/output",
            "locale": "en_US",
            "no_spellchecker": True,
            "no_warning_titles_length": True,
            "no_time": True,
            "no_version": True,
            "debug": True,
            "sector": "Educação",
            "protocol": "v2.0",
            "user": "admin",
            "file": "data.xlsx",
        }
        
        assert result_dict == expected_dict

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_str_method(
        self, 
        mock_parse_args: Mock, 
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test __str__ method returns correct string representation."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = "pt_BR"
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = True
        mock_args.no_time = False
        mock_args.no_version = True
        mock_args.debug = False
        mock_args.sector = "Saúde"
        mock_args.protocol = "v1.5"
        mock_args.user = "doctor"
        mock_args.file = "medical.xlsx"
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs()
        str_result = str(data_args)
        
        expected_parts = [
            f"DataArgs(input_folder={temp_input_dir}",
            "output_folder=/test/output",
            "locale=pt_BR",
            "no_spellchecker=False",
            "no_warning_titles_length=True",
            "no_time=False",
            "no_version=True",
            "debug=False",
            "sector=Saúde",
            "protocol=v1.5",
            "user=doctor",
            "file=medical.xlsx)"
        ]
        
        for part in expected_parts:
            assert part in str_result

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    def test_run_method_calls_parser(self, mock_lm_class: Mock) -> None:
        """Test that run method creates parser and parses arguments."""
        mock_lm_class.return_value = Mock()
        
        with patch.object(DataArgs, '_create_parser') as mock_create_parser:
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.input_folder = "/test/input"
            mock_args.output_folder = "/test/output" 
            mock_args.locale = "pt_BR"
            mock_args.no_spellchecker = False
            mock_args.no_warning_titles_length = False
            mock_args.no_time = False
            mock_args.no_version = False
            mock_args.debug = False
            mock_args.sector = None
            mock_args.protocol = None
            mock_args.user = None
            mock_args.file = None
            
            mock_parser.parse_args.return_value = mock_args
            mock_create_parser.return_value = mock_parser
            
            with patch.object(DataFile, '__init__', return_value=None):
                with patch.object(DataAction, '__init__', return_value=None):
                    with patch.object(DataReport, '__init__', return_value=None):
                        data_args = DataArgs.__new__(DataArgs)
                        data_args.lm = Mock()
                        data_args.allow_abbrev = True
                        data_args.run()
            
            mock_create_parser.assert_called_once()
            mock_parser.parse_args.assert_called_once()


class TestDataArgsDataDrivenTests:
    """Data-driven tests for DataArgs using pytest parameterization."""

    @pytest.fixture
    def temp_input_dir(self) -> Generator[str, None, None]:
        """Create temporary input directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.mark.parametrize(
        "allow_abbrev,expected_abbrev",
        [
            (True, True),
            (False, False),
        ],
    )
    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_allow_abbrev_parameter(
        self, 
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        allow_abbrev: bool, 
        expected_abbrev: bool,
        temp_input_dir: str
    ) -> None:
        """Test DataArgs with different allow_abbrev settings."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = "pt_BR"
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = False
        mock_args.no_time = False
        mock_args.no_version = False
        mock_args.debug = False
        mock_args.sector = None
        mock_args.protocol = None
        mock_args.user = None
        mock_args.file = None
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs(allow_abbrev=allow_abbrev)
        
        assert data_args.allow_abbrev == expected_abbrev

    @pytest.mark.parametrize(
        "locale_value,expected_locale",
        [
            ("pt_BR", "pt_BR"),
            ("en_US", "en_US"),
        ],
    )
    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_locale_parameter_variations(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        locale_value: str,
        expected_locale: str,
        temp_input_dir: str
    ) -> None:
        """Test DataArgs with different locale values."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = locale_value
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = False
        mock_args.no_time = False
        mock_args.no_version = False
        mock_args.debug = False
        mock_args.sector = None
        mock_args.protocol = None
        mock_args.user = None
        mock_args.file = None
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs()
        
        assert data_args.data_file.locale == expected_locale

    @pytest.mark.parametrize(
        "boolean_flags,expected_values",
        [
            (
                {"no_spellchecker": True, "no_warning_titles_length": False, "no_time": True, "no_version": False, "debug": True},
                {"no_spellchecker": True, "no_warning_titles_length": False, "no_time": True, "no_version": False, "debug": True}
            ),
            (
                {"no_spellchecker": False, "no_warning_titles_length": True, "no_time": False, "no_version": True, "debug": False},
                {"no_spellchecker": False, "no_warning_titles_length": True, "no_time": False, "no_version": True, "debug": False}
            ),
            (
                {"no_spellchecker": True, "no_warning_titles_length": True, "no_time": True, "no_version": True, "debug": True},
                {"no_spellchecker": True, "no_warning_titles_length": True, "no_time": True, "no_version": True, "debug": True}
            ),
        ],
    )
    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_boolean_flags_combinations(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        boolean_flags: Dict[str, bool],
        expected_values: Dict[str, bool],
        temp_input_dir: str
    ) -> None:
        """Test DataArgs with different combinations of boolean flags."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/test/output"
        mock_args.locale = "pt_BR"
        mock_args.no_spellchecker = boolean_flags["no_spellchecker"]
        mock_args.no_warning_titles_length = boolean_flags["no_warning_titles_length"]
        mock_args.no_time = boolean_flags["no_time"]
        mock_args.no_version = boolean_flags["no_version"]
        mock_args.debug = boolean_flags["debug"]
        mock_args.sector = None
        mock_args.protocol = None
        mock_args.user = None
        mock_args.file = None
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs()
        
        assert data_args.data_action.no_spellchecker == expected_values["no_spellchecker"]
        assert data_args.data_action.no_warning_titles_length == expected_values["no_warning_titles_length"]
        assert data_args.data_action.no_time == expected_values["no_time"]
        assert data_args.data_action.no_version == expected_values["no_version"]
        assert data_args.data_action.debug == expected_values["debug"]


class TestDataArgsEdgeCases:
    """Edge cases and boundary condition tests for DataArgs."""

    @pytest.fixture
    def temp_input_dir(self) -> Generator[str, None, None]:
        """Create temporary input directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_create_parser_with_all_arguments(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test that _create_parser creates parser with all required arguments."""
        mock_lm_class.return_value = Mock()
        mock_parse_args.return_value = Mock()
        
        data_args = DataArgs.__new__(DataArgs)
        data_args.lm = Mock()
        data_args.allow_abbrev = True
        
        parser = data_args._create_parser()
        
        # Check that parser has all expected arguments
        action_names = [action.dest for action in parser._actions if action.dest != 'help']
        
        expected_args = [
            'input_folder', 'output_folder', 'locale',
            'no_spellchecker', 'no_warning_titles_length', 'no_time', 'no_version', 'debug',
            'sector', 'protocol', 'user', 'file'
        ]
        
        for arg in expected_args:
            assert arg in action_names

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_parser_description_and_settings(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock
    ) -> None:
        """Test parser description and allow_abbrev setting."""
        mock_lm_class.return_value = Mock()
        mock_parse_args.return_value = Mock()
        
        data_args = DataArgs.__new__(DataArgs)
        data_args.lm = Mock()
        data_args.allow_abbrev = False
        
        parser = data_args._create_parser()
        
        assert "Adapta Parser" in parser.description
        assert parser.allow_abbrev is False

    @pytest.mark.parametrize(
        "invalid_type_value,expected_error",
        [
            ("string_value", "must be a boolean value"),
            (123, "must be a boolean value"),
            ([], "must be a boolean value"),
            ({}, "must be a boolean value"),
            (1.5, "must be a boolean value"),
        ],
    )
    def test_data_action_invalid_type_validation(
        self, 
        invalid_type_value: Any, 
        expected_error: str
    ) -> None:
        """Test DataAction validation with various invalid types."""
        with pytest.raises(ValueError, match=expected_error):
            DataAction(
                no_spellchecker=invalid_type_value,
                no_warning_titles_length=True,
                no_time=True,
                no_version=True,
                debug=True
            )

    @pytest.mark.parametrize(
        "invalid_folder_name",
        [
            "/path/to/file.txt",
            "/path/to/file.xlsx", 
            "/path/to/config.json",
            "/path/to/data.csv",
            "/path/to/script.py",
        ],
    )
    def test_data_file_invalid_output_folder_names(
        self, 
        invalid_folder_name: str,
        temp_input_dir: str
    ) -> None:
        """Test DataFile validation with various invalid output folder names."""
        with pytest.raises(ValueError, match="Output folder name is invalid"):
            DataFile(
                input_folder=temp_input_dir,
                output_folder=invalid_folder_name,
                locale="pt_BR"
            )


class TestDataArgsIntegration:
    """Integration tests for DataArgs complete workflows."""

    @pytest.fixture
    def temp_input_dir(self) -> Generator[str, None, None]:
        """Create temporary input directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_complete_workflow_with_all_parameters(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test complete workflow with all parameters set."""
        # Setup mocks
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "/complete/output"
        mock_args.locale = "en_US"
        mock_args.no_spellchecker = True
        mock_args.no_warning_titles_length = True
        mock_args.no_time = False
        mock_args.no_version = True
        mock_args.debug = False
        mock_args.sector = "Agricultura"
        mock_args.protocol = "v3.0"
        mock_args.user = "farmer"
        mock_args.file = "crops.xlsx"
        mock_parse_args.return_value = mock_args
        
        # Test complete initialization
        data_args = DataArgs(allow_abbrev=False)
        
        # Verify all components initialized correctly
        assert data_args.allow_abbrev is False
        assert isinstance(data_args.lm, Mock)
        
        # Verify DataFile
        assert data_args.data_file.input_folder == temp_input_dir
        assert data_args.data_file.output_folder == "/complete/output"
        assert data_args.data_file.locale == "en_US"
        
        # Verify DataAction
        assert data_args.data_action.no_spellchecker is True
        assert data_args.data_action.no_warning_titles_length is True
        assert data_args.data_action.no_time is False
        assert data_args.data_action.no_version is True
        assert data_args.data_action.debug is False
        
        # Verify DataReport
        assert data_args.data_report.sector == "Agricultura"
        assert data_args.data_report.protocol == "v3.0"
        assert data_args.data_report.user == "farmer"
        assert data_args.data_report.file == "crops.xlsx"
        
        # Test dictionary output
        result_dict = data_args.get_dict_args()
        assert len(result_dict) == 12
        assert result_dict["input_folder"] == temp_input_dir
        assert result_dict["sector"] == "Agricultura"
        
        # Test string representation
        str_repr = str(data_args)
        assert "DataArgs(" in str_repr
        assert "Agricultura" in str_repr
        assert "crops.xlsx" in str_repr

    @patch('data_validate.helpers.base.data_args.LanguageManager')
    @patch('argparse.ArgumentParser.parse_args')
    def test_workflow_with_minimal_parameters(
        self,
        mock_parse_args: Mock,
        mock_lm_class: Mock,
        temp_input_dir: str
    ) -> None:
        """Test workflow with minimal required parameters."""
        # Setup mocks  
        mock_lm_class.return_value = Mock()
        mock_args = Mock()
        mock_args.input_folder = temp_input_dir
        mock_args.output_folder = "output_data/"  # Default value
        mock_args.locale = "pt_BR"  # Default value
        mock_args.no_spellchecker = False
        mock_args.no_warning_titles_length = False
        mock_args.no_time = False
        mock_args.no_version = False
        mock_args.debug = False
        mock_args.sector = None
        mock_args.protocol = None
        mock_args.user = None
        mock_args.file = None
        mock_parse_args.return_value = mock_args
        
        data_args = DataArgs()
        
        # Verify defaults are set correctly
        assert data_args.data_file.output_folder == "output_data/"
        assert data_args.data_file.locale == "pt_BR"
        assert data_args.data_action.debug is False
        assert data_args.data_report.sector is None
        
        # Test with minimal data
        result_dict = data_args.get_dict_args()
        assert result_dict["locale"] == "pt_BR"
        assert result_dict["debug"] is False
        assert result_dict["sector"] is None

    def test_multiple_dataargs_instances_independence(self) -> None:
        """Test that multiple DataArgs instances are independent."""
        with patch('data_validate.helpers.base.data_args.LanguageManager'):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
                with tempfile.TemporaryDirectory() as temp_dir1:
                    with tempfile.TemporaryDirectory() as temp_dir2:
                        # Create two different mock args
                        mock_args1 = Mock()
                        mock_args1.input_folder = temp_dir1  # Use real temp directory
                        mock_args1.output_folder = "/output1"
                        mock_args1.locale = "pt_BR"
                        mock_args1.no_spellchecker = True
                        mock_args1.no_warning_titles_length = False
                        mock_args1.no_time = True
                        mock_args1.no_version = False
                        mock_args1.debug = True
                        mock_args1.sector = "Sector1"
                        mock_args1.protocol = "v1.0"
                        mock_args1.user = "user1"
                        mock_args1.file = "file1.xlsx"
                        
                        mock_args2 = Mock()
                        mock_args2.input_folder = temp_dir2  # Use real temp directory
                        mock_args2.output_folder = "/output2"
                        mock_args2.locale = "en_US"
                        mock_args2.no_spellchecker = False
                        mock_args2.no_warning_titles_length = True
                        mock_args2.no_time = False
                        mock_args2.no_version = True
                        mock_args2.debug = False
                        mock_args2.sector = "Sector2"
                        mock_args2.protocol = "v2.0"
                        mock_args2.user = "user2"
                        mock_args2.file = "file2.xlsx"
                        
                        # Test first instance
                        mock_parse_args.return_value = mock_args1
                        data_args1 = DataArgs(allow_abbrev=True)
                        
                        # Test second instance
                        mock_parse_args.return_value = mock_args2
                        data_args2 = DataArgs(allow_abbrev=False)
                        
                        # Verify independence
                        assert data_args1.allow_abbrev is True
                        assert data_args2.allow_abbrev is False
                        
                        assert data_args1.data_file.locale == "pt_BR"
                        assert data_args2.data_file.locale == "en_US"
                        
                        assert data_args1.data_action.debug is True
                        assert data_args2.data_action.debug is False
                        
                        assert data_args1.data_report.sector == "Sector1"
                        assert data_args2.data_report.sector == "Sector2"
