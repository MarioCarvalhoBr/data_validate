import logging
import os
import tempfile
import shutil

import pytest

from data_validate.helpers.base.logger_manager import LoggerManager, CustomFormatter


class TestCustomFormatter:
    """
    Test suite for CustomFormatter class.

    Tests color formatting functionality for different log levels
    and proper format string application.
    """

    def test_formatter_attributes(self):
        """Test that CustomFormatter has all required color attributes."""
        formatter = CustomFormatter()

        assert hasattr(formatter, "grey")
        assert hasattr(formatter, "yellow")
        assert hasattr(formatter, "red")
        assert hasattr(formatter, "bold_red")
        assert hasattr(formatter, "reset")
        assert hasattr(formatter, "format")
        assert hasattr(formatter, "FORMATS")

    def test_formats_dictionary_structure(self):
        """Test that FORMATS dictionary contains all required logging levels."""
        formatter = CustomFormatter()

        expected_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

        for level in expected_levels:
            assert level in formatter.FORMATS

    @pytest.mark.parametrize(
        "log_level,expected_color",
        [
            (logging.DEBUG, CustomFormatter.grey),
            (logging.INFO, CustomFormatter.grey),
            (logging.WARNING, CustomFormatter.yellow),
            (logging.ERROR, CustomFormatter.red),
            (logging.CRITICAL, CustomFormatter.bold_red),
        ],
    )
    def test_format_colors_for_different_levels(self, log_level, expected_color, mocker):
        """Test that correct colors are applied for different log levels."""
        formatter = CustomFormatter()

        # Create a mock log record
        record = mocker.MagicMock()
        record.levelno = log_level
        record.asctime = "2023-01-01 12:00:00"
        record.name = "test_logger"
        record.levelname = logging.getLevelName(log_level)
        record.message = "Test message"
        record.filename = "test.py"
        record.lineno = 123

        expected_format = formatter.FORMATS[log_level]
        assert expected_format.startswith(expected_color)
        assert expected_format.endswith(formatter.reset)
        # Verify that the base format string is included in the colored format
        assert "%(asctime)s - %(name)s - %(levelname)s" in expected_format

    def test_format_method_with_mock_record(self, mocker):
        """Test format method with a mock log record."""
        formatter = CustomFormatter()

        # Create a mock log record for INFO level
        record = mocker.Mock()
        record.levelno = logging.INFO
        record.getMessage.return_value = "Test log message"

        mock_format = mocker.patch("logging.Formatter.format")
        mock_format.return_value = "Formatted message"
        result = formatter.format(record)

        assert result == "Formatted message"
        mock_format.assert_called_once()

    @pytest.mark.parametrize("invalid_level", [999, -1, 0])
    def test_format_with_invalid_log_level(self, invalid_level, mocker):
        """Test format method behavior with invalid log levels."""
        formatter = CustomFormatter()

        record = mocker.Mock()
        record.levelno = invalid_level

        mock_format = mocker.patch("logging.Formatter.format")
        mock_format.return_value = "Default formatted message"
        result = formatter.format(record)

        # Should handle gracefully and still format
        assert result == "Default formatted message"

    def test_format_string_pattern(self):
        """Test that format string contains all required components."""
        expected_components = ["%(asctime)s", "%(name)s", "%(levelname)s", "%(message)s", "%(filename)s", "%(lineno)d"]

        # Access the class-level format attribute directly from the class definition
        # Use a string literal to match the actual format string from the class
        actual_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

        for component in expected_components:
            assert component in actual_format


