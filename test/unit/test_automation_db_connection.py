"""Tests for database connectivity."""
import pytest

from core.automation_database_manager import AutomationDatabaseManager
from core.test_case import TestCase
from models.test_case_model import TestCaseModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_run_model import TestRunModel


@pytest.fixture(scope="module")
def db_connection():
    yield AutomationDatabaseManager.get_database()


def test_test_case_creation(db_connection):
    """Test creating and retrieving a test case."""
    # Create a unique test case for this test
    import uuid
    unique_id = str(uuid.uuid4())
    test_name = f"Connectivity Test {unique_id}"

    # Create test case
    test_case = TestCase(
        name=test_name,
        description="Test database connectivity",
        test_suite="Database Tests",
        scope="Unit",
        component="Database"
    )
    test_case.set_test_location("tests/test_db_connectivity.py", "test_test_case_creation")

    # Save to database
    test_case_id = db_connection.insert_test_case(test_case)
    assert test_case_id is not None, "Failed to insert test case"

    # Retrieve from database
    retrieved_case = db_connection.fetch_test_case(test_case_id)
    assert retrieved_case is not None, "Failed to retrieve test case"
    assert retrieved_case.name == test_name, "Retrieved test case has incorrect name"
    assert retrieved_case.scope == "Unit", "Retrieved test case has incorrect scope"
    assert retrieved_case.component == "Database", "Retrieved test case has incorrect component"

    # Clean up - normally not needed, but good for test isolation
    with db_connection.session_scope() as session:
        session.query(TestCaseModel).filter_by(id=test_case_id).delete()


def test_query_performance(db_connection):
    """Test database query performance."""
    import time

    # Measure query time
    start_time = time.time()
    with db_connection.session_scope() as session:
        # Query all models to test basic performance
        test_cases_count = session.query(TestCaseModel).count()
        test_runs_count = session.query(TestRunModel).count()
        test_execs_count = session.query(TestExecutionRecordModel).count()

    end_time = time.time()
    query_time = end_time - start_time

    # Log counts and time
    print(f"Found {test_cases_count} test cases")
    print(f"Found {test_runs_count} test runs")
    print(f"Found {test_execs_count} test executions")
    print(f"Query time: {query_time:.4f} seconds")

    # Basic performance assertion - should be quick for small datasets
    # Adjust threshold based on your environment and dataset size
    assert query_time < 2.0, f"Query performance is slow: {query_time:.4f} seconds"


def test_transaction_rollback(db_connection):
    """Test that transactions can be rolled back."""
    # Create a test case that we'll roll back
    test_case = TestCase(
        name="Transaction Rollback Test",
        description="This test case should not be committed",
        test_suite="Database Tests",
        scope="Unit",
        component="Database"
    )
    test_case.set_test_location("tests/test_db_connectivity.py", "test_transaction_rollback")

    # Get initial count
    with db_connection.session_scope() as session:
        initial_count = session.query(TestCaseModel).count()

    # Start a transaction and roll it back
    try:
        with db_connection.session_scope() as session:
            # Convert to model and add to session
            model = test_case.to_model()
            session.add(model)
            session.flush()  # This assigns an ID but doesn't commit

            # Get ID for verification
            test_case_id = model.id
            assert test_case_id is not None, "Test case didn't get an ID"

            # Intentionally raise an exception to trigger rollback
            raise ValueError("Intentional rollback")
    except ValueError:
        # Expected exception, should trigger rollback
        pass

    # Verify the test case wasn't committed
    with db_connection.session_scope() as session:
        final_count = session.query(TestCaseModel).count()
        assert final_count == initial_count, "Transaction was not rolled back"

