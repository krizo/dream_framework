import logging
from enum import Enum
from typing import Optional

# Custom log levels
STEP_LEVEL = 35
CONSOLE_LEVEL = 15  # Between DEBUG and INFO
EMPTY_LEVEL = 11  # Be
logging.addLevelName(STEP_LEVEL, "STEP")
logging.addLevelName(CONSOLE_LEVEL, "CONSOLE")
logging.addLevelName(EMPTY_LEVEL, "EMPTY")


class LogLevel(Enum):
    """
    Enumeration of available log levels.

    @param EMPTY: int - Level for messages without additional information
    @param DEBUG: int - Level for detailed debugging information
    @param CONSOLE: int - Level for console-only output
    @param INFO: int - Level for general information
    @param STEP: int - Level for test step information
    @param WARNING: int - Level for warning messages
    @param ERROR: int - Level for error messages
    @param CRITICAL: int - Level for critical error messages
    """
    EMPTY = EMPTY_LEVEL
    DEBUG = logging.DEBUG
    CONSOLE = CONSOLE_LEVEL
    INFO = logging.INFO
    STEP = STEP_LEVEL
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class MultiFormatter(logging.Formatter):
    """
    Formatter that applies different formats based on the log level.
    
    @param fmt: str - Message format string
    @param datefmt: str - Date format string
    @param style: str - Format style
    @param validate: bool - Whether to validate the format string
    @return str - The formatted message
    """
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        super().__init__(fmt, datefmt, style, validate)
        self.default_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            style='%'
        )

    def format(self, record):
        if record.levelno == EMPTY_LEVEL:
            return record.getMessage()
        return self.default_formatter.format(record)


class ConsoleFilter(logging.Filter):
    """ Filter for console output to show only CONSOLE level messages. """

    def filter(self, record):
        """
        Filter log records for console output.

        @param record: logging.LogRecord - The log record to be filtered
        @return bool - True if the record should be logged, False otherwise
        """
        return record.levelno in [CONSOLE_LEVEL, logging.INFO, STEP_LEVEL,
                                  logging.WARNING, logging.ERROR, logging.CRITICAL]


class FileFilter(logging.Filter):
    """ Filter for file output to show INFO and STEP level messages. """

    def filter(self, record):
        """
        Filter log records for file output.

        @param record: logging.LogRecord - The log record to be filtered
        @return bool - True if the record should be logged, False otherwise
        """
        return record.levelno in [logging.INFO, STEP_LEVEL, logging.WARNING, logging.ERROR, logging.CRITICAL]


class EmptyFormatter(logging.Formatter):
    """
    Formatter for EMPTY level messages - returns message without any additional formatting.

    @param record: logging.LogRecord - The log record to be formatted
    @return str - The formatted message
    """

    def format(self, record):
        return record.getMessage()


class Log:
    """
    Static logger class providing centralized logging functionality.
    """
    _instance: Optional[logging.Logger] = None
    _step_counter: int = 0

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        """
        Get or create logger instance.

        @return logging.Logger - Configured logger instance
        """
        if cls._instance is None:
            cls._instance = logging.getLogger("TestLogger")
        return cls._instance

    @classmethod
    def _log(cls, level: LogLevel, message: str, *args, **kwargs):
        """
        Internal logging method.

        @param level: LogLevel - Enum value defining log level
        @param message: str - Message to be logged
        @param args: tuple - Variable length argument list
        @param kwargs: dict - Arbitrary keyword arguments
        """
        logger = cls._get_logger()
        logger.log(level.value, message, *args, **kwargs)

    @classmethod
    def console(cls, message: str):
        """
        Log console message (visible only in console output).

        @param message: str - Console message to be logged
        """
        cls._log(LogLevel.CONSOLE, message)

    @classmethod
    def debug(cls, message: str):
        """
        Log debug message.

        @param message: str - Debug message to be logged
        """
        cls._log(LogLevel.DEBUG, message)

    @classmethod
    def info(cls, message: str):
        """
        Log info message (visible in pytest report).

        @param message: str - Info message to be logged
        """
        cls._log(LogLevel.INFO, message)

    @classmethod
    def step(cls, message: str):
        """
        Log test step (visible in pytest report).
        Steps are logged at custom STEP level for high visibility.

        @param message: str - Step description to be logged
        """
        cls._step_counter += 1
        cls._log(LogLevel.STEP, f"Step {cls._step_counter}: {message}")

    @classmethod
    def warning(cls, message: str):
        """
        Log warning message.

        @param message: str - Warning message to be logged
        """
        cls._log(LogLevel.WARNING, message)

    @classmethod
    def error(cls, message: str, exception: Exception = ''):
        """
        Log error message.

        @param message: str - Error message to be logged
        @param exception: exception to be logged
        """
        message += f": {str(exception)}"
        cls._log(LogLevel.ERROR, message)

    @classmethod
    def critical(cls, message: str):
        """
        Log critical message.

        @param message: str - Critical message to be logged
        """
        cls._log(LogLevel.CRITICAL, message)

    @classmethod
    def separator(cls, char: str = '-', length: int = 80) -> None:
        """
        Create a visual separator line in logs without any additional formatting.

        @param char: str - Character to use for the separator line (default: '-')
        @param length: int - Length of the separator line (default: 80)
        """
        separator_line = char * length
        cls._log(LogLevel.EMPTY, separator_line)

    @classmethod
    def reset_step_counter(cls):
        """
        Reset step counter to 0.

        """
        cls._step_counter = 0
