from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult


class LoginTestCase(TestCase):
    """Test case for login functionality."""

    def __init__(self):
        super().__init__(
            name="Login Test",
            description="Verify user login functionality",
            test_suite="authentication_tests",
            component="Authentication",
            scope="Integration"
        )


def test_login_execution_record_success(base_test_case, real_db):
    """Test successful login execution with metrics."""

    # Create execution record
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    # Add execution metrics
    execution.add_custom_metric("user_id", "12345")
    execution.add_custom_metric("login_duration_ms", 150)
    execution.add_custom_metric("browser", "Chrome")

    # Mark as successful
    execution.end(TestResult.PASSED)

    # Save execution - normally it will take place in pytest hook, so we should never do that
    execution_id = real_db.insert_test_execution(execution)

    # Verify execution was saved correctly
    retrieved_execution = real_db.fetch_test_execution(execution_id)
    assert retrieved_execution is not None
    assert retrieved_execution.result is TestResult.PASSED
    assert retrieved_execution.get_metric("user_id") == "12345"
    assert retrieved_execution.get_metric("login_duration_ms") == 150
    assert retrieved_execution.get_metric("browser") == "Chrome"


def test_login_execution_record_failure(base_test_case, real_db):
    """Test failed login execution with error details."""
    # Create execution record
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    # Add execution metrics
    execution.add_custom_metric("user_id", "12345")
    execution.add_custom_metric("error_type", "InvalidCredentials")
    execution.add_custom_metric("attempts", 3)

    # Mark as failed and set error details
    execution.end(TestResult.FAILED)
    execution.set_failure("Invalid username or password", "AuthenticationError")

    # Save execution
    execution_id = real_db.insert_test_execution(execution)

    # Verify execution was saved correctly
    retrieved_execution = real_db.fetch_test_execution(execution_id)
    assert retrieved_execution is not None
    assert retrieved_execution.result is TestResult.FAILED
    assert retrieved_execution.failure_type == "AuthenticationError"
    assert retrieved_execution.get_metric("error_type") == "InvalidCredentials"
    assert retrieved_execution.get_metric("attempts") == 3


def test_multiple_executions_login(base_test_case, real_db):
    """Test multiple execution records for the same test case."""

    # Create executions with different scenarios
    scenarios = [
        {
            "metrics": {"error": "Network timeout"},
            "result": TestResult.FAILED,
            "failure": ("Network connection failed", "NetworkError")
        },
        {
            "metrics": {"error": "Invalid password"},
            "result": TestResult.FAILED,
            "failure": ("Authentication failed", "AuthError")
        },
        {
            "metrics": {"login_time_ms": 120},
            "result": TestResult.PASSED,
            "failure": None
        }
    ]

    execution_ids = []  # Track our execution IDs

    # Create executions
    for i, scenario in enumerate(scenarios, 1):
        execution = TestExecutionRecord(base_test_case)
        execution.start()

        # Add common metrics
        execution.add_custom_metric("attempt_number", i)
        execution.add_custom_metric("user_id", "12345")

        # Add scenario-specific metrics
        for name, value in scenario["metrics"].items():
            execution.add_custom_metric(name, value)

        # Set result and failure if any
        execution.end(scenario["result"])
        if scenario["failure"]:
            message, failure_type = scenario["failure"]
            execution.set_failure(message, failure_type)

        execution_id = real_db.insert_test_execution(execution)
        execution_ids.append(execution_id)  # Store the ID

    # Fetch only our created executions by ID
    executions = [
        real_db.fetch_test_execution(exec_id)
        for exec_id in execution_ids
    ]

    # Filter out any None values (in case fetch failed)
    executions = [e for e in executions if e is not None]

    assert len(executions) == len(scenarios), \
        f"Expected {len(scenarios)} executions, got {len(executions)}"

    # Sort executions by attempt number for deterministic verification
    executions.sort(key=lambda e: e.get_metric("attempt_number"))

    # Verify execution details
    success_count = sum(1 for e in executions if e.result is TestResult.PASSED)
    assert success_count == 1, f"Expected 1 successful execution, got {success_count}"

    # Verify each execution matches its scenario
    for execution, scenario in zip(executions, scenarios):
        attempt = execution.get_metric("attempt_number")

        # Verify common metrics
        assert execution.get_metric("user_id") == "12345"

        # Verify scenario-specific metrics
        for name, value in scenario["metrics"].items():
            assert execution.get_metric(name) == value, \
                f"Metric {name} mismatch in attempt {attempt}"

        # Verify result
        assert execution.result == scenario["result"], \
            f"Result mismatch in attempt {attempt}"

        # Verify failure if any
        if scenario["failure"]:
            message, failure_type = scenario["failure"]
            assert execution.failure == message, \
                f"Failure message mismatch in attempt {attempt}"
            assert execution.failure_type == failure_type, \
                f"Failure type mismatch in attempt {attempt}"
        else:
            assert not execution.failure and not execution.failure_type, \
                f"Unexpected failure in successful attempt {attempt}"


def test_execution_metric_updates(base_test_case, real_db):
    """Test updating metrics during test execution."""

    # Start execution
    execution = TestExecutionRecord(base_test_case)
    execution.start()

    # Set initial metrics
    initial_metrics = {
        "status": "starting",
        "progress": 0
    }
    for name, value in initial_metrics.items():
        execution.add_custom_metric(name, value)

    # Save initial state
    execution_id = real_db.insert_test_execution(execution)
    assert execution_id is not None, "Failed to create initial execution record"

    # Verify initial state
    initial = real_db.fetch_test_execution(execution_id)
    assert initial is not None, "Failed to fetch initial execution"
    assert initial.get_metric("status") == "starting"
    assert initial.get_metric("progress") == 0

    # Update progress
    execution.add_custom_metric("status", "authenticating")
    execution.add_custom_metric("progress", 50)
    update_success = real_db.update_test_execution(execution)
    assert update_success is True, "Failed to update execution with progress metrics"

    # Verify intermediate state
    intermediate = real_db.fetch_test_execution(execution_id)
    assert intermediate.get_metric("status") == "authenticating"
    assert intermediate.get_metric("progress") == 50

    # Final update
    final_metrics = {
        "status": "completed",
        "progress": 100,
        "login_time_ms": 200
    }
    for name, value in final_metrics.items():
        execution.add_custom_metric(name, value)
    execution.end(TestResult.PASSED)

    update_success = real_db.update_test_execution(execution)
    assert update_success is True, "Failed to update execution with final metrics"

    # Verify final state
    final = real_db.fetch_test_execution(execution_id)
    assert final is not None, "Failed to fetch final execution state"
    assert final.get_metric("status") == "completed"
    assert final.get_metric("progress") == 100
    assert final.get_metric("login_time_ms") == 200
    assert final.result is TestResult.PASSED

    # Verify all metrics are present
    all_metrics = {
        "status": "completed",
        "progress": 100,
        "login_time_ms": 200
    }
    for name, expected_value in all_metrics.items():
        assert final.get_metric(name) == expected_value, \
            f"Metric {name} has incorrect value"
