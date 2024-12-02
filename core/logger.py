"""Core logging module."""
import logging
import logging.config
from enum import Enum
from typing import Optional

# Custom log levels
STEP_LEVEL = 35
CONSOLE_LEVEL = 15
EMPTY_LEVEL = 11
logging.addLevelName(STEP_LEVEL, "STEP")
logging.addLevelName(CONSOLE_LEVEL, "CONSOLE")
logging.addLevelName(EMPTY_LEVEL, "EMPTY")


class LogLevel(Enum):
    """Enumeration of available log levels."""
    EMPTY = EMPTY_LEVEL
    DEBUG = logging.DEBUG
    CONSOLE = CONSOLE_LEVEL
    INFO = logging.INFO
    STEP = STEP_LEVEL
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class MultiFormatter(logging.Formatter):
    """Formatter that applies different formats based on log level."""

    def __init__(self):
        super().__init__('%(asctime)s | %(levelname)-8s | %(message)s',
                         datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record):
        if record.levelno == EMPTY_LEVEL:
            return record.getMessage()
        return super().format(record)


class EmptyFormatter(logging.Formatter):
    """Formatter for empty messages without any additional formatting."""

    def format(self, record):
        return record.getMessage()


class ConsoleFilter(logging.Filter):
    """Filter allowing console messages to pass through."""

    def filter(self, record):
        return record.levelno >= CONSOLE_LEVEL


class FileFilter(logging.Filter):
    """Filter allowing file messages to pass through."""

    def filter(self, record):
        return record.levelno != CONSOLE_LEVEL


class Log:
    """Static logger class providing centralized logging functionality."""

    _instance: Optional[logging.Logger] = None
    _initialized: bool = False
    _step_counter: int = 0

    @classmethod
    def _initialize(cls):
        """Initialize logger with proper configuration."""
        if cls._initialized:
            return

        logger = logging.getLogger("TestLogger")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(MultiFormatter())
        console_handler.setLevel(logging.DEBUG)
        console_handler.addFilter(ConsoleFilter())
        logger.addHandler(console_handler)

        logger.propagate = False
        cls._instance = logger
        cls._initialized = True

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get or create logger instance."""
        if not cls._initialized:
            cls._initialize()
        return cls._instance

    @classmethod
    def reconfigure_file_handler(cls, log_file: str):
        """Configure file handler with new log file."""
        logger = cls.get_logger()

        # Remove old file handlers
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.removeHandler(handler)

        # Add new file handler
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(MultiFormatter())
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(FileFilter())
        logger.addHandler(file_handler)

    @classmethod
    def reset(cls, preserve_handlers=None):
        """Reset logger to initial state."""
        if cls._instance:
            preserved = []
            if preserve_handlers:
                preserved = [h for h in cls._instance.handlers if h in preserve_handlers]

            for handler in cls._instance.handlers[:]:
                if handler not in preserved:
                    handler.close()
                    cls._instance.removeHandler(handler)

            cls._instance.handlers = preserved

        cls._step_counter = 0

    @classmethod
    def _log(cls, level: LogLevel, message: str, *args, **kwargs):
        """Internal logging method."""
        logger = cls.get_logger()
        logger.log(level.value, message, *args, **kwargs)

    @classmethod
    def console(cls, message: str):
        """Log console message."""
        cls._log(LogLevel.CONSOLE, message)

    @classmethod
    def debug(cls, message: str):
        """Log debug message."""
        cls._log(LogLevel.DEBUG, message)

    @classmethod
    def info(cls, message: str):
        """Log info message."""
        cls._log(LogLevel.INFO, message)

    @classmethod
    def step(cls, message: str):
        """Log test step."""
        cls._step_counter += 1
        cls._log(LogLevel.STEP, message)

    @classmethod
    def warning(cls, message: str):
        """Log warning message."""
        cls._log(LogLevel.WARNING, message)

    @classmethod
    def error(cls, message: str):
        """Log error message."""
        cls._log(LogLevel.ERROR, message)

    @classmethod
    def critical(cls, message: str):
        """Log critical message."""
        cls._log(LogLevel.CRITICAL, message)

    @classmethod
    def separator(cls, char: str = '-', length: int = 80) -> None:
        """Create a visual separator line in logs."""
        separator_line = char * length
        cls._log(LogLevel.EMPTY, separator_line)

    @classmethod
    def reset_step_counter(cls):
        """Reset step counter to 0."""
        cls._step_counter = 0

    @classmethod
    def switch_log_file(cls, log_file: str):
        """
        Switch logging to a different file.
        Preserves handlers other than file handler.
        """
        logger = cls.get_logger()

        other_handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler)]
        logger.handlers.clear()

        for handler in other_handlers:
            logger.addHandler(handler)

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(MultiFormatter())
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(FileFilter())
        logger.addHandler(file_handler)
