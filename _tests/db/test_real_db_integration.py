from datetime import datetime

import pytest

from core.logger import Log
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult


def test_cross_dialect_compatibility(emulated_odbc_db, base_test_case):
    """Test compatibility across different database dialects"""
    # First, persist the test case
    test_case_id = emulated_odbc_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create execution record
    execution = TestExecutionRecord(base_test_case)
    execution.initialize()

    current_time = datetime.now()

    # Add test metrics with different data types
    test_metrics = {
        "big_integer": 9223372036854775807,  # Max int64
        "decimal": 123.456,
        "varchar": "a" * 255,  # Long string
        "timestamp": current_time.isoformat(),
        "boolean": True
    }

    # Start execution and add metrics
    execution.start()
    for name, value in test_metrics.items():
        execution.add_custom_metric(name, value)

    try:
        # Insert execution record
        execution_id = emulated_odbc_db.insert_test_execution(execution)
        assert execution_id is not None, "Failed to insert execution record"

        # Verify insertion
        retrieved_execution = emulated_odbc_db.fetch_test_execution(execution_id)
        assert retrieved_execution is not None, "Failed to retrieve execution record"

        # Verify metrics were stored correctly
        for name, expected_value in test_metrics.items():
            stored_value = retrieved_execution.get_metric(name)
            assert stored_value == expected_value, f"Metric {name} value mismatch"

        # Mark test as successful
        execution.end(TestResult.PASSED)
        assert emulated_odbc_db.update_test_execution(execution), "Failed to update execution status"

        # Verify final state
        final_execution = emulated_odbc_db.fetch_test_execution(execution_id)
        assert final_execution is not None
        assert final_execution.result == TestResult.PASSED
        assert final_execution.is_successful

    except Exception as e:
        Log.error(f"Test failed with dialect {emulated_odbc_db.dialect}: {str(e)}")
        execution.set_failure(str(e), type(e).__name__)
        execution.end(TestResult.FAILED)
        raise


def test_rollback_scenarios(emulated_odbc_db, base_test_case):
    """Test transaction rollback behavior"""
    # First, persist the test case
    test_case_id = emulated_odbc_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    execution = TestExecutionRecord(base_test_case)
    execution.initialize()
    execution.start()

    try:
        # Try operation that should trigger rollback
        with pytest.raises(Exception):
            with emulated_odbc_db.session_scope() as session:
                execution.add_custom_metric("to_rollback", True)
                session.add(execution.to_model())
                session.flush()

                # Force a rollback by raising an exception
                raise Exception("Forced rollback")

        # Verify the transaction was rolled back
        execution_id = execution.id
        if execution_id:
            retrieved_execution = emulated_odbc_db.fetch_test_execution(execution_id)
            assert retrieved_execution is None, "Execution record should not exist after rollback"

        # Mark execution as successful
        execution.add_custom_metric("rollback_verified", True)
        execution.end(TestResult.PASSED)

    except Exception as e:
        Log.error(f"Rollback test failed with dialect {emulated_odbc_db.dialect}: {str(e)}")
        execution.set_failure(str(e), type(e).__name__)
        execution.end(TestResult.FAILED)
        raise


def test_large_metrics_payload(emulated_odbc_db, base_test_case):
    """Test handling of large metric payloads"""
    # First, persist the test case
    test_case_id = emulated_odbc_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    execution = TestExecutionRecord(base_test_case)
    execution.initialize()
    execution.start()

    try:
        # Add large number of metrics
        for i in range(1000):
            execution.add_custom_metric(f"metric_{i}", f"value_{i}")

        # Create deep nested structure for testing serialization
        nested_dict = {"value": 0}
        current = nested_dict
        for i in range(100):
            current["next"] = {"value": i + 1}
            current = current["next"]

        execution.add_custom_metric("deep_structure", nested_dict)

        # Insert execution with all metrics
        execution_id = emulated_odbc_db.insert_test_execution(execution)
        assert execution_id is not None

        # Verify all metrics were stored
        retrieved = emulated_odbc_db.fetch_test_execution(execution_id)
        assert retrieved is not None

        # Verify metric count including base metrics
        metrics = retrieved.get_all_metrics()
        assert len(metrics) > 1000

        # Verify deep structure was serialized and deserialized correctly
        deep_metric = retrieved.get_metric("deep_structure")
        assert deep_metric is not None
        assert deep_metric["next"]["next"]["next"]["value"] == 3

        execution.end(TestResult.PASSED)
        assert emulated_odbc_db.update_test_execution(execution)

        # Verify final state
        final_execution = emulated_odbc_db.fetch_test_execution(execution_id)
        assert final_execution is not None
        assert final_execution.result == TestResult.PASSED
        assert final_execution.is_successful

    except Exception as e:
        Log.error(f"Large metrics test failed with dialect {emulated_odbc_db.dialect}: {str(e)}")
        execution.set_failure(str(e), type(e).__name__)
        execution.end(TestResult.FAILED)
        raise
