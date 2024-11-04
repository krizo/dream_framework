import io
import logging
import os

import pytest

from core.logger import (
    Log, MultiFormatter, ConsoleFilter, FileFilter,
    CONSOLE_LEVEL, STEP_LEVEL, EMPTY_LEVEL, EmptyFormatter
)
from core.test_case import TestCase


@pytest.fixture
def dummy_test_case():
    """
    Provide minimal TestCase implementation for testing.

    @return: TestCase instance
    """

    class DummyTestCase(TestCase):
        @property
        def test_suite(self) -> str:
            return "Dummy Suite"

    return DummyTestCase(
        name="Dummy Test",
        scope="Unit",
        component="API"
    )


@pytest.fixture(autouse=True)
def reset_logger(dummy_test_case):
    """
    Reset logger before and after each test.
    Also temporarily disable any existing handlers and clean up log file.

    @param dummy_test_case: Dummy TestCase fixture to prevent real test case creation
    @return: None
    """
    # Store original handlers
    logger = logging.getLogger("TestLogger")
    original_handlers = logger.handlers[:]
    logger.handlers.clear()

    Log.reset()
    yield

    # Restore original handlers
    Log.reset()
    for handler in original_handlers:
        logger.addHandler(handler)

    # Clean up test.log if exists
    try:
        if os.path.exists('test.log'):
            os.remove('test.log')
    except Exception as e:
        print(f"Warning: Could not remove test.log: {str(e)}")


def test_logger_initialization(tmp_path, dummy_test_case):
    """
    Test logger initialization and configuration.

    @param tmp_path: pytest temporary directory fixture
    @param dummy_test_case: Dummy TestCase fixture
    """
    # Initialize logger with a test file
    test_log = tmp_path / "test.log"
    Log.reconfigure_file_handler(str(test_log))
    logger = Log._get_logger()

    # Basic configuration checks
    assert logger.name == "TestLogger"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2  # Console and file handler

    # Log a test message
    test_msg = "Test initialization"
    Log.info(test_msg)

    # Read log file content
    for handler in logger.handlers:
        handler.flush()
    content = test_log.read_text()

    # Verify message was logged
    assert test_msg in content


def test_log_levels(tmp_path, dummy_test_case):
    """
    Test all log levels output.

    @param tmp_path: pytest temporary directory fixture
    @param dummy_test_case: Dummy TestCase fixture
    """
    test_log = tmp_path / "levels.log"
    Log.reconfigure_file_handler(str(test_log))
    logger = Log._get_logger()

    test_messages = {
        "debug": "Debug message",
        "console": "Console message",
        "info": "Info message",
        "step": "Step message",
        "warning": "Warning message",
        "error": "Error message",
        "critical": "Critical message"
    }

    # Log test messages
    Log.console(test_messages["console"])
    Log.info(test_messages["info"])
    Log.step(test_messages["step"])
    Log.warning(test_messages["warning"])
    Log.error(test_messages["error"])
    Log.critical(test_messages["critical"])

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Read log content
    content = test_log.read_text()

    # File should contain these messages
    assert test_messages["info"] in content, "Info message not found"
    assert test_messages["warning"] in content, "Warning message not found"
    assert test_messages["error"] in content, "Error message not found"
    assert test_messages["critical"] in content, "Critical message not found"
    assert f"{test_messages['step']}" in content, "Step message not found"

    # File should not contain these messages
    assert test_messages["debug"] not in content, "Debug message should not be in file"
    assert test_messages["console"] not in content, "Console message should not be in file"


def test_step_counter(tmp_path, dummy_test_case):
    """
    Test step counter functionality.

    @param tmp_path: pytest temporary directory fixture
    @param dummy_test_case: Dummy TestCase fixture
    """
    test_log = tmp_path / "steps.log"
    Log.reconfigure_file_handler(str(test_log))
    logger = Log._get_logger()

    # Reset counter at start
    Log.reset_step_counter()
    assert Log._step_counter == 0

    # Log steps
    steps = ["First step", "Second step", "Third step"]
    for step in steps:
        Log.step(step)

    # Force flush
    for handler in logger.handlers:
        handler.flush()

    # Verify counter
    assert Log._step_counter == 3

    # Verify log content
    content = test_log.read_text()
    assert "First step" in content
    assert "Second step" in content
    assert "Third step" in content

    # Test reset
    Log.reset_step_counter()
    assert Log._step_counter == 0


