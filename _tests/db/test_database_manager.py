"""Tests for database manager functionality."""
import tempfile
from pathlib import Path

import pytest
import yaml

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager, AutomationDatabaseConfig
from core.test_run import TestRun


@pytest.fixture
def temp_config_file():
    """Create temporary config file with test database configuration."""
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
        config_path = Path(f.name)

    yield config_path

    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def preserve_test_run(request):
    """Preserve TestRun instance during database reset."""
    test_run = None
    if TestRun.get_instance():
        test_run = TestRun.get_instance()

    yield

    if test_run:
        TestRun._instance = test_run


@pytest.fixture(autouse=True)
def reset_manager(preserve_test_run):
    """Reset DatabaseManager state before and after each test."""
    AutomationDatabaseManager.close()
    yield


def ensure_test_run():
    """Ensure TestRun instance exists."""
    if not TestRun.get_instance():
        TestRun.initialize(owner="test_user")


def test_initialization_with_connection_string(preserve_test_run):
    """Test database manager initialization with direct connection string."""
    ensure_test_run()

    connection_string = "sqlite:///:memory:"
    AutomationDatabaseManager.initialize(connection_string=connection_string)

    assert AutomationDatabaseManager.is_initialized()

    db = AutomationDatabaseManager.get_database()
    assert isinstance(db, AutomationDatabase)
    assert db.engine.url.database == ':memory:'

    config = AutomationDatabaseManager.get_config()
    assert config.url == connection_string
    assert config.dialect is None


def test_initialization_with_config_file(temp_config_file, preserve_test_run):
    """Test database manager initialization from config file."""
    ensure_test_run()

    AutomationDatabaseManager.initialize(config_path=temp_config_file)

    assert AutomationDatabaseManager.is_initialized()

    db = AutomationDatabaseManager.get_database()
    assert isinstance(db, AutomationDatabase)

    config = AutomationDatabaseManager.get_config()
    assert config.url == 'sqlite:///:memory:'
    assert config.dialect is None


def test_initialization_with_custom_tag(temp_config_file, preserve_test_run):
    """Test initialization with custom config tag."""
    ensure_test_run()

    AutomationDatabaseManager.initialize(
        config_path=temp_config_file,
        config_tag='test_db'
    )

    config = AutomationDatabaseManager.get_config()
    assert config.url == 'sqlite:///:memory:'
    assert config.dialect == 'mysql'


def test_singleton_behavior(preserve_test_run):
    """Test singleton behavior of database manager."""
    ensure_test_run()

    from sqlalchemy import inspect

    # Initialize first instance
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db1 = AutomationDatabaseManager.get_database()
    db2 = AutomationDatabaseManager.get_database()

    # Should return same instance
    assert db1 is db2

    # Second initialization should keep existing instance
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db3 = AutomationDatabaseManager.get_database()
    assert db1 is db3

    # Verify tables are created only once
    inspector = inspect(db1.engine)
    table_count_1 = len(inspector.get_table_names())
    db1.create_tables()
    table_count_2 = len(inspector.get_table_names())
    assert table_count_1 == table_count_2


def test_close_and_reinitialize(preserve_test_run):
    """Test closing and reinitializing database connection."""
    ensure_test_run()

    # Initial setup
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    original_db = AutomationDatabaseManager.get_database()

    # Close and verify state
    AutomationDatabaseManager.close()
    assert not AutomationDatabaseManager.is_initialized()
    assert AutomationDatabaseManager.get_config() is None

    # Reinitialize with new connection
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    new_db = AutomationDatabaseManager.get_database()

    # Should be different instances
    assert new_db is not original_db
    assert AutomationDatabaseManager.is_initialized()


def test_automatic_initialization(preserve_test_run):
    """Test automatic initialization when getting database."""
    ensure_test_run()

    # Get database without explicit initialization
    db = AutomationDatabaseManager.get_database()
    assert db is not None
    assert AutomationDatabaseManager.is_initialized()

    # Should create default configuration
    config = AutomationDatabaseManager.get_config()
    assert config is not None
    assert config.url is not None


@pytest.mark.no_execution_record
def test_database_creation(preserve_test_run):
    """Test database file creation for file-based databases."""
    ensure_test_run()

    from sqlalchemy import inspect

    # Create temp database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    connection_string = f"sqlite:///{db_path}"
    AutomationDatabaseManager.initialize(connection_string)

    # Verify file exists and tables are created
    assert Path(db_path).exists()
    db = AutomationDatabaseManager.get_database()
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    required_tables = {'test_cases', 'test_execution_records', 'test_runs', 'custom_metrics', 'steps'}
    assert required_tables.issubset(set(tables))

    # Cleanup
    AutomationDatabaseManager.remove()
    assert not Path(db_path).exists()


@pytest.mark.no_execution_record
def test_error_handling(temp_config_file, preserve_test_run):
    """Test error handling in database operations."""
    ensure_test_run()

    # Invalid config file
    with pytest.raises(FileNotFoundError):
        AutomationDatabaseManager.initialize(config_path=Path("nonexistent.yaml"))

    # Invalid config tag
    with pytest.raises(KeyError):
        AutomationDatabaseManager.initialize(
            config_path=temp_config_file,
            config_tag='invalid_tag'
        )

    # Invalid connection string
    with pytest.raises(Exception):
        AutomationDatabaseManager.initialize('invalid://connection:string')


@pytest.mark.no_execution_record
def test_config_validation(preserve_test_run):
    """Test database configuration validation."""
    ensure_test_run()

    # Test empty URL
    with pytest.raises(ValueError):
        AutomationDatabaseConfig(url="")

    # Test None URL
    with pytest.raises(ValueError):
        AutomationDatabaseConfig(url=None)

    # Test valid config
    config = AutomationDatabaseConfig(url="sqlite:///:memory:", dialect="mysql")
    assert config.url == "sqlite:///:memory:"
    assert config.dialect == "mysql"


@pytest.mark.no_execution_record
def test_database_schema_management(preserve_test_run):
    """Test database schema management."""
    ensure_test_run()

    from sqlalchemy import inspect

    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db = AutomationDatabaseManager.get_database()

    # First creation
    db.create_tables()
    inspector = inspect(db.engine)
    tables1 = set(inspector.get_table_names())

    # Second creation should not modify schema
    db.create_tables()
    tables2 = set(inspector.get_table_names())

    assert tables1 == tables2

    # Verify required tables
    required_tables = {'test_cases', 'test_execution_records', 'test_runs', 'custom_metrics', 'steps'}
    assert required_tables.issubset(tables1)

    # Verify table relationships (key tables)
    test_case_fks = inspector.get_foreign_keys('test_execution_records')
    assert any(fk['referred_table'] == 'test_cases' for fk in test_case_fks)
    assert any(fk['referred_table'] == 'test_runs' for fk in test_case_fks)
