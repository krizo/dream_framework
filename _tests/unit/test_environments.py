import os
from dataclasses import dataclass

import pytest

from core.environments import BaseTestEnvironment

pytestmark = pytest.mark.no_database_plugin


# Example configuration classes for testing
@dataclass
class DatabaseConfig:
    """Example database configuration."""
    server: str
    name: str


@dataclass
class ServiceConfig:
    """Example service configuration."""
    url: str


@dataclass
class AppConfig:
    """Example application configuration built from environment."""
    hostname: str
    api_prefix: str
    ui_base: str
    database: DatabaseConfig
    service_stats: ServiceConfig

    @classmethod
    def from_environment(cls, env_name: str = "development") -> 'AppConfig':
        """Create configuration from environment settings."""
        env = BaseTestEnvironment(env_name)
        return cls(
            hostname=env.get_property("hostname"),
            api_prefix=env.get_property("api_prefix"),
            ui_base=env.get_property("ui_base"),
            database=DatabaseConfig(
                server=env.get_property("database")["server"],
                name=env.get_property("database")["name"]
            ),
            service_stats=ServiceConfig(
                url=env.get_property("service_stats")["url"]
            )
        )


def test_environment_initialization():
    """Test environment initialization with explicit name."""
    env = BaseTestEnvironment("development")
    assert env.environment_name == "development"
    assert str(env) == "development"


def test_environment_from_env_var():
    """Test environment initialization from environment variable."""
    os.environ["TEST_ENVIRONMENT"] = "staging"
    env = BaseTestEnvironment()
    assert env.environment_name == "staging"
    assert str(env) == "staging"


def test_environment_properties():
    """Test property access from environment."""
    env = BaseTestEnvironment("production")

    # Test simple properties
    assert env.get_property("hostname") == "foo.example.com"
    assert env.get_property("api_prefix") == "api.example.com"

    # Test nested properties
    database = env.get_property("database")
    assert database["server"] == "db.example.com"
    assert database["name"] == "nba_players"


def test_environment_not_initialized():
    """Test uninitialized environment behavior."""
    if "TEST_ENVIRONMENT" in os.environ:
        del os.environ["TEST_ENVIRONMENT"]

    env = BaseTestEnvironment()
    assert env.environment_name is None
    assert str(env) == "None"

    with pytest.raises(ValueError, match="Environment not initialized"):
        env.get_property("hostname")


def test_invalid_environment():
    """Test behavior with invalid environment name."""
    with pytest.raises(ValueError, match="Environment 'invalid' not found"):
        BaseTestEnvironment("invalid")


def test_missing_property():
    """Test behavior when accessing missing property."""
    env = BaseTestEnvironment("development")
    with pytest.raises(KeyError, match="Property 'nonexistent' not found"):
        env.get_property("nonexistent")


def test_app_config_creation():
    """Test creating application configuration from environment."""
    # Test with development environment
    dev_config = AppConfig.from_environment("development")
    assert dev_config.hostname == "localhost"
    assert dev_config.database.server == "localhost"
    assert dev_config.database.name == "nba_players_dev"

    # Test with production environment
    prod_config = AppConfig.from_environment("production")
    assert prod_config.hostname == "foo.example.com"
    assert prod_config.database.server == "db.example.com"
    assert prod_config.service_stats.url == "api.example.com/stats/rest/"


def test_different_environments():
    """Test different environments have different configurations."""
    dev_env = BaseTestEnvironment("development")
    prod_env = BaseTestEnvironment("production")
    staging_env = BaseTestEnvironment("staging")

    # Compare hostnames
    assert dev_env.get_property("hostname") == "localhost"
    assert prod_env.get_property("hostname") == "foo.example.com"
    assert staging_env.get_property("hostname") == "staging.example.com"

    # Compare database configurations
    assert dev_env.get_property("database")["server"] == "localhost"
    assert prod_env.get_property("database")["server"] == "db.example.com"
    assert staging_env.get_property("database")["server"] == "db-staging.example.com"