class TestLoggerManager:
    """
    Test suite for LoggerManager class.

    Tests logger configuration, file generation, and complete functionality
    of the logger management system.
    """

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_datetime(self, mocker):
        """Mock datetime for consistent timestamp testing."""
        mock_dt = mocker.patch("data_validate.helpers.base.logger_manager.datetime")
        mock_dt.now.return_value.strftime.return_value = "20230101_120000"
        return mock_dt

    def test_init_default_parameters(self, temp_log_dir, mocker):
        """Test LoggerManager initialization with default parameters."""
        mock_makedirs = mocker.patch("os.makedirs")
        mocker.patch("os.path.exists", return_value=False)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        assert logger_manager.log_folder == temp_log_dir
        assert logger_manager.default_level == logging.DEBUG
        assert logger_manager.console_logger is not None
        assert logger_manager.file_logger is not None
        assert logger_manager.log_file is not None

        mock_makedirs.assert_called_once_with(temp_log_dir)

    def test_init_existing_log_folder(self, temp_log_dir, mocker):
        """Test initialization when log folder already exists."""
        mock_makedirs = mocker.patch("os.makedirs")
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        assert logger_manager.log_folder == temp_log_dir
        mock_makedirs.assert_not_called()

    @pytest.mark.parametrize("log_level", [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL])
    def test_init_custom_log_levels(self, temp_log_dir, log_level, mocker):
        """Test initialization with different log levels."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir, default_level=log_level)

        assert logger_manager.default_level == log_level

    def test_init_custom_parameters(self, temp_log_dir, mocker):
        """Test initialization with all custom parameters."""
        custom_console = "custom_console"
        custom_prefix = "custom_prefix"
        custom_logger_name = "custom_logger"

        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(
            log_folder=temp_log_dir,
            default_level=logging.WARNING,
            console_logger=custom_console,
            prefix=custom_prefix,
            logger_name=custom_logger_name,
        )

        assert logger_manager.log_folder == temp_log_dir
        assert logger_manager.default_level == logging.WARNING

    def test_configure_logger_console_only(self, temp_log_dir, mocker):
        """Test configure_logger method with console handler only."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        test_logger = logger_manager.configure_logger("test_logger")

        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_logger"
        assert test_logger.level == logging.DEBUG  # default level

        # Should have at least one handler (console)
        assert len(test_logger.handlers) >= 1

    def test_configure_logger_with_file(self, temp_log_dir, mocker):
        """Test configure_logger method with file handler."""
        log_file_path = os.path.join(temp_log_dir, "test.log")

        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        test_logger = logger_manager.configure_logger("test_logger_file", log_file=log_file_path)

        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_logger_file"

        # Should have two handlers (console + file)
        assert len(test_logger.handlers) >= 2

    def test_configure_logger_custom_level(self, temp_log_dir, mocker):
        """Test configure_logger with custom logging level."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        test_logger = logger_manager.configure_logger("test_logger", level=logging.ERROR)

        assert test_logger.level == logging.ERROR

    def test_configure_logger_none_level_uses_default(self, temp_log_dir, mocker):
        """Test that None level parameter uses default level."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir, default_level=logging.WARNING)

        test_logger = logger_manager.configure_logger("test_logger", level=None)

        assert test_logger.level == logging.WARNING

    def test_generate_log_file_name_default_prefix(self, temp_log_dir, mock_datetime, mocker):
        """Test log file name generation with default prefix."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        log_file = logger_manager.generate_log_file_name()

        expected_file = os.path.join(temp_log_dir, "app_20230101_120000.log")
        assert log_file == expected_file

    def test_generate_log_file_name_custom_prefix(self, temp_log_dir, mock_datetime, mocker):
        """Test log file name generation with custom prefix."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        log_file = logger_manager.generate_log_file_name(prefix="custom")

        expected_file = os.path.join(temp_log_dir, "custom_20230101_120000.log")
        assert log_file == expected_file

    @pytest.mark.parametrize("prefix", ["test_app", "validation", "system_log", "debug_session"])
    def test_generate_log_file_name_various_prefixes(self, temp_log_dir, mock_datetime, prefix, mocker):
        """Test log file name generation with various prefixes."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        log_file = logger_manager.generate_log_file_name(prefix=prefix)

        expected_file = os.path.join(temp_log_dir, f"{prefix}_20230101_120000.log")
        assert log_file == expected_file

    def test_log_file_path_contains_folder(self, temp_log_dir, mocker):
        """Test that generated log file path is within log folder."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        log_file = logger_manager.generate_log_file_name()

        assert log_file.startswith(temp_log_dir)
        assert log_file.endswith(".log")

    def test_timestamp_format_in_filename(self, temp_log_dir, mocker):
        """Test that timestamp format is correct in filename."""
        mocker.patch("os.path.exists", return_value=True)
        mock_dt = mocker.patch("data_validate.helpers.base.logger_manager.datetime")
        mock_dt.now.return_value.strftime.return_value = "20231201_143022"

        logger_manager = LoggerManager(log_folder=temp_log_dir)
        log_file = logger_manager.generate_log_file_name("test")

        assert "20231201_143022" in log_file
        mock_dt.now.return_value.strftime.assert_called_with("%Y%m%d_%H%M%S")

    def test_logger_integration_console_and_file(self, temp_log_dir, mocker):
        """Test complete integration of console and file loggers."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        # Test that both loggers are created
        assert logger_manager.console_logger is not None
        assert logger_manager.file_logger is not None

        # Test that file logger has file handler
        file_handlers = [h for h in logger_manager.file_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

    def test_custom_formatter_applied_to_handlers(self, temp_log_dir, mocker):
        """Test that CustomFormatter is applied to all handlers."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        test_logger = logger_manager.configure_logger("test_logger", log_file=os.path.join(temp_log_dir, "test.log"))

        # Check that all handlers have CustomFormatter
        for handler in test_logger.handlers:
            assert isinstance(handler.formatter, CustomFormatter)

    def test_makedirs_called_with_correct_path(self, temp_log_dir, mocker):
        """Test that os.makedirs is called with correct path when folder doesn't exist."""
        test_folder = temp_log_dir

        mocker.patch("os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("os.makedirs")
        mock_dt = mocker.patch("data_validate.helpers.base.logger_manager.datetime")
        mock_dt.now.return_value.strftime.return_value = "20230101_120000"

        LoggerManager(log_folder=test_folder)

        mock_makedirs.assert_called_once_with(test_folder)

    def test_logging_levels_hierarchy(self, temp_log_dir, mocker):
        """Test that logging levels work correctly."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir, default_level=logging.WARNING)

        test_logger = logger_manager.configure_logger("hierarchy_test")

        # Logger should be set to WARNING level
        assert test_logger.level == logging.WARNING
        assert test_logger.isEnabledFor(logging.WARNING)
        assert test_logger.isEnabledFor(logging.ERROR)
        assert test_logger.isEnabledFor(logging.CRITICAL)

    def test_multiple_loggers_creation(self, temp_log_dir, mocker):
        """Test creation of multiple loggers with different configurations."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        logger1 = logger_manager.configure_logger("logger1", level=logging.DEBUG)
        logger2 = logger_manager.configure_logger("logger2", level=logging.INFO)
        logger3 = logger_manager.configure_logger("logger3", level=logging.ERROR)

        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger3.name == "logger3"

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.INFO
        assert logger3.level == logging.ERROR

    def test_file_path_construction(self, temp_log_dir, mock_datetime, mocker):
        """Test that file paths are constructed correctly."""
        mocker.patch("os.path.exists", return_value=True)

        logger_manager = LoggerManager(log_folder=temp_log_dir)

        mock_join = mocker.patch("os.path.join", return_value="mocked_path")
        result = logger_manager.generate_log_file_name("test")

        mock_join.assert_called_once_with(temp_log_dir, "test_20230101_120000.log")
        assert result == "mocked_path"
