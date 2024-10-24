import os
import tempfile
import time

import pytest

from core.automation_database_manager import AutomationDatabaseManager
from core.test_case import TestCase


class LoginTestCase(TestCase):
    def __init__(self):
        super().__init__(
            name="Login Test",
            description="Verify user login functionality",
            test_suite="authentication_tests",
            component="Authentication",
            scope="Integration"
        )


@pytest.fixture(scope="session")
def db_path():
    """
    Create a temporary database file.

    @return: Path to temporary SQLite database
    """
    # Create a temporary file
    temp_dir = tempfile.gettempdir()
    db_file = os.path.join(temp_dir, 'test_automation.db')

    # Ensure clean state
    if os.path.exists(db_file):
        os.remove(db_file)

    yield f"sqlite:///{db_file}"

    # Cleanup after all tests
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Fixture to setup and teardown database for all tests.

    @note: scope="session" ensures database is initialized once for all tests
    @note: autouse=True ensures this fixture runs automatically
    """
    # Uses default configuration from database_config.yaml
    AutomationDatabaseManager.initialize()
    yield
    AutomationDatabaseManager.remove()


@pytest.fixture
def login_test_case(request):
    """
    Fixture providing specific TestCase for login tests.

    @param request: pytest request object
    @return: LoginTestCase instance
    """
    print("\nCreating login test case")
    test_case = LoginTestCase()
    yield test_case

    print(f"\nIn fixture teardown - test case ID: {test_case.id}")
    retrieved_case = AutomationDatabaseManager.get_database().fetch_test_case(test_case_id=test_case.id)
    print(f"Retrieved case is None: {retrieved_case is None}")
    if retrieved_case:
        print(f"Retrieved case details: {retrieved_case.test_name}")
    assert retrieved_case is not None, f"Test case with ID {test_case.id} not found in database"


def test_user_login(login_test_case):
    """
    Test using custom TestCase fixture.
    The plugin will automatically handle persistence.

    @param login_test_case: LoginTestCase fixture
    """
    print(f"\nIn test - test case ID before metric: {login_test_case.id}")
    login_test_case.add_custom_metric("user_id", "12345")
    print(f"Test case ID after metric: {login_test_case.id}")
    time.sleep(1)
