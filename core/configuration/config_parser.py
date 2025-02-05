"""Base configuration parser module."""
import ast
import configparser
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, ClassVar, Optional, TypeVar, Generic

from core.logger import Log

# Generic type definition
T = TypeVar('T')


class ConfigParser(Generic[T]):
    """
    Base parser for framework configuration files.
    Generic base class for specific configuration sections.
     T determines the type of configuration settings this parser handles.
    """

    _instance: ClassVar[Optional[configparser.ConfigParser]] = None
    _config_path: ClassVar[Optional[Path]] = None

    SECTION_NAME: str = ""  # To be overridden by subclasses

    @classmethod
    def _get_instance(cls) -> configparser.ConfigParser:
        """
        Get or create singleton instance of ConfigParser.

        @return: ConfigParser instance
        """
        if cls._instance is None:
            cls._instance = configparser.ConfigParser(
                interpolation=configparser.ExtendedInterpolation()
            )

            if cls._config_path is None:
                cls._config_path = Path(__file__).parent.parent.parent / 'config' / 'config.ini'

            if cls._config_path.exists():
                cls._instance.read(str(cls._config_path))
            else:
                Log.warning(f"Config file not found at {cls._config_path}")

        return cls._instance

    @classmethod
    def set_config_path(cls, path: Path) -> None:
        """Set custom configuration file path and reset cache."""
        cls._config_path = path
        cls._instance = None
        cls.clear_cache()

    @classmethod
    @lru_cache(maxsize=32)
    def get_value(cls, key: str, fallback: Any = None) -> Any:
        """Get value from configuration with type conversion and caching."""
        config = cls._get_instance()
        try:
            if not config.has_section(cls.SECTION_NAME) or not config.has_option(cls.SECTION_NAME, key):
                return fallback

            value_str = config.get(cls.SECTION_NAME, key)

            # Special handling for boolean values
            if isinstance(fallback, bool):
                return value_str.lower() == 'true'

            try:
                return ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                return value_str

        except Exception as e:
            Log.error(f"Error getting config value {cls.SECTION_NAME}.{key}: {str(e)}")
            return fallback

        except Exception as e:
            Log.error(f"Error getting config value {cls.SECTION_NAME}.{key}: {str(e)}")
            return fallback

    @classmethod
    @lru_cache(maxsize=8)
    def get_section(cls) -> Dict[str, Any]:
        """Get all key-value pairs from the section."""
        config = cls._get_instance()
        if not config.has_section(cls.SECTION_NAME):
            return {}

        return {
            key: cls.get_value(key)
            for key in config.options(cls.SECTION_NAME)
        }

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached values."""
        cls.get_value.cache_clear()
        cls.get_section.cache_clear()

    @classmethod
    def reload(cls) -> None:
        """Reload configuration and clear cache."""
        cls._instance = None
        cls.clear_cache()
