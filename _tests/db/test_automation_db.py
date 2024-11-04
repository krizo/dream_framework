from datetime import datetime, timedelta

import pytest
from sqlalchemy import inspect

from core.automation_database import AutomationDatabase
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult
from models.test_case_model import TestCaseModel

pytestmark = pytest.mark.no_database_plugin


@pytest.fixture
def test_db(tmp_path):
    """
    Provide clean SQLite database for each test.

    @param tmp_path: pytest temporary directory fixture
    @return: AutomationDatabase instance
    """
    db_file = tmp_path / "test.db"
    db = AutomationDatabase(f"sqlite:///{db_file}")
    db.create_tables()
    return db


@pytest.fixture
def db_with_test_case(test_db, dummy_test_case):
    """
    Provide database with pre-inserted test case.

    @param test_db: Database fixture
    @param dummy_test_case: Test case fixture
    @return: tuple (database, test_case)
    """
    dummy_test_case.set_test_location("test_module.py", "test_function")
    test_case_id = test_db.insert_test_case(dummy_test_case)
    dummy_test_case.id = test_case_id
    return test_db, dummy_test_case


def test_database_initialization(tmp_path, dummy_test_case):
    """Test database initialization and schema creation."""
    db_file = tmp_path / "test.db"
    db = AutomationDatabase(f"sqlite:///{db_file}")

    # Verify database was created
    assert db.engine is not None
    assert db.Session is not None

    # Create tables and verify schema
    db.create_tables()
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    assert "test_cases" in tables
    assert "test_execution_records" in tables
    assert "custom_metrics" in tables

    # Verify required columns
    test_case_columns = {col['name'] for col in inspector.get_columns('test_cases')}
    required_columns = {
        'id', 'test_id', 'test_module', 'test_function',
        'name', 'description', 'test_suite',
    }
    assert required_columns.issubset(test_case_columns)


def test_test_case_operations(test_db, dummy_test_case):
    """Test CRUD operations for TestCase."""
    # Set test location
    dummy_test_case.set_test_location("test_module.py", "test_function")

    # Create
    test_case_id = test_db.insert_test_case(dummy_test_case)
    assert test_case_id is not None

    # Read by ID
    retrieved = test_db.fetch_test_case(test_case_id)
    assert retrieved is not None
    assert retrieved.name == dummy_test_case.name
    assert retrieved.test_id == dummy_test_case.test_id

    # Read by test_id
    retrieved_by_test_id = test_db.fetch_test_case_by_test_id(dummy_test_case.test_id)
    assert retrieved_by_test_id is not None
    assert retrieved_by_test_id.id == test_case_id

    # Update
    retrieved.description = "Updated Description"
    update_success = test_db.update_test_case(retrieved)
    assert update_success is True

    # Verify update
    updated = test_db.fetch_test_case(test_case_id)
    assert updated.description == "Updated Description"

    # Test non-existent cases
    assert test_db.fetch_test_case(9999) is None
    assert test_db.fetch_test_case_by_test_id("nonexistent::test") is None


def test_execution_record_operations(db_with_test_case):
    """Test CRUD operations for TestExecutionRecord."""
    db, test_case = db_with_test_case

    # Create execution record
    execution = TestExecutionRecord(test_case)
    execution.start()
    execution.add_custom_metric("metric1", "value1")
    execution.add_custom_metric("metric2", 123)

    # Insert
    execution_id = db.insert_test_execution(execution)
    assert execution_id is not None

    # Read
    retrieved = db.fetch_test_execution(execution_id)
    assert retrieved is not None
    assert retrieved.test_case.id == test_case.id
    assert retrieved.get_metric("metric1") == "value1"
    assert retrieved.get_metric("metric2") == 123

    # Update with new metrics
    retrieved.add_custom_metric("metric3", "new value")
    update_success = db.update_test_execution(retrieved)
    assert update_success is True

    # Verify update
    updated = db.fetch_test_execution(execution_id)
    assert updated.get_metric("metric3") == "new value"
    assert updated.get_metric("metric1") == "value1"  # Original metrics preserved

    # Test non-existent execution
    assert db.fetch_test_execution(9999) is None


