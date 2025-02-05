from typing import Dict

from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult


def test_execution_record_initialization(dummy_test_case):
    """
    Test initialization of TestExecutionRecord.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)

    assert execution.id is None
    assert execution.test_case == dummy_test_case
    assert execution.result is TestResult.STARTED
    assert execution.start_time is None
    assert execution.end_time is None
    assert execution.duration is None
    assert not execution._initialized


def test_execution_lifecycle(dummy_test_case):
    """
    Test complete execution lifecycle from start to end.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)

    # Test initialization
    execution.initialize()
    assert execution._initialized
    assert execution.test_case.name == dummy_test_case.name
    assert execution.test_case.description == dummy_test_case.description

    # Test start
    execution.start()
    assert execution.start_time is not None
    start_time = execution.start_time
    assert start_time is not None

    # Test successful completion
    execution.end(TestResult.PASSED)
    assert execution.result is TestResult.PASSED
    assert execution.end_time is not None
    assert execution.duration is not None
    assert execution.duration > 0
    assert execution.is_completed
    assert execution.is_successful


def test_execution_failure(dummy_test_case):
    """
    Test execution failure handling.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)
    execution.start()

    failure_msg = "Test failed"
    failure_type = "AssertionError"

    execution.set_failure(failure_msg, failure_type)
    execution.end(TestResult.FAILED)

    assert execution.result is TestResult.FAILED
    assert execution.failure == failure_msg
    assert execution.failure_type == failure_type
    assert execution.is_completed
    assert not execution.is_successful


def test_metric_management(dummy_test_case):
    """
    Test adding and retrieving metrics.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)

    # Test adding different types of metrics
    test_metrics: Dict[str, any] = {
        "string_metric": "test",
        "int_metric": 42,
        "float_metric": 3.14,
        "bool_metric": True,
        "list_metric": [1, 2, 3],
        "dict_metric": {"key": "value"},
        "none_metric": None
    }

    for name, value in test_metrics.items():
        execution.add_custom_metric(name, value)
        stored = execution.get_metric(name)
        assert stored == value, f"Metric {name} was not stored correctly"

    # Test getting all metrics
    all_metrics = execution.get_all_metrics()
    assert len(all_metrics) == len(test_metrics)

    for metric in all_metrics:
        assert isinstance(metric, dict)
        assert "name" in metric
        assert "value" in metric
        assert metric["value"] == test_metrics[metric["name"]]


def test_test_location_handling(dummy_test_case):
    """
    Test setting test location information.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)

    module = "test_module.py"
    function = "test_function"
    name = 'test name'
    description = 'test description'

    execution.set_test_location(module, function, name, description)

    assert execution.test_module == module
    assert execution.test_function == function
    assert execution.test_module == module
    assert execution.test_function == function


def test_model_conversion(dummy_test_case):
    """
    Test conversion between TestExecutionRecord and database model.

    @param dummy_test_case: Minimal TestCase fixture
    """
    execution = TestExecutionRecord(dummy_test_case)
    execution.start()
    execution.add_custom_metric("test_metric", "value")
    execution.end(TestResult.PASSED)

    model = execution.to_model()

    assert model.test_case_id == dummy_test_case.id
    assert model.result is TestResult.PASSED.value
    assert len(model.custom_metrics) > 0

    # Verify metrics in model
    metric = next(m for m in model.custom_metrics if m.name == "test_metric")
    assert metric.value == "value"
