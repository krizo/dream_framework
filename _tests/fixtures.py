import os
import tempfile
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Generator, Any
from unittest.mock import patch

import pytest

from core.automation_database import AutomationDatabase
from core.common_paths import ROOT_DIR
from core.frontend.browser_manager import BrowserManager
from core.test_case import TestCase
from core.test_run import TestRun
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
def sqlite_db() -> "AutomationDatabase":
    """
    Provide clean SQLite database for testing.
    Recreates all tables for each test to ensure clean state.

    @return: AutomationDatabase instance
    """
    # Create new in-memory database
    from core.automation_database import AutomationDatabase
    test_db = AutomationDatabase('sqlite:///:memory:')

    # Drop all tables if they exist
    Base.metadata.drop_all(test_db.engine)

    # Create fresh tables
    Base.metadata.create_all(test_db.engine)

    return test_db


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


@pytest.fixture(autouse=True)
def clean_test_run():
    """Reset TestRun singleton before and after each test."""
    TestRun.reset()
    yield
    TestRun.reset()


@pytest.fixture
def active_test_run(clean_test_run, test_db):
    """Fixture providing active TestRun instance."""
    with patch('core.automation_database_manager.AutomationDatabaseManager.get_database', return_value=test_db):
        test_run = TestRun.initialize(owner="test_user")
        yield test_run


@pytest.fixture
def test_db():
    """Create in-memory database for testing."""
    db = AutomationDatabase('sqlite:///:memory:')
    db.create_tables()
    yield db


@pytest.fixture(scope="session")
def server_url() -> Generator[str, Any, None]:
    """Start local server with test page."""
    page_name = "example_html_page.html"
    test_page = ROOT_DIR / '_tests' / 'frontend' / page_name

    os.chdir(test_page.parent)

    server = HTTPServer(('localhost', 0), SimpleHTTPRequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://localhost:{server.server_port}/{page_name}"

    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def browser():
    """Initialize and clean up browser."""
    browser = BrowserManager.initialize()
    yield browser
    BrowserManager.close()


@pytest.fixture
def page(server_url, browser):
    """Load test page."""
    browser.get_driver().get(server_url)
    return browser.get_driver()
