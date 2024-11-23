"""Tests for WaitUntilConfig."""
import configparser
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from core.configuration.wait_until_config import WaitUntilConfig

pytestmark = pytest.mark.no_database_plugin


@pytest.fixture(autouse=True)
def reset_config():
    """
    Reset configuration before each test.
    Ensures clean state for each test case.
    """
    WaitUntilConfig._instance = None
    WaitUntilConfig._config_path = None
    WaitUntilConfig.clear_cache()
    yield


@pytest.fixture
def config_file(tmp_path):
    """
    Create temporary config file with test configuration.

    @param tmp_path: Pytest fixture providing temporary directory
    @return: Path to test configuration file
    """
    config_content = """[WAIT_UNTIL]
default_exceptions = ["builtins.AssertionError", "builtins.ValueError", "pytest.skip.Exception"]
default_timeout = 15.5
default_interval = 0.75"""

    config_file = tmp_path / "test_config.ini"
    config_file.write_text(config_content)
    return config_file


def test_get_default_exceptions_valid_config(config_file):
    """
    Test getting default exceptions from valid configuration.
    Should properly parse and return configured exception classes.
    """
    WaitUntilConfig.set_config_path(config_file)
    exceptions = WaitUntilConfig.get_default_exceptions()

    # Debug info
    print(f"\nFound exceptions: {exceptions}")

    # Verify all expected exceptions are present
    assert isinstance(exceptions, tuple), "Should return a tuple of exceptions"
    exception_classes = set(exc for exc in exceptions)
    assert AssertionError in exception_classes, "Missing AssertionError"


def test_get_default_exceptions_invalid_format():
    """
    Test handling of invalid exception format.
    Should fallback to default exceptions when config is invalid.
    """
    invalid_config = """[WAIT_UNTIL]
default_exceptions = ["InvalidFormat", "no.dots.here"]
default_timeout = 15.5
default_interval = 0.75"""

    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.open', mock_open(read_data=invalid_config)):
        mock_exists.return_value = True

        WaitUntilConfig.set_config_path(Path("test_config.ini"))
        exceptions = WaitUntilConfig.get_default_exceptions()

        # Should return default (AssertionError,)
        assert exceptions == (AssertionError,)


def test_parse_exception_list_valid():
    """
    Test parsing valid exception list.
    Should correctly parse properly formatted exception strings.
    """
    exceptions_str = '["builtins.AssertionError", "builtins.ValueError"]'
    result = WaitUntilConfig.parse_exception_list(exceptions_str)

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(exc, str) for exc in result)
    assert "builtins.AssertionError" in result
    assert "builtins.ValueError" in result


def test_parse_exception_list_invalid_syntax():
    """
    Test parsing exception list with invalid syntax.
    Should return empty list for invalid input.
    """
    exceptions_str = 'not a valid python list'
    result = WaitUntilConfig.parse_exception_list(exceptions_str)
    assert result == []


def test_get_default_timeout_valid(config_file):
    """
    Test getting default timeout from valid configuration.
    Should return configured timeout value.
    """
    WaitUntilConfig.set_config_path(config_file)
    timeout = WaitUntilConfig.get_default_timeout()
    assert timeout == 15.5


def test_get_default_timeout_invalid():
    """
    Test handling of invalid timeout value.
    Should fallback to default timeout when config is invalid.
    """
    invalid_config = """[WAIT_UNTIL]
default_timeout = invalid"""

    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.open', mock_open(read_data=invalid_config)):
        mock_exists.return_value = True

        WaitUntilConfig.set_config_path(Path("test_config.ini"))
        timeout = WaitUntilConfig.get_default_timeout()

        assert timeout == 10.0  # default value


def test_get_default_interval_valid(config_file):
    """
    Test getting default interval from valid configuration.
    Should return configured interval value.
    """
    WaitUntilConfig.set_config_path(config_file)
    interval = WaitUntilConfig.get_default_interval()
    assert interval == 0.75


def test_get_default_interval_negative():
    """
    Test handling of negative interval value.
    Should fallback to default interval when configured value is invalid.
    """
    invalid_config = """[WAIT_UNTIL]
default_interval = -1.0"""

    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.open', mock_open(read_data=invalid_config)):
        mock_exists.return_value = True

        WaitUntilConfig.set_config_path(Path("test_config.ini"))
        interval = WaitUntilConfig.get_default_interval()

        assert interval == 0.5  # default value


def test_config_file_not_found():
    """
    Test behavior when configuration file is not found.
    Should return default values when file doesn't exist.
    """
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False

        WaitUntilConfig.set_config_path(Path("nonexistent.ini"))

        assert WaitUntilConfig.get_default_timeout() == 10.0
        assert WaitUntilConfig.get_default_interval() == 0.5
        assert WaitUntilConfig.get_default_exceptions() == (AssertionError,)


def test_cache_behavior():
    """
    Test configuration caching behavior.
    Should cache values and reload them when cache is cleared.
    """

    with patch.object(configparser.ConfigParser, 'read'), \
         patch.object(configparser.ConfigParser, 'has_section') as mock_has_section, \
         patch.object(configparser.ConfigParser, 'has_option') as mock_has_option, \
         patch.object(configparser.ConfigParser, 'get') as mock_get:

        mock_has_section.return_value = True
        mock_has_option.return_value = True
        mock_get.return_value = "20.0"

        WaitUntilConfig.set_config_path(Path("test_config.ini"))

        # First call should read configuration
        timeout1 = WaitUntilConfig.get_default_timeout()
        assert timeout1 == 20.0
        assert mock_get.call_count == 1

        # Second call should use cache
        timeout2 = WaitUntilConfig.get_default_timeout()
        assert timeout2 == 20.0
        assert mock_get.call_count == 1

        # After clearing cache, should read again
        WaitUntilConfig.clear_cache()
        timeout3 = WaitUntilConfig.get_default_timeout()
        assert timeout3 == 20.0
        assert mock_get.call_count == 2