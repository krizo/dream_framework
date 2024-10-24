import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import yaml

from core.automation_database import AutomationDatabase
from core.logger import Log


@dataclass
class AutomationDatabaseConfig:
    """
    Configuration class for the test automation database.
    This database is used to store test execution data, including test cases,
    their results, metrics, and other test automation artifacts.

    @param url: Database connection URL
    @param dialect: Optional database dialect (e.g., 'mssql', 'oracle', 'mysql')
    """
    url: str
    dialect: Optional[str] = None

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path], config_tag: str = 'automation_db') -> 'AutomationDatabaseConfig':
        """
        Create configuration from YAML file.

        @param yaml_path: Path to YAML configuration file (string or Path object)
        @param config_tag: Configuration section tag to use
        @return: AutomationDatabaseConfig instance
        @raises FileNotFoundError: If config file is not found
        @raises KeyError: If specified configuration tag is not found in config file
        """
        config_path = Path(yaml_path) if isinstance(yaml_path, str) else yaml_path

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with config_path.open('r') as config_file:
            config_data = yaml.safe_load(config_file)

        if config_tag not in config_data:
            raise KeyError(f"Configuration tag '{config_tag}' not found in config file")

        return cls(
            url=config_data[config_tag]['url'],
            dialect=config_data[config_tag].get('dialect')
        )

    @classmethod
    def from_url(cls, url: str, dialect: Optional[str] = None) -> 'AutomationDatabaseConfig':
        """
        Create configuration directly from URL and dialect.

        @param url: Database connection URL
        @param dialect: Optional database dialect
        @return: AutomationDatabaseConfig instance
        """
        return cls(url=url, dialect=dialect)


class AutomationDatabaseManager:
    """
    Class managing database connection through class methods.
    Ensures single database instance throughout the application.
    Uses AutomationDatabaseConfig for database configuration.

    @note: All methods are class methods, no instance creation needed.
    """

    _db_instance: Optional[AutomationDatabase] = None
    _config: Optional[AutomationDatabaseConfig] = None

    @classmethod
    def initialize(cls, connection_string: Optional[str] = None, dialect: Optional[str] = None,
                   config_path: Optional[Union[str, Path]] = None, config_tag: str = 'automation_db') -> None:
        """
        Initialize database connection using either direct connection string or configuration file.

        @param connection_string: Optional direct database connection string
        @param dialect: Optional database dialect
        @param config_path: Optional path to configuration file
        @param config_tag: Configuration section tag to use (default: 'automation_db')
        @raises FileNotFoundError: If config file is specified but not found
        @raises KeyError: If config file is specified but tag is not found
        """
        if cls._db_instance is None:
            if connection_string is not None:
                # Use direct connection string
                cls._config = AutomationDatabaseConfig.from_url(connection_string, dialect)
            else:
                # Use configuration file
                if config_path is None:
                    config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
                cls._config = AutomationDatabaseConfig.from_yaml(config_path, config_tag)

            cls._db_instance = AutomationDatabase(cls._config.url, cls._config.dialect)
            cls._db_instance.create_tables()

    @classmethod
    def get_database(cls) -> AutomationDatabase:
        """
        Get database instance. Initializes database with default configuration if not initialized.

        @return: AutomationDatabase instance
        @raises RuntimeError: If database is not initialized and no default configuration exists
        """
        if cls._db_instance is None:
            cls.initialize()
        return cls._db_instance

    @classmethod
    def get_config(cls) -> Optional[AutomationDatabaseConfig]:
        """
        Get current database configuration.

        @return: Current AutomationDatabaseConfig or None if not initialized
        """
        return cls._config

    @classmethod
    def close(cls) -> None:
        """
        Close database connection and cleanup resources.
        """
        cls._db_instance = None
        cls._config = None

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if database is initialized.

        @return: True if database is initialized, False otherwise
        """
        return cls._db_instance is not None

    @classmethod
    def remove(cls) -> None:
        """
        Remove database file if it's a file-based database.
        Used primarily for testing to ensure clean state.

        @note: Only removes file if using file-based database (e.g., SQLite)
        """
        if cls._config and cls._config.url.startswith('sqlite:///'):
            # Extract file path from SQLite URL by removing 'sqlite:///'
            db_path = cls._config.url.replace('sqlite:///', '')

            # Handle relative and absolute paths
            if db_path and db_path != ':memory:':
                try:
                    if os.path.exists(db_path):
                        os.remove(db_path)
                        Log.step(f"Removed database file: {db_path}")
                except Exception as e:
                    Log.step(f"Warning: Could not remove database file {db_path}: {str(e)}")
        cls.close()
