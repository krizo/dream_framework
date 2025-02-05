import io
import logging

import pytest

from core.logger import (
    Log, ConsoleFilter, FileFilter,
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
def reset_logger():
    """
    Reset logger before and after each test.
    """
    Log.reset()
    yield
    Log.reset()


def test_logger_initialization(tmp_path):
    """
    Test logger initialization and configuration.

    @param tmp_path: pytest temporary directory fixture
    """
    test_log = tmp_path / "test.log"
    Log.reconfigure_file_handler(str(test_log))
    logger = Log.get_logger()

    assert logger.name == "TestLogger"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1

    test_msg = "Test initialization"
    Log.info(test_msg)

    for handler in logger.handlers:
        handler.flush()
    content = test_log.read_text()

    assert test_msg in content


def test_log_levels(tmp_path):
    """
    Test different log level outputs.

    @param tmp_path: pytest temporary directory fixture
    """
    test_log = tmp_path / "levels.log"
    Log.reconfigure_file_handler(str(test_log))

    messages = {
        "debug": "Debug message",
        "console": "Console message",
        "info": "Info message",
        "step": "Step message",
        "warning": "Warning message",
        "error": "Error message",
        "critical": "Critical message"
    }

    Log.console(messages["console"])
    Log.info(messages["info"])
    Log.step(messages["step"])
    Log.warning(messages["warning"])
    Log.error(messages["error"])
    Log.critical(messages["critical"])

    for handler in Log.get_logger().handlers:
        handler.flush()

    content = test_log.read_text()

    assert messages["info"] in content
    assert messages["warning"] in content
    assert messages["error"] in content
    assert messages["critical"] in content
    assert messages["step"] in content

    assert messages["debug"] not in content
    assert messages["console"] not in content


def test_step_counter(tmp_path):
    """
    Test step counter functionality.

    @param tmp_path: pytest temporary directory fixture
    """
    test_log = tmp_path / "steps.log"
    Log.reconfigure_file_handler(str(test_log))

    Log.reset_step_counter()
    assert Log._step_counter == 0

    steps = ["First step", "Second step", "Third step"]
    for step in steps:
        Log.step(step)

    assert Log._step_counter == 3

    content = test_log.read_text()
    for step in steps:
        assert step in content

    Log.reset_step_counter()
    assert Log._step_counter == 0


def test_empty_formatter():
    """Test empty message formatter."""
    formatter = EmptyFormatter()
    record = logging.LogRecord(
        "test", EMPTY_LEVEL, "", 0, "Raw message", (), None
    )
    formatted = formatter.format(record)
    assert formatted == "Raw message"


def test_log_file_switch(tmp_path):
    """
    Test switching log files.

    @param tmp_path: pytest temporary directory fixture
    """
    log1 = tmp_path / "log1.log"
    log2 = tmp_path / "log2.log"

    Log.switch_log_file(str(log1))
    Log.info("Message 1")

    Log.switch_log_file(str(log2))
    Log.info("Message 2")

    assert "Message 1" in log1.read_text()
    assert "Message 2" in log2.read_text()
    assert "Message 1" not in log2.read_text()


def test_separator(tmp_path):
    """
    Test separator line generation.

    @param tmp_path: pytest temporary directory fixture
    """
    buffer = io.StringIO()
    logger = Log.get_logger()
    logger.handlers.clear()

    handler = logging.StreamHandler(buffer)
    handler.setFormatter(EmptyFormatter())
    logger.addHandler(handler)

    Log.separator('-', 80)
    Log.separator('=', 40)

    content = buffer.getvalue()

    assert '-' * 80 in content
    assert '=' * 40 in content


def test_filters():
    """Test log filters behavior."""
    console_filter = ConsoleFilter()
    file_filter = FileFilter()

    def create_record(level):
        return logging.LogRecord(
            "test", level, "", 0, "test", (), None
        )

    assert console_filter.filter(create_record(CONSOLE_LEVEL))
    assert console_filter.filter(create_record(logging.INFO))
    assert not console_filter.filter(create_record(logging.DEBUG))

    assert not file_filter.filter(create_record(CONSOLE_LEVEL))
    assert file_filter.filter(create_record(logging.INFO))
    assert file_filter.filter(create_record(STEP_LEVEL))