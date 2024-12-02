from datetime import datetime

import pytest

from _tests.fixtures import DIALECTS
from core.automation_database import AutomationDatabase
from core.logger import Log
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult
from models.base_model import Base


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


def test_cross_dialect_compatibility(emulated_odbc_db, base_test_case):
    """
    Test database compatibility across different SQL dialects.
    Verifies that different data types are properly stored and retrieved.

    @param emulated_odbc_db: Database fixture emulating different dialects
    @param base_test_case: Basic test case fixture
    """
    # Set up test case location and persist it
    base_test_case.set_test_location("test_module.py", "test_function")
    test_case_id = emulated_odbc_db.insert_test_case(base_test_case)
    base_test_case.id = test_case_id

    # Create and initialize execution record
    execution = TestExecutionRecord(base_test_case)
    execution.set_test_location(
        base_test_case.test_module,
        base_test_case.test_function,
        base_test_case.name,
        base_test_case.description
    )
    execution.initialize()

    # Test different data types
    current_time = datetime.now()
    test_metrics = {
        "big_integer": 9223372036854775807,  # Max int64
        "decimal": 123.456,  # Floating point
        "varchar": "a" * 255,  # Long string
        "timestamp": current_time.isoformat(),  # Date/time
        "boolean": True,  # Boolean
        "dictionary": {"key": "value"},  # Nested structure
        "list": [1, 2, 3],  # Array
        "null": None  # NULL value
    }

    # Add metrics and persist execution
    execution.start()
    for name, value in test_metrics.items():
        execution.add_custom_metric(name, value)

    try:
        # Save execution record
        execution_id = emulated_odbc_db.insert_test_execution(execution)
        assert execution_id is not None

        # Verify data was stored correctly
        retrieved_execution = emulated_odbc_db.fetch_test_execution(execution_id)
        assert retrieved_execution is not None

        # Verify all metrics were preserved
        for name, expected_value in test_metrics.items():
            stored_value = retrieved_execution.get_metric(name)
            assert stored_value == expected_value, f"Metric {name} value mismatch"

        # Complete execution successfully
        execution.end(TestResult.PASSED)
        assert emulated_odbc_db.update_test_execution(execution)


    except Exception as e:
        Log.error(f"Test failed with dialect {emulated_odbc_db.dialect}: {str(e)}")
        raise
