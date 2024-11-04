"""
Tests for wait_until decorator functionality.
"""
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from helpers.decorators import wait_until, WaitTimeoutError

pytestmark = pytest.mark.no_database_plugin


def test_successful_immediate_return():
    """Test when function succeeds immediately."""
    counter = 0

    @wait_until
    def test_func():
        nonlocal counter
        counter += 1
        return True

    result = test_func()
    assert result is True
    assert counter == 1


def test_successful_after_retries():
    """Test when function succeeds after several retries."""
    counter = 0

    @wait_until(timeout=2, interval=0.1)
    def test_func():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise AssertionError("Not ready yet")
        return True

    result = test_func()
    assert result is True
    assert counter == 3


def test_timeout_reached():
    """Test when function times out."""
    counter = 0

    @wait_until(timeout=0.5, interval=0.1)
    def test_func():
        nonlocal counter
        counter += 1
        raise AssertionError("Never ready")

    with pytest.raises(WaitTimeoutError) as exc_info:
        test_func()

    assert "Never ready" in str(exc_info.value)
    assert counter >= 4  # Should have tried at least 4 times in 0.5 seconds


def test_custom_exceptions():
    """Test handling of custom exceptions."""

    @wait_until(
        timeout=0.5,
        interval=0.1,
        ignored_exceptions=(ValueError,),
        error_message="Custom error"
    )
    def test_func():
        raise ValueError("Testing custom exception")

    with pytest.raises(WaitTimeoutError) as exc_info:
        test_func()

    assert "Custom error" in str(exc_info.value)
    assert "Testing custom exception" in str(exc_info.value)


def test_non_ignored_exception():
    """Test immediate raise of non-ignored exception."""

    @wait_until(timeout=1, interval=0.1)
    def test_func():
        raise TypeError("Non-ignored exception")

    with pytest.raises(TypeError) as exc_info:
        test_func()

    assert "Non-ignored exception" in str(exc_info.value)


def test_return_value_handling():
    """Test handling of different return values."""

    @wait_until(timeout=0.5)
    def test_func():
        return "success"

    result = test_func()
    assert result == "success"


def test_execution_time_tracking():
    """Test accurate tracking of execution time."""
    start_time = None

    @wait_until(timeout=1, interval=0.2)
    def test_func():
        nonlocal start_time
        if start_time is None:
            start_time = datetime.now()
            raise AssertionError("First attempt")
        if (datetime.now() - start_time).total_seconds() < 0.4:
            raise AssertionError("Not enough time passed")
        return True

    result = test_func()
    assert result is True


@patch('time.sleep')
def test_interval_accuracy(mock_sleep):
    """Test accurate interval timing between retries."""
    counter = 0

    @wait_until(timeout=1, interval=0.25)
    def test_func():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise AssertionError("Not yet")
        return True

    test_func()
    assert mock_sleep.call_count == 2  # Should have slept twice
    mock_sleep.assert_called_with(0.25)


def test_long_running_function():
    """Test handling of long-running functions."""

    @wait_until(timeout=1, interval=0.1)
    def test_func():
        time.sleep(0.3)  # Simulate long operation
        return True

    start_time = time.time()
    result = test_func()
    execution_time = time.time() - start_time

    assert result is True
    assert execution_time >= 0.3  # Should have taken at least 0.3 seconds


def test_nested_decorators():
    """Test compatibility with other decorators."""

    def another_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @wait_until(timeout=0.5)
    @another_decorator
    def test_func():
        return True

    assert test_func() is True


def test_error_message_formatting():
    """Test proper formatting of error messages."""
    counter = 0

    @wait_until(
        timeout=0.5,
        interval=0.1,
        error_message="Custom error message"
    )
    def test_func():
        nonlocal counter
        counter += 1
        raise AssertionError(f"Attempt {counter} failed")

    with pytest.raises(WaitTimeoutError) as exc_info:
        test_func()

    error_message = str(exc_info.value)
    assert "Custom error message" in error_message
    assert "Attempt" in error_message
    assert str(counter) in error_message


class TestClass:
    """Test class for testing decorator with class methods."""

    def __init__(self):
        self.counter = 0

    @wait_until(timeout=0.5, interval=0.1)
    def test_method(self):
        self.counter += 1
        if self.counter < 3:
            raise AssertionError("Not ready")
        return True


def test_class_method():
    """Test decorator on class methods."""
    test_obj = TestClass()
    result = test_obj.test_method()
    assert result is True
    assert test_obj.counter == 3


@pytest.mark.parametrize("timeout,interval,expected_attempts", [
    (0.5, 0.1, 5),  # Should make about 5 attempts
    (1.0, 0.2, 5),  # Should make about 5 attempts
    (0.3, 0.1, 3),  # Should make about 3 attempts
])
def test_attempt_counts(timeout, interval, expected_attempts):
    """Test correct number of attempts based on timeout and interval."""
    counter = 0

    @wait_until(timeout=timeout, interval=interval)
    def test_func():
        nonlocal counter
        counter += 1
        raise AssertionError("Never ready")

    with pytest.raises(WaitTimeoutError):
        test_func()

    assert abs(counter - expected_attempts) <= 1  # Allow for small timing variations
