"""Wait Until decorator configuration."""
import ast
import importlib
from functools import lru_cache
from typing import List, Type, Tuple

from core.logger import Log
from .config_parser import ConfigParser


class WaitUntilConfig(ConfigParser):
    """Configuration parser for wait_until decorator settings."""

    SECTION_NAME = "WAIT_UNTIL"

    @classmethod
    def parse_exception_list(cls, value_str: str) -> List[str]:
        """
        Safely parse list of exception class paths.

        @param value_str: String containing list of exception paths
        @return: List of validated exception paths
        """
        try:
            # Parse using safe ast.literal_eval
            parsed_value = ast.literal_eval(value_str)

            # Validate it's a list
            if not isinstance(parsed_value, list):
                Log.error(f"Exception configuration must be a list, got: {type(parsed_value)}")
                return []

            # Validate all elements are strings
            if not all(isinstance(x, str) for x in parsed_value):
                Log.error("All exceptions must be string values")
                return []

            # Validate format of each exception path
            valid_exceptions = []
            for exc_path in parsed_value:
                if '.' not in exc_path:
                    Log.warning(f"Invalid exception format (no module path): {exc_path}")
                    continue

                _, class_name = exc_path.rsplit('.', 1)
                if not (class_name.endswith('Error') or class_name.endswith('Exception')):
                    Log.warning(f"Suspicious exception name: {class_name}")
                    continue

                valid_exceptions.append(exc_path)

            return valid_exceptions

        except (ValueError, SyntaxError) as e:
            Log.error(f"Failed to parse exception list: {str(e)}")
            return []

    @classmethod
    @lru_cache(maxsize=16)
    def get_default_exceptions(cls) -> Tuple[Type[Exception], ...]:
        """
        Get configured default exceptions to ignore.

        @return: Tuple of exception classes
        """
        DEFAULT_EXCEPTIONS = (AssertionError,)

        try:
            exceptions_str = cls.get_value('default_exceptions',
                                           '["builtins.AssertionError"]')
            if not exceptions_str:
                return DEFAULT_EXCEPTIONS

            # Parse exception list safely
            exception_paths = cls.parse_exception_list(exceptions_str)
            if not exception_paths:
                return DEFAULT_EXCEPTIONS

            # Import and validate each exception class
            exceptions = []
            for exc_path in exception_paths:
                try:
                    module_path, exc_name = exc_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    exc_class = getattr(module, exc_name)

                    # Validate it's a proper exception class
                    if isinstance(exc_class, type) and issubclass(exc_class, Exception):
                        exceptions.append(exc_class)
                    else:
                        Log.warning(f"Invalid exception class: {exc_path}")

                except (ImportError, AttributeError) as e:
                    Log.warning(f"Failed to import exception {exc_path}: {str(e)}")

            return tuple(exceptions) if exceptions else DEFAULT_EXCEPTIONS

        except Exception as e:
            Log.error(f"Error getting default exceptions: {str(e)}")
            return DEFAULT_EXCEPTIONS

    @classmethod
    def get_default_timeout(cls) -> float:
        """
        Get configured default timeout.

        @return: Default timeout in seconds
        """
        DEFAULT_TIMEOUT = 10.0
        try:
            value = cls.get_value('default_timeout', DEFAULT_TIMEOUT)
            # Validate timeout is a positive number
            if not isinstance(value, (int, float)) or value <= 0:
                Log.warning(f"Invalid timeout value: {value}, using default")
                return DEFAULT_TIMEOUT
            return float(value)
        except (ValueError, TypeError) as e:
            Log.error(f"Error parsing timeout: {str(e)}")
            return DEFAULT_TIMEOUT

    @classmethod
    def get_default_interval(cls) -> float:
        """
        Get configured default interval between retries.

        @return: Default interval in seconds
        """
        DEFAULT_INTERVAL = 0.5
        try:
            value = cls.get_value('default_interval', DEFAULT_INTERVAL)
            # Validate interval is a positive number
            if not isinstance(value, (int, float)) or value <= 0:
                Log.warning(f"Invalid interval value: {value}, using default")
                return DEFAULT_INTERVAL
            return float(value)
        except (ValueError, TypeError) as e:
            Log.error(f"Error parsing interval: {str(e)}")
            return DEFAULT_INTERVAL
