import os
import tempfile
from typing import Generator

import pytest

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager
from core.test_case import TestCase
from models.base_model import Base

DIALECTS = {
    'mssql': {
        'date_format': '%Y-%m-%d %H:%M:%S.%f',
        'max_identifier_length': 128
    },
    'oracle': {
        'date_format': '%Y-%m-%d %H:%M:%S.%f',
        'max_identifier_length': 30
    },
    'mysql': {
        'date_format': '%Y-%m-%d %H:%M:%S.%f',
        'max_identifier_length': 64
    },
    'postgresql': {
        'date_format': '%Y-%m-%d %H:%M:%S.%f',
        'max_identifier_length': 63
    }
}


@pytest.fixture(scope="session")
def db_path() -> Generator[str, None, None]:
    """
    Create temporary database file path.

    @yield: Path to temporary SQLite database
    """
    temp_dir = tempfile.gettempdir()
    db_file = os.path.join(temp_dir, 'test_automation.db')

    if os.path.exists(db_file):
        os.remove(db_file)

    yield f"sqlite:///{db_file}"

    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="function")
def sqlite_db() -> AutomationDatabase:
    """
    Provide clean SQLite database for testing.
    Recreates all tables for each test to ensure clean state.

    @return: AutomationDatabase instance
    """
    # Create new in-memory database
    test_db = AutomationDatabase('sqlite:///:memory:')

    # Drop all tables if they exist
    Base.metadata.drop_all(test_db.engine)

    # Create fresh tables
    Base.metadata.create_all(test_db.engine)

    return test_db


@pytest.fixture(params=DIALECTS.keys())
def emulated_odbc_db(request) -> AutomationDatabase:
    """
    Provide database instance emulating different SQL dialects.

    @param request: Pytest request with dialect parameter
    @return: AutomationDatabase instance configured for specific dialect
    """
    dialect = request.param
    test_db = AutomationDatabase('sqlite:///:memory:', dialect=dialect)
    test_db.create_tables()

    test_db.Session.remove()

    yield test_db

    test_db.Session.remove()
    Base.metadata.drop_all(test_db.engine)
    AutomationDatabaseManager.close()


@pytest.fixture(scope="session")
def real_db() -> AutomationDatabase:
    """
    Provide connection to real database configured in database_config.yaml under 'automation_db' tag.
    This fixture uses the actual database, not an in-memory one.

    @return: AutomationDatabase instance connected to real database
    """
    # Initialize database manager with default config (uses automation_db from yaml)
    AutomationDatabaseManager.initialize()
    db = AutomationDatabaseManager.get_database()

    yield db

    # Don't drop tables or cleanup data in real database
    AutomationDatabaseManager.close()


class SampleTestCase(TestCase):
    """Sample test case class for testing."""

    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.get('name', "Sample Test"),
            description=kwargs.get('description', "Sample test description"),
            test_suite=kwargs.get('test_suite', "Sample Suite"),
            scope=kwargs.get('scope', "integration"),
            component=kwargs.get('component', "database")
        )


@pytest.fixture
def base_test_case() -> TestCase:
    """
    Provide basic TestCase instance.

    @return: TestCase instance with default values
    """
    return SampleTestCase()


@pytest.fixture
def dummy_test_case():
    """
    Provide minimal TestCase instance for testing.
    Uses only required properties.

    @return: TestCase instance with minimal configuration
    """

    class DummyTestCase(TestCase):
        @property
        def test_suite(self) -> str:
            return "Dummy Suite"

    return DummyTestCase(
        name="Dummy Test",
        description="Just a dummy test",
        scope="Unit",
        component="API"
    )
