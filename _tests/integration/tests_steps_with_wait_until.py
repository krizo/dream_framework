"""
Test module for verifying wait_until decorator's log reset functionality.
Tests how the decorator handles step logging in different scenarios.
"""
from pathlib import Path

import pytest

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from core.plugins.test_case_plugin import TestCasePlugin
from core.step import step_start
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from helpers.decorators import wait_until, WaitTimeoutError

# Mark all tests to disable standard database plugin
pytestmark = pytest.mark.no_database_plugin


def get_log_steps(log_file: Path) -> list[str]:
    """
    Extract step entries from log file.

    @param log_file: Path to log file
    @return: List of step log entries
    """
    steps = []
    if not log_file.exists():
        return steps

    with open(log_file, 'r') as f:
        for line in f:
            if '| STEP     |' in line:
                steps.append(line.strip())
    return steps


class WaitUntilTestCase(TestCase):
    """Test case for verifying wait_until logs behavior."""

    def __init__(self):
        super().__init__(
            name="Wait Until Logs Test",
            description="Test wait until decorator log reset functionality",
            test_suite="Step Tests",
            scope="Unit",
            component="Steps"
        )
        self.counter = 0

    @wait_until(timeout=0.5, interval=0.1, reset_logs=True)
    def wait_with_reset(self):
        """Test function with log reset between attempts."""
        with step_start("Checking condition"):
            with step_start("Validating counter"):
                self.counter += 1
                Log.info(f"Counter value: {self.counter}")
                assert self.counter >= 3, f"Counter ({self.counter}) should be >= 3"

    @wait_until(timeout=0.5, interval=0.1, reset_logs=False)
    def wait_without_reset(self):
        """Test function without log reset between attempts."""
        with step_start("Checking condition"):
            with step_start("Validating counter"):
                self.counter += 1
                Log.info(f"Counter value: {self.counter}")
                assert self.counter >= 3, f"Counter ({self.counter}) should be >= 3"


