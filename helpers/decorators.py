"""
Decorators module providing test automation specific decorators.
"""
import inspect
import time
from datetime import datetime
from functools import wraps
from typing import Callable, Optional, Type, Tuple, Any

from core.logger import Log
from core.plugins.test_case_plugin import TestCasePlugin
from core.step import Step, step_start


class WaitTimeoutError(Exception):
    """Custom exception for wait_until timeout scenarios."""
    pass


def wait_until(*args, timeout: float = 10, interval: float = 0.5,
               ignored_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
               error_message: Optional[str] = None,
               reset_logs: bool = False) -> Callable:
    """
    Decorator that retries a function until it succeeds or timeout is reached.
    Handles both assertion errors and specified exceptions.

    @param timeout: Maximum wait time in seconds (default: 10)
    @param interval: Sleep interval between retries in seconds (default: 0.5)
    @param ignored_exceptions: Tuple of exception types to ignore until timeout
    @param error_message: Custom error message for timeout
    @param reset_logs: Whether to reset step counter for each retry (default: False)
    @return: Decorated function
    @raises: Last caught exception if timeout is reached

    Example usage:
        # Basic usage
        @wait_until
        def check_condition():
            assert element.is_displayed()

        # With custom parameters
        @wait_until(timeout=20, interval=1)
        def check_with_params():
            return element.is_displayed()

        # With custom exceptions to ignore
        @wait_until(
            ignored_exceptions=(ValueError, TypeError),
            error_message="Custom error"
        )
        def check_with_exceptions():
            return validate_something()
    """
    default_exceptions = (AssertionError,)

    # Combine default and user-specified exceptions
    if ignored_exceptions:
        if not isinstance(ignored_exceptions, tuple):
            ignored_exceptions = tuple(ignored_exceptions)
        exceptions_to_ignore = default_exceptions + ignored_exceptions
    else:
        exceptions_to_ignore = default_exceptions

    def _wait_until(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args_, **kwargs_) -> Any:
            start_time = datetime.now()
            attempt = 1

            while True:
                try:
                    if reset_logs and attempt > 1:
                        Log.debug(f"Resetting steps for attempt {attempt}")
                        # Store current execution before reset
                        current_execution = TestCasePlugin.get_current_execution()

                        # Reset all step data
                        Step.reset_for_test()
                        Log.reset_step_counter()

                        # Restore execution record
                        TestCasePlugin.set_current_execution(current_execution)

                    Log.debug(f"Starting attempt {attempt} for {func.__name__}")
                    result = func(*args_, **kwargs_)

                    # If function returns something explicitly, return that value
                    if result is not None:
                        return result
                    # Otherwise, consider it a success
                    return True

                except exceptions_to_ignore as e:
                    last_exception = e
                    elapsed = (datetime.now() - start_time).total_seconds()

                    if elapsed > timeout:
                        # Prepare detailed timeout message
                        timeout_msg = (
                            f"Timeout after {elapsed:.2f}s waiting for {func.__name__} "
                            f"(attempts: {attempt})"
                        )
                        if error_message:
                            timeout_msg = f"{timeout_msg}: {error_message}"
                        if last_exception:
                            timeout_msg = f"{timeout_msg}. Last error: {str(last_exception)}"

                        Log.error(timeout_msg)
                        raise WaitTimeoutError(timeout_msg) from last_exception

                    Log.debug(f"Attempt {attempt} failed: {str(e)}")
                    time.sleep(interval)
                    attempt += 1

                except Exception as e:
                    # Non-ignored exceptions are raised immediately
                    Log.error(f"Non-ignored exception in {func.__name__}: {str(e)}")
                    raise

        return wrapper

    # Handle both @wait_until and @wait_until() syntax
    if len(args) == 1 and callable(args[0]):
        return _wait_until(args[0])
    return _wait_until


def step(func: Optional[Callable] = None, *, content: Optional[str] = None) -> Callable:
    """
    Decorator to mark function as a step.
    Can be used with or without parameters.

    @param func: Function to decorate
    @param content: Optional step description template. Can include {param} placeholders
    @return: Decorated function
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get current step before starting new one

            if content:
                try:
                    # Combine positional and keyword arguments for formatting
                    format_args = {}
                    if args:
                        # Get function parameter names
                        sig = inspect.signature(f)
                        param_names = list(sig.parameters.keys())
                        # Map positional args to their parameter names
                        format_args.update(zip(param_names, args))
                    format_args.update(kwargs)

                    step_content = content.format(**format_args)
                except (KeyError, IndexError):
                    # If formatting fails, use content as it is
                    step_content = content
            else:
                step_content = f.__name__.replace('_', ' ').title()

            # Get the actual function name for step_function
            actual_function = f.__name__

            with step_start(step_content, function_name=actual_function):
                result = f(*args, **kwargs)
                return result

        return wrapper

    if func is None:
        return decorator
    return decorator(func)