def test_separator(tmp_path, dummy_test_case):
    """
    Test separator line generation.

    @param tmp_path: pytest temporary directory fixture
    @param dummy_test_case: Dummy TestCase fixture
    """
    # Use StringIO instead of file for direct content checking
    buffer = io.StringIO()

    logger = Log._get_logger()
    logger.handlers.clear()

    # Add test handler with simple formatter
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(EmptyFormatter())  # Use EmptyFormatter to get raw separator lines
    logger.addHandler(handler)

    # Test separators
    Log.separator('-', 80)  # default separator
    Log.separator('=', 40)  # custom separator

    # Force flush and get content
    handler.flush()
    content = buffer.getvalue()

    # Print debug info
    print("\nSeparator test content:")
    print(repr(content))

    # Verify separators
    assert '-' * 80 in content, "Default separator not found"
    assert '=' * 40 in content, "Custom separator not found"


def test_console_output(tmp_path, dummy_test_case):
    """
    Test console output handling.

    @param tmp_path: pytest temporary directory fixture
    @param dummy_test_case: Dummy TestCase fixture
    """
    console_buffer = io.StringIO()
    file_buffer = io.StringIO()

    logger = Log._get_logger()
    logger.handlers.clear()

    # Add test handlers
    console_handler = logging.StreamHandler(console_buffer)
    console_handler.addFilter(ConsoleFilter())
    console_handler.setFormatter(MultiFormatter())

    file_handler = logging.StreamHandler(file_buffer)
    file_handler.addFilter(FileFilter())
    file_handler.setFormatter(MultiFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Test messages
    test_messages = {
        "console": "Console only message",
        "info": "Info message for both",
        "error": "Error for both outputs"
    }

    Log.console(test_messages["console"])
    Log.info(test_messages["info"])
    Log.error(test_messages["error"])

    # Force flush
    console_handler.flush()
    file_handler.flush()

    console_output = console_buffer.getvalue()
    file_output = file_buffer.getvalue()

    # Console should have all messages
    assert test_messages["console"] in console_output
    assert test_messages["info"] in console_output
    assert test_messages["error"] in console_output

    # File should not have console messages
    assert test_messages["console"] not in file_output
    assert test_messages["info"] in file_output
    assert test_messages["error"] in file_output


def test_formatter(dummy_test_case):
    """
    Test log message formatting.

    @param dummy_test_case: Dummy TestCase fixture
    """
    formatter = MultiFormatter()

    # Test regular message
    record = logging.LogRecord(
        "test", logging.INFO, "", 0, "Test message", (), None
    )
    formatted = formatter.format(record)
    assert "INFO" in formatted
    assert "Test message" in formatted
    assert "|" in formatted

    # Test empty message
    empty_record = logging.LogRecord(
        "test", EMPTY_LEVEL, "", 0, "Raw message", (), None
    )
    empty_formatted = formatter.format(empty_record)
    assert empty_formatted == "Raw message"
    assert "|" not in empty_formatted


def test_filters(dummy_test_case):
    """
    Test log filters behavior.

    @param dummy_test_case: Dummy TestCase fixture
    """
    console_filter = ConsoleFilter()
    file_filter = FileFilter()

    def create_record(level):
        return logging.LogRecord(
            "test", level, "", 0, "test", (), None
        )

    # Console filter
    assert console_filter.filter(create_record(CONSOLE_LEVEL))
    assert console_filter.filter(create_record(logging.INFO))
    assert not console_filter.filter(create_record(logging.DEBUG))

    # File filter
    assert not file_filter.filter(create_record(CONSOLE_LEVEL))
    assert file_filter.filter(create_record(logging.INFO))
    assert file_filter.filter(create_record(STEP_LEVEL))