def initialize_test_execution(test_case: TestCase, test_function: str) -> TestExecutionRecord:
    """
    Initialize test execution record and database.

    @param test_case: Test case instance
    @param test_function: Test function name
    @return: Initialized TestExecutionRecord
    """
    Log.info(f"Initializing test execution for {test_function}")

    # Setup test case
    test_case.set_test_location(
        "_tests/integration/test_steps_with_wait_until.py",
        test_function
    )

    # Create and initialize execution record
    execution_record = TestExecutionRecord(test_case)
    test_case.set_execution_record(execution_record)
    execution_record.set_test_location(
        "_tests/integration/test_steps_with_wait_until.py",
        test_function,
        test_case.name,
        test_case.description
    )

    # Start execution
    execution_record.start()

    # Set current execution in plugin
    TestCasePlugin.set_current_execution(execution_record)
    Log.info(f"Current execution set: {TestCasePlugin.get_current_execution()}")

    # Initialize database
    db = AutomationDatabaseManager.get_database()
    test_case_id = db.insert_test_case(test_case)
    test_case.id = test_case_id
    execution_id = db.insert_test_execution(execution_record)
    execution_record.id = execution_id

    return execution_record


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initialize in-memory database for tests."""
    Log.info("Setting up test database")

    # Create in-memory database
    db = AutomationDatabase('sqlite:///:memory:')
    db.create_tables()

    # Initialize database manager
    AutomationDatabaseManager._db_instance = db
    AutomationDatabaseManager._initialized = True

    yield db

    # Cleanup
    AutomationDatabaseManager.close()
    Log.info("Test database cleaned up")


@pytest.fixture
def wait_test_case():
    """Fixture providing test case instance."""
    return WaitUntilTestCase()


def test_wait_until_with_log_reset(wait_test_case, tmp_path):
    """Test wait_until with log reset between attempts."""
    log_file = tmp_path / "test_reset.log"
    Log.reconfigure_file_handler(str(log_file))

    execution_record = initialize_test_execution(
        wait_test_case,
        "test_wait_until_with_log_reset"
    )
    Log.info(f"Test execution initialized with ID: {execution_record.id}")

    # Execute test function
    wait_test_case.wait_with_reset()

    # Analyze logs
    steps = get_log_steps(log_file)
    Log.info(f"Found {len(steps)} step entries in log")

    for step in steps:
        Log.info(f"Step log: {step}")

    # Extract sequence numbers
    sequence_numbers = []
    for step in steps:
        parts = step.split('|')
        if len(parts) >= 3:
            number = parts[2].strip().split()[0]
            sequence_numbers.append(number)
            Log.info(f"Found step number: {number}")

    # Verify reset behavior
    root_step_count = sequence_numbers.count("1")
    nested_step_count = sequence_numbers.count("1.1")

    Log.info(f"Root steps found: {root_step_count}")
    Log.info(f"Nested steps found: {nested_step_count}")

    assert root_step_count > 1, "Step numbers should reset between attempts"
    assert nested_step_count > 1, "Nested step numbers should reset between attempts"
    assert wait_test_case.counter == 3, "Counter should reach 3"


def test_wait_until_without_log_reset(wait_test_case, tmp_path):
    """Test wait_until without log reset between attempts."""
    log_file = tmp_path / "test_no_reset.log"
    Log.reconfigure_file_handler(str(log_file))

    execution_record = initialize_test_execution(
        wait_test_case,
        "test_wait_until_without_log_reset"
    )
    Log.info(f"Test execution initialized with ID: {execution_record.id}")

    # Execute test function
    wait_test_case.wait_without_reset()

    # Analyze logs
    steps = get_log_steps(log_file)
    Log.info(f"Found {len(steps)} step entries in log")

    for step in steps:
        Log.info(f"Step log: {step}")

    sequence_numbers = []
    for step in steps:
        parts = step.split('|')
        if len(parts) >= 3:
            number = parts[2].strip().split()[0]
            sequence_numbers.append(number)
            Log.info(f"Found step number: {number}")

    # Verify continuous numbering
    root_step_count = sequence_numbers.count("1")
    nested_step_count = sequence_numbers.count("1.1")

    Log.info(f"Root steps found: {root_step_count}")
    Log.info(f"Nested steps found: {nested_step_count}")

    assert root_step_count >= 3, "Should have at least 3 root steps (one per attempt)"
    assert nested_step_count >= 3, "Should have at least 3 nested steps (one per attempt)"
    assert wait_test_case.counter == 3, "Counter should reach 3"


@pytest.mark.parametrize("reset_logs,expected_resets", [
    (True, True),
    (False, False)
])
def test_wait_until_parameterized(wait_test_case, tmp_path, reset_logs, expected_resets):
    """Test wait_until with different reset_logs configurations."""
    log_file = tmp_path / f"test_param_{reset_logs}.log"
    Log.reconfigure_file_handler(str(log_file))

    test_name = f"test_wait_until_parameterized[{reset_logs}-{expected_resets}]"
    execution_record = initialize_test_execution(
        wait_test_case,
        test_name
    )
    Log.info(f"Test execution initialized with ID: {execution_record.id}")

    wait_test_case.counter = 0

    all_root_steps = []

    @wait_until(timeout=0.5, interval=0.1, reset_logs=reset_logs)
    def count_up():
        """Test counting function with nested steps."""
        with step_start("Start counting") as root_step:
            # Store the actual sequence number
            all_root_steps.append(root_step.sequence_number)
            Log.info(f"Started root step with sequence number: {root_step.sequence_number}")

            with step_start("Incrementing counter"):
                wait_test_case.counter += 1
                Log.info(f"Counter value: {wait_test_case.counter}")

            with step_start("Validating counter"):
                assert wait_test_case.counter >= 3, \
                    f"Counter {wait_test_case.counter} should be >= 3"

    # Execute test function
    count_up()

    Log.info(f"All root step sequence numbers: {all_root_steps}")

    if expected_resets:
        # When resetting, all sequence numbers should be 1
        assert all(num == 1 for num in all_root_steps), \
            f"All root step sequence numbers should be 1 when reset_logs=True, got {all_root_steps}"
    else:
        # When not resetting, sequence numbers should increase monotonically
        assert len(all_root_steps) == 3, f"Expected 3 attempts, got {len(all_root_steps)}"
        assert all(all_root_steps[i] < all_root_steps[i+1] for i in range(len(all_root_steps)-1)), \
            f"Root step sequence numbers should increase without reset_logs, got {all_root_steps}"

    # Common assertions
    assert wait_test_case.counter == 3, "Counter should reach exactly 3"

    # Verify step nesting is preserved
    steps = get_log_steps(log_file)
    nested_steps = []
    for step in steps:
        parts = step.split('|')
        if len(parts) >= 3:
            step_info = parts[2].strip()
            number = step_info.split()[0]
            nested_steps.append(number)

    # Group steps by attempt
    attempts = []
    current_attempt = []
    for step in nested_steps:
        if '.' not in step and current_attempt:
            attempts.append(current_attempt)
            current_attempt = []
        current_attempt.append(step)
    if current_attempt:
        attempts.append(current_attempt)

    Log.info(f"Step structure by attempt: {attempts}")

    # Verify each attempt has correct structure
    for attempt in attempts:
        assert len(attempt) == 3, f"Each attempt should have 3 steps, got {attempt}"
        root = attempt[0]
        nested1 = attempt[1]
        nested2 = attempt[2]

        # Verify nesting structure independent of actual numbers
        assert '.' not in root, f"First step should be root step, got {root}"
        assert nested1.startswith(f"{root}."), f"Second step should be nested under root, got {nested1}"
        assert nested2.startswith(f"{root}."), f"Third step should be nested under root, got {nested2}"


def test_wait_until_error_handling(wait_test_case, tmp_path):
    """Test error handling in wait_until with steps."""
    log_file = tmp_path / "test_error.log"
    Log.reconfigure_file_handler(str(log_file))

    execution_record = initialize_test_execution(
        wait_test_case,
        "test_wait_until_error_handling"
    )
    Log.info(f"Test execution initialized with ID: {execution_record.id}")

    all_root_steps = []

    @wait_until(
        timeout=0.3,
        interval=0.1,
        reset_logs=True,
        ignored_exceptions=(ValueError,)  # Add ValueError to ignored exceptions
    )
    def always_fail():
        """Function that always fails with nested steps."""
        with step_start("Starting fail test") as root_step:
            all_root_steps.append(root_step.sequence_number)
            Log.info(f"Started root step with number: {root_step.sequence_number}")

            with step_start("This will fail"):
                Log.info("About to fail...")
                raise ValueError("Expected failure")

    # Execute and verify timeout
    with pytest.raises(WaitTimeoutError) as exc_info:
        always_fail()

    # Verify error message
    assert "Expected failure" in str(exc_info.value), "Error message should contain original error"

    # Verify we had multiple attempts
    assert len(all_root_steps) > 1, f"Should have multiple attempts, got {len(all_root_steps)}"

    # Verify step numbers were reset
    assert all(num == 1 for num in all_root_steps), \
        f"All root steps should have number 1 when reset_logs=True, got {all_root_steps}"

    # Analyze steps from log
    steps = get_log_steps(log_file)

    # Group steps by attempt
    attempts = []
    current_attempt = []
    for step in steps:
        parts = step.split('|')
        if len(parts) >= 3:
            step_info = parts[2].strip()
            number = step_info.split()[0]
            if '.' not in number and current_attempt:
                attempts.append(current_attempt)
                current_attempt = []
            current_attempt.append(step_info)

    if current_attempt:
        attempts.append(current_attempt)

    Log.info(f"Found {len(attempts)} attempt groups")
    for i, attempt in enumerate(attempts):
        Log.info(f"Attempt {i + 1} steps: {attempt}")

    # Verify we have proper step structure in each attempt
    for attempt in attempts:
        assert len(attempt) == 2, f"Each attempt should have 2 steps, got {attempt}"
        root = attempt[0].split()[0]  # Get just the number
        nested = attempt[1].split()[0]  # Get just the number

        # Verify nesting structure
        assert '.' not in root, f"First step should be root step, got {root}"
        assert nested.startswith(f"{root}."), \
            f"Second step should be nested under root, got {nested}"