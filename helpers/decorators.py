"""
Decorators module providing test automation specific decorators.
"""
import time
from datetime import datetime
from functools import wraps
from typing import Callable, Optional, Type, Tuple, Any

from core.logger import Log


class WaitTimeoutError(Exception):
    """Custom exception for wait_until timeout scenarios."""
    pass


def wait_until(*args, timeout: float = 10, interval: float = 0.5,
               ignored_exceptions: Optional[Tuple[Type[Exception], ...]] = None, error_message: Optional[str] = None
) -> Callable:
    """
    Decorator that retries a function until it succeeds or timeout is reached.
    Handles both assertion errors and specified exceptions.

    @param timeout: Maximum wait time in seconds (default: 10)
    @param interval: Sleep interval between retries in seconds (default: 0.5)
    @param ignored_exceptions: Tuple of exception types to ignore until timeout
    @param error_message: Custom error message for timeout
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
                    Log.debug(f"Attempt {attempt} for {func.__name__}")
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
