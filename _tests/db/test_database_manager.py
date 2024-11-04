import tempfile
from pathlib import Path

import pytest
import yaml

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager, AutomationDatabaseConfig

pytestmark = pytest.mark.no_database_plugin


@pytest.fixture
def temp_config_file():
    """
    Create temporary config file with test database configuration.

    @return: Path to temporary config file
    """
    config = {
        'automation_db': {
            'url': 'sqlite:///:memory:',
            'dialect': None
        },
        'test_db': {
            'url': 'sqlite:///:memory:',
            'dialect': 'mysql'
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = Path(f.name)  # Konwertujemy na Path

    yield config_path

    if config_path.exists():  # Sprawdzamy czy plik istnieje przed usunięciem
        config_path.unlink()


@pytest.fixture(autouse=True)
def reset_manager():
    """
    Reset DatabaseManager state before and after each test.

    @return: None
    """
    AutomationDatabaseManager.close()
    yield
    AutomationDatabaseManager.close()


def test_initialization_with_connection_string():
    """Test database manager initialization with direct connection string."""
    connection_string = "sqlite:///:memory:"
    AutomationDatabaseManager.initialize(connection_string=connection_string)

    assert AutomationDatabaseManager.is_initialized()

    db = AutomationDatabaseManager.get_database()
    assert isinstance(db, AutomationDatabase)
    assert db.engine.url.database == ':memory:'

    config = AutomationDatabaseManager.get_config()
    assert config.url == connection_string
    assert config.dialect is None


def test_initialization_with_config_file(temp_config_file):
    """
    Test database manager initialization from config file.

    @param temp_config_file: Temporary config file fixture
    """
    AutomationDatabaseManager.initialize(config_path=temp_config_file)

    assert AutomationDatabaseManager.is_initialized()

    db = AutomationDatabaseManager.get_database()
    assert isinstance(db, AutomationDatabase)

    config = AutomationDatabaseManager.get_config()
    assert config.url == 'sqlite:///:memory:'
    assert config.dialect is None


def test_initialization_with_custom_tag(temp_config_file):
    """
    Test initialization with custom config tag.

    @param temp_config_file: Temporary config file fixture
    """
    AutomationDatabaseManager.initialize(
        config_path=temp_config_file,
        config_tag='test_db'
    )

    config = AutomationDatabaseManager.get_config()
    assert config.url == 'sqlite:///:memory:'
    assert config.dialect == 'mysql'


def test_singleton_behavior():
    """Test singleton behavior of database manager."""
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db1 = AutomationDatabaseManager.get_database()
    db2 = AutomationDatabaseManager.get_database()

    assert db1 is db2, "Should return same database instance"

    # Second initialization should not create new instance
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db3 = AutomationDatabaseManager.get_database()
    assert db1 is db3, "Should preserve existing instance"


def test_close_and_reinitialize():
    """Test closing and reinitializing database connection."""
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    original_db = AutomationDatabaseManager.get_database()

    AutomationDatabaseManager.close()
    assert not AutomationDatabaseManager.is_initialized()
    assert AutomationDatabaseManager.get_config() is None

    # Reinitialize with new connection
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    new_db = AutomationDatabaseManager.get_database()

    assert new_db is not original_db, "Should create new instance after close"
    assert AutomationDatabaseManager.is_initialized()


def test_automatic_initialization():
    """Test automatic initialization when getting database."""
    db = AutomationDatabaseManager.get_database()
    assert db is not None
    assert AutomationDatabaseManager.is_initialized()

    config = AutomationDatabaseManager.get_config()
    assert config is not None


def test_config_validation(temp_config_file):
    """
    Test configuration validation.

    @param temp_config_file: Temporary config file fixture
    """
    # Invalid config file path
    with pytest.raises(FileNotFoundError):
        AutomationDatabaseManager.initialize(config_path=Path("nonexistent.yaml"))

    # Invalid config tag
    with pytest.raises(KeyError):
        AutomationDatabaseManager.initialize(
            config_path=temp_config_file,  # teraz temp_config_file to Path z fixture'a
            config_tag='invalid_tag'
        )


def test_database_removal():
    """Test database file removal for file-based databases."""
    # Create temp database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    connection_string = f"sqlite:///{db_path}"
    AutomationDatabaseManager.initialize(connection_string)

    assert Path(db_path).exists()

    AutomationDatabaseManager.remove()
    assert not Path(db_path).exists()
    assert not AutomationDatabaseManager.is_initialized()


def test_config_object_creation():
    """Test AutomationDatabaseConfig object creation."""
    # From URL
    config = AutomationDatabaseConfig.from_url(
        "sqlite:///test.db",
        dialect="mysql"
    )
    assert config.url == "sqlite:///test.db"
    assert config.dialect == "mysql"

    # From YAML
    yaml_content = {
        'automation_db': {
            'url': 'sqlite:///:memory:',
            'dialect': 'postgres'
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(yaml_content, f)
        config = AutomationDatabaseConfig.from_yaml(f.name)
        assert config.url == 'sqlite:///:memory:'
        assert config.dialect == 'postgres'
