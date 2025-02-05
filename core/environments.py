import os
from pathlib import Path
from typing import Optional, Any, Dict

import yaml


class TestEnvironment:
    """
    Class representing test environment configuration.
    Provides access to environment-specific properties defined in YAML configuration.

    Configuration file location:
    The configuration file must be located at 'config/environments.yml' relative to the
    framework's root directory. Example structure:

    my_project/
    ├── config/
    │   └── environments.yml
    ├── core/
    │   └── environments.py
    └── tests/
        └── test_environments.py

    Configuration file format:
    The YAML file should contain environment configurations as top-level keys:

    ```yaml
    production:
      hostname: foo.example.com
      api_prefix: api.example.com
      ui_base: https://www.example.com
      database:
        server: db.example.com
        name: nba_players
      service_stats:
        url: api.example.com/stats/rest/

    staging:
      hostname: staging.example.com
      api_prefix: api-staging.example.com
      database:
        server: db-staging.example.com
        name: nba_players_staging
    ```

    Usage examples:
        # Direct initialization
        env = TestEnvironment("production")
        hostname = env.get_property("hostname")
        db_config = env.get_property("database")
        db_name = db_config["name"]

        # Using environment variable
        # export TEST_ENVIRONMENT=staging
        env = TestEnvironment()  # Will use "staging" from TEST_ENVIRONMENT
        api_prefix = env.get_property("api_prefix")

        # Creating configuration classes
        @dataclass
        class DbConfig:
            server: str
            name: str

        class MyEnvironmentConfig:
            def __init__(self, env_name: str):
                env = TestEnvironment(env_name)
                db_data = env.get_property("database")
                self.db = DbConfig(
                    server=db_data["server"],
                    name=db_data["name"]
                )

    Note:
        The configuration file should not contain sensitive data like passwords,
        tokens, or private keys. These is managed by Credentials class.
    """

    def __init__(self, environment_name: Optional[str] = None):
        """
        Initialize environment configuration.

        @param environment_name: Name of the environment to load
            If not provided, tries to get from TEST_ENVIRONMENT env variable
        """
        self.environment_name = environment_name or os.getenv("TEST_ENVIRONMENT")
        self._config: Optional[Dict[str, Any]] = None

        if self.environment_name:
            self._load_configuration()

    def _load_configuration(self) -> None:
        """
        Load environment configuration from YAML file.
        Configuration file is expected at config/environments.yml
        """
        config_path = Path(__file__).parent.parent / 'config' / 'environments.yml'

        if not config_path.exists():
            raise FileNotFoundError(f"Environment configuration not found at: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as config_file:
            all_configs = yaml.safe_load(config_file)

        if self.environment_name not in all_configs:
            raise ValueError(f"Environment '{self.environment_name}' not found in configuration")

        self._config = all_configs[self.environment_name]

    def get_property(self, property_name: str) -> Any:
        """
        Get environment property by name.

        @param property_name: Name of the property to retrieve
        @return: Property value from configuration
        @raises: KeyError if property not found
        @raises: ValueError if environment not initialized
        """
        if not self._config:
            raise ValueError("Environment not initialized")

        if property_name not in self._config:
            raise KeyError(f"Property '{property_name}' not found in environment configuration")

        return self._config[property_name]

    def __str__(self) -> str:
        return self.environment_name if self.environment_name else "None"