def test_multiple_executions(db_with_test_case):
    """Test handling multiple executions of the same test case."""
    db, test_case = db_with_test_case

    # Create multiple executions
    execution_ids = []
    scenarios = [
        (TestResult.PASSED, True),
        (TestResult.FAILED, False),
        (TestResult.XFAILED, True)
    ]

    for i, (result, expected_success) in enumerate(scenarios):
        execution = TestExecutionRecord(test_case)
        execution.start()
        execution.add_custom_metric("iteration", i)
        execution.add_custom_metric("status", result.value)
        execution.end(result)

        if not expected_success:
            execution.set_failure(f"Test failed with {result.value}", "TestFailure")

        execution_id = db.insert_test_execution(execution)
        execution_ids.append(execution_id)

    # Fetch all executions
    executions = db.fetch_executions_for_test(test_case.id)
    assert len(executions) == len(scenarios)

    # Verify execution details
    success_count = sum(1 for e in executions if e.result.is_successful)
    assert success_count == 2  # PASSED and XFAILED are successful

    # Verify each execution separately
    for execution, (expected_result, expected_success) in zip(executions, scenarios):
        assert execution.result == expected_result
        assert execution.result.is_successful == expected_success
        assert execution.is_successful == expected_success
        assert execution.is_completed  # All should be completed

    # Verify metrics
    for i, execution in enumerate(executions):
        assert execution.get_metric("iteration") == i
        assert execution.get_metric("status") == scenarios[i][0].value


def test_metric_types(db_with_test_case):
    """Test handling different metric value types, including timestamps."""
    db, test_case = db_with_test_case

    # Create execution with various metric types
    execution = TestExecutionRecord(test_case)
    execution.start()

    # Current timestamp for testing
    current_time = datetime.now()
    iso_timestamp = current_time.isoformat()

    test_metrics = {
        "string": "test",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "null": None,
        "timestamp": current_time,
        "iso_timestamp": iso_timestamp,
        "timestamp_with_tz": current_time.astimezone(),
        "dates": {
            "start": current_time,
            "end": current_time + timedelta(hours=1)
        }
    }

    # Add all metrics
    for name, value in test_metrics.items():
        execution.add_custom_metric(name, value)

    # Save and verify
    execution_id = db.insert_test_execution(execution)
    retrieved = db.fetch_test_execution(execution_id)

    # Verify each metric type
    assert retrieved.get_metric("string") == "test"
    assert retrieved.get_metric("integer") == 42
    assert retrieved.get_metric("float") == 3.14
    assert retrieved.get_metric("boolean") is True
    assert retrieved.get_metric("list") == [1, 2, 3]
    assert retrieved.get_metric("dict") == {"key": "value"}
    assert retrieved.get_metric("null") is None

    # Verify timestamp handling
    stored_timestamp = retrieved.get_metric("timestamp")
    stored_iso = retrieved.get_metric("iso_timestamp")
    stored_tz = retrieved.get_metric("timestamp_with_tz")
    stored_dates = retrieved.get_metric("dates")

    # Verify timestamp formats
    assert isinstance(stored_timestamp, str)  # Should be serialized as ISO string
    assert isinstance(stored_iso, str)
    assert isinstance(stored_tz, str)
    assert isinstance(stored_dates, dict)

    # Parse and verify timestamps
    parsed_timestamp = datetime.fromisoformat(stored_timestamp)
    parsed_iso = datetime.fromisoformat(stored_iso)
    parsed_start = datetime.fromisoformat(stored_dates["start"])
    parsed_end = datetime.fromisoformat(stored_dates["end"])

    # Verify time differences are minimal
    assert abs((parsed_timestamp - current_time).total_seconds()) < 1
    assert abs((parsed_iso - current_time).total_seconds()) < 1
    assert abs((parsed_start - current_time).total_seconds()) < 1
    assert abs((parsed_end - (current_time + timedelta(hours=1))).total_seconds()) < 1


def test_transaction_management(test_db, dummy_test_case):
    """Test transaction management and rollback."""
    dummy_test_case.set_test_location("test_module.py", "test_function")

    # Test successful transaction
    with test_db.session_scope() as session:
        model = dummy_test_case.to_model()
        session.add(model)

    # Verify commit
    retrieved = test_db.fetch_test_case_by_test_id(dummy_test_case.test_id)
    assert retrieved is not None

    # Test transaction rollback
    try:
        with test_db.session_scope() as session:
            model = dummy_test_case.to_model()
            model.id = None  # Force new insert
            session.add(model)

            # Simulating a failure
            raise Exception("Test rollback")
    except:
        # rollback
        pass

    # Verify no duplicate test case
    with test_db.session_scope() as session:
        count = session.query(TestCaseModel).count()
        assert count == 1  # Only the first insert should persist
