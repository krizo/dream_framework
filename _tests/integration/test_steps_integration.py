"""Integration tests for test steps functionality."""
from typing import List

"""Integration tests for test steps functionality."""
from typing import Dict, Any

import pytest

from core.automation_database_manager import AutomationDatabaseManager
from core.step import step_start
from core.test_case import TestCase
from models.step_model import StepModel


class StepsTest(TestCase):
    """Test case for verifying step functionality."""

    def __init__(self):
        super().__init__(
            name="Steps Integration Test",
            description="Testing step hierarchy and persistence",
            test_suite="Integration Tests",
            scope="E2E",
            component="Steps"
        )


@pytest.fixture
def steps_test():
    """Provide test case fixture."""
    return StepsTest()


# Store results for verification
test_results: Dict[str, Any] = {}


def pytest_runtest_makereport(item, call):
    """Verify steps after test execution."""
    if call.when == "teardown":
        # Get the test case from the test function
        test_case = None
        for arg_name, arg_value in item.funcargs.items():
            if isinstance(arg_value, TestCase):
                test_case = arg_value
                break

        if not test_case:
            return

        # Store test result for verification
        test_results[item.name] = {
            'test_case': test_case,
            'execution_record': test_case._execution_record
        }


@pytest.fixture
def verify_steps(request):
    """Fixture to verify steps after test."""
    yield
    test_name = request.node.name
    result = test_results.get(test_name)

    if not result or not result['execution_record']:
        return

    # Now verify steps
    db = AutomationDatabaseManager.get_database()
    with db.session_scope() as session:
        steps = session.query(StepModel) \
            .filter(StepModel.execution_record_id == result['execution_record'].id) \
            .order_by(StepModel.sequence_number) \
            .all()

        if test_name == "test_complex_workflow_with_steps":
            verify_complex_workflow_steps(steps)
        elif test_name == "test_step_error_handling":
            verify_error_handling_steps(steps)
        elif test_name == "test_step_performance":
            verify_performance_steps(steps, result['execution_record'].id)


def verify_complex_workflow_steps(steps: List[StepModel]):
    """Verify steps from complex workflow test."""
    # Basic verification
    assert len(steps) == 15, f"Expected 15 steps, got {len(steps)}"
    assert all(step.completed for step in steps), "All steps should be completed"

    # Verify root step
    root_steps = [s for s in steps if s.parent_step_id is None]
    assert len(root_steps) == 1, "Should have exactly one root step"
    root = root_steps[0]
    assert root.content == "Initialize workflow"

    # Verify immediate children of root
    level1_steps = [s for s in steps if s.parent_step_id == root.id]
    assert len(level1_steps) == 3, "Root should have 3 direct children"
    assert {s.content for s in level1_steps} == {
        "Setup environment",
        "Process items",
        "Cleanup"
    }


def test_complex_workflow_with_steps(steps_test):
    """
    Complex workflow test case verifying:
    - Nested steps creation
    - Sequential steps
    - Step hierarchy persistence
    """
    with step_start("Initialize workflow"):
        with step_start("Setup environment"):
            with step_start("Configure settings"):
                pass
            with step_start("Verify configuration"):
                pass

        with step_start("Process items"):
            for item in ["A", "B", "C"]:
                with step_start(f"Processing {item}"):
                    with step_start(f"Validate {item}"):
                        pass
                    with step_start(f"Transform {item}"):
                        pass

        with step_start("Cleanup"):
            pass


def test_step_error_handling(steps_test, verify_steps):
    """Test step behavior when errors occur."""
    error_msg = "Test error"
    try:
        with step_start("Main operation"):
            with step_start("Sub operation"):
                raise ValueError(error_msg)
    except ValueError as e:
        assert str(e) == error_msg


def verify_error_handling_steps(steps: List[StepModel]):
    """Verify steps from error handling test."""
    assert len(steps) == 2, "Both steps should be saved"
    assert all(step.completed for step in steps)

    # Verify hierarchy
    root = next(s for s in steps if s.parent_step_id is None)
    child = next(s for s in steps if s.parent_step_id == root.id)

    assert root.content == "Main operation"
    assert child.content == "Sub operation"


def test_step_performance(steps_test, verify_steps):
    """Test step performance with large number of steps."""
    with step_start("Performance test"):
        for i in range(100):
            with step_start(f"Operation {i}"):
                for j in range(5):
                    with step_start(f"Sub operation {i}.{j}"):
                        pass


def verify_performance_steps(steps: List[StepModel], execution_id: int):
    """Verify steps from performance test."""
    expected_steps = 1 + 100 + (100 * 5)  # root + operations + sub-operations
    assert len(steps) == expected_steps, \
        f"Expected {expected_steps} steps, got {len(steps)}"

    # Verify all steps are completed and linked correctly
    assert all(step.completed for step in steps)
    assert all(step.execution_record_id == execution_id for step in steps)

    # Verify hierarchy
    root = next(s for s in steps if s.parent_step_id is None)
    operations = [s for s in steps if s.parent_step_id == root.id]
    assert len(operations) == 100

    # Verify sub-operations
    for op in operations:
        sub_steps = [s for s in steps if s.parent_step_id == op.id]
        assert len(sub_steps) == 5
