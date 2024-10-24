import pytest

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager


@pytest.fixture(autouse=True)
def reset_database_manager():
    """
    Fixture to reset DatabaseManager before each test.
    """
    AutomationDatabaseManager.close()
    yield
    AutomationDatabaseManager.close()


def test_single_database_instance():
    """
    Test that DatabaseManager maintains single database instance.
    """
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    db1 = AutomationDatabaseManager.get_database()
    db2 = AutomationDatabaseManager.get_database()

    assert db1 is db2
    assert AutomationDatabaseManager.is_initialized()


def test_database_initialization():
    """
    Test database initialization and retrieval.
    """
    assert not AutomationDatabaseManager.is_initialized()
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    assert AutomationDatabaseManager.is_initialized()

    db = AutomationDatabaseManager.get_database()
    assert isinstance(db, AutomationDatabase)


def test_multiple_initialization():
    """
    Test that multiple initializations don't create new database instances.
    """
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    first_db = AutomationDatabaseManager.get_database()

    # Second initialization should not create new instance
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    second_db = AutomationDatabaseManager.get_database()

    assert first_db is second_db


def test_close_and_reinitialize():
    """
    Test closing and reinitializing database connection.
    """
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    first_db = AutomationDatabaseManager.get_database()

    AutomationDatabaseManager.close()
    assert not AutomationDatabaseManager.is_initialized()

    # After close, should be able to initialize again
    AutomationDatabaseManager.initialize('sqlite:///:memory:')
    second_db = AutomationDatabaseManager.get_database()

    assert first_db is not second_db
    assert AutomationDatabaseManager.is_initialized()


def test_dialect_configuration():
    """
    Test if database is properly configured with different dialects.
    """
    AutomationDatabaseManager.initialize('sqlite:///:memory:', dialect='mysql')
    mysql_db = AutomationDatabaseManager.get_database()
    assert mysql_db.dialect == 'mysql'

    AutomationDatabaseManager.close()

    AutomationDatabaseManager.initialize('sqlite:///:memory:', dialect='postgresql')
    postgresql_db = AutomationDatabaseManager.get_database()
    assert postgresql_db.dialect == 'postgresql'
