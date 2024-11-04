from datetime import datetime
from typing import Dict

from core.automation_database import AutomationDatabase
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult

DIALECTS: Dict[str, Dict[str, any]] = {
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


def test_basic_test_case_persistence(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test basic test case persistence without executions."""

    # Save test case
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    assert test_case_id is not None, "Failed to insert test case"

    # Retrieve and verify
    retrieved = sqlite_db.fetch_test_case(test_case_id)
    assert retrieved is not None, "Failed to retrieve test case"
    assert retrieved.name == base_test_case.name, "Test case name mismatch"
    assert retrieved.description == base_test_case.description, "Test case description mismatch"
    assert retrieved.test_suite == base_test_case.test_suite, "Test suite mismatch"
    assert retrieved.scope == base_test_case.scope, "Scope mismatch"
    assert retrieved.component == base_test_case.component, "Component mismatch"


def test_test_execution_persistence(sqlite_db, base_test_case):
    """Test persisting and retrieving test execution record."""

    # Insert test case first
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create execution record
    execution = TestExecutionRecord(base_test_case)

    # Add some metrics before initialization
    execution.add_custom_metric("pre_init_metric", "value")

    # Start execution
    execution.start()

    # Add more metrics
    execution.add_custom_metric("post_init_metric", "value")

    # Persist
    execution_id = sqlite_db.insert_test_execution(execution)
    assert execution_id is not None

    # Make sure we store the execution ID
    execution.id = execution_id

    # Complete execution
    execution.end(TestResult.PASSED)
    sqlite_db.update_test_execution(execution)

    # Retrieve using the correct ID
    retrieved = sqlite_db.fetch_test_execution(execution_id)
    assert retrieved is not None, f"Failed to retrieve execution record with ID {execution_id}"

    # Verify retrieved data
    assert retrieved.test_case.id == base_test_case.id
    assert retrieved.test_case.name == base_test_case.name
    assert retrieved.get_metric("pre_init_metric") == "value"
    assert retrieved.get_metric("post_init_metric") == "value"
    assert retrieved.is_completed
    assert retrieved.is_successful


def test_multiple_executions(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test multiple executions of the same test case."""

    # Save test case
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create multiple executions with different results
    executions = []
    for i in range(3):
        execution = TestExecutionRecord(base_test_case)
        execution.start()
        execution.add_custom_metric("iteration", i + 1)
        execution.add_custom_metric("data_size", (i + 1) * 100)
        execution.end(TestResult.FAILED if i == 1 else TestResult.PASSED)  # Make second execution fail

        execution_id = sqlite_db.insert_test_execution(execution)
        executions.append(execution_id)

    # Verify all executions
    retrieved_executions = sqlite_db.fetch_executions_for_test(test_case_id)
    assert len(retrieved_executions) == 3, "Wrong number of executions retrieved"

    # Verify execution details
    success_count = sum(1 for e in retrieved_executions if e.is_successful)
    assert success_count == 2, "Wrong number of successful executions"


def test_dialect_specific_features(emulated_odbc_db: AutomationDatabase, base_test_case: TestCase):
    """Test database operations with different SQL dialects."""

    # Save test case
    test_case_id = emulated_odbc_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create execution with various metric types
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    test_metrics = {
        "int_value": 42,
        "float_value": 3.14159,
        "string_value": "test string",
        "bool_value": True,
        "list_value": [1, 2, 3],
        "dict_value": {"key": "value"},
        "date_value": datetime.now().isoformat()
    }

    for name, value in test_metrics.items():
        execution.add_custom_metric(name, value)

    execution.end(TestResult.PASSED)

    # Save and verify
    execution_id = emulated_odbc_db.insert_test_execution(execution)

    retrieved = emulated_odbc_db.fetch_test_execution(execution_id)
    assert retrieved is not None, "Failed to retrieve test execution"

    for name, value in test_metrics.items():
        assert retrieved.get_metric(name) == value, f"Metric {name} mismatch"


def test_error_cases(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test error handling in database operations."""

    # Test fetching non-existent test case
    assert sqlite_db.fetch_test_case(9999) is None, "Should return None for non-existent test case"

    # Test fetching non-existent execution
    assert sqlite_db.fetch_test_execution(9999) is None, "Should return None for non-existent execution"

    # Test updating non-existent test case
    base_test_case.id = 9999
    assert not sqlite_db.update_test_case(base_test_case), "Should return False for non-existent test case update"

    # Test updating non-existent execution
    execution = TestExecutionRecord(base_test_case)
    execution.id = 9999
    assert not sqlite_db.update_test_execution(execution), "Should return False for non-existent execution update"


def test_execution_metrics_update(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test updating test execution metrics."""

    # Save test case
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create initial execution with metrics
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    # Add initial metrics
    execution.add_custom_metric("metric1", "initial_value")
    execution.add_custom_metric("metric2", "value2")

    # Save initial execution
    execution_id = sqlite_db.insert_test_execution(execution)

    # Verify initial state
    initial = sqlite_db.fetch_test_execution(execution_id)
    assert initial.get_metric("metric1") == "initial_value", "Initial metric1 not set correctly"
    assert initial.get_metric("metric2") == "value2", "Initial metric2 not set correctly"

    # Update execution with ONLY the metrics we want to keep
    retrieved = sqlite_db.fetch_test_execution(execution_id)
    retrieved._metrics.clear()  # Clear all existing metrics

    # Re-add test case properties
    retrieved._add_test_case_metrics()

    # Add only the metrics we want
    retrieved.add_custom_metric("metric1", "updated_value")
    retrieved.add_custom_metric("metric3", "new_value")

    # Save updates
    success = sqlite_db.update_test_execution(retrieved)
    assert success is True, "Failed to update execution"

    # Fetch and verify final state
    final = sqlite_db.fetch_test_execution(execution_id)
    assert final is not None, "Failed to retrieve updated execution"

    # Check each metric individually and log the values
    metric1 = final.get_metric("metric1")
    metric2 = final.get_metric("metric2")
    metric3 = final.get_metric("metric3")

    assert metric1 == "updated_value", f"metric1 should be 'updated_value', got {metric1}"
    assert metric2 is None, f"metric2 should be None, got {metric2}"
    assert metric3 == "new_value", f"metric3 should be 'new_value', got {metric3}"


def test_complex_metrics(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test handling of complex metric types."""

    # Save test case
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create execution with complex metrics
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    complex_metrics = {
        "nested_dict": {
            "key1": {
                "subkey1": "value1",
                "subkey2": 42
            },
            "key2": [1, 2, 3]
        },
        "list_of_dicts": [
            {"name": "item1", "value": 100},
            {"name": "item2", "value": 200}
        ],
        "mixed_data": {
            "string": "test",
            "number": 42,
            "boolean": True,
            "null_value": None,
            "list": [1, "two", 3.0],
        }
    }

    for name, value in complex_metrics.items():
        execution.add_custom_metric(name, value)

    # Save and verify
    execution_id = sqlite_db.insert_test_execution(execution)

    retrieved = sqlite_db.fetch_test_execution(execution_id)
    assert retrieved is not None, "Failed to retrieve execution"

    for name, value in complex_metrics.items():
        assert retrieved.get_metric(name) == value, f"Complex metric {name} mismatch"


def test_long_execution_updates(sqlite_db: AutomationDatabase, base_test_case: TestCase):
    """Test multiple updates during a long execution."""

    # Save test case
    test_case_id = sqlite_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Start execution
    execution = TestExecutionRecord(base_test_case)
    execution.start()
    execution_id = sqlite_db.insert_test_execution(execution)

    # Simulate multiple updates during execution
    updates = [
        {"progress": 25, "memory_usage": 100, "status": "initializing"},
        {"progress": 50, "memory_usage": 150, "status": "processing"},
        {"progress": 75, "memory_usage": 200, "status": "finalizing"},
        {"progress": 100, "memory_usage": 180, "status": "completed"}
    ]

    for update_data in updates:
        retrieved = sqlite_db.fetch_test_execution(execution_id)
        for name, value in update_data.items():
            retrieved.add_custom_metric(name, value)

        success = sqlite_db.update_test_execution(retrieved)
        assert success is True, f"Failed to update execution at progress {update_data['progress']}%"

    # Verify final state
    final = sqlite_db.fetch_test_execution(execution_id)
    assert final is not None, "Failed to retrieve final execution state"

    for name, value in updates[-1].items():
        assert final.get_metric(name) == value, f"Final metric {name} mismatch"
