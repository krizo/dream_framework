"""Tests for step functionality."""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from core.logger import Log
from core.step import Step, step_start
from helpers.decorators import step


@pytest.fixture(autouse=True)
def reset_step_state():
    """Reset step state before and after each test."""
    Step.reset_for_test()
    yield
    Step.reset_for_test()


@pytest.fixture
def mock_logger():
    """Mock logger to verify step logging."""
    with patch.object(Log, 'step') as mock:
        yield mock


def test_basic_step_creation():
    """Test basic step object creation."""
    step = Step("Test step")
    assert step.content == "Test step"
    assert step.completed is False
    assert step.parent_step is None
    assert step.step_id.startswith("step_")


def test_step_context_manager(mock_logger):
    """Test using step as context manager."""
    with step_start("Test step") as test_step:
        assert test_step.content == "Test step"
        assert not test_step.completed
        assert Step.get_current_step() == test_step

    assert test_step.completed
    assert Step.get_current_step() is None
    mock_logger.assert_called_once_with("1 Test step")


def test_step_nesting(mock_logger):
    """Test nested steps functionality."""
    with step_start("Parent step") as parent:
        assert parent.parent_step is None
        assert Step.get_current_step() == parent

        with step_start("Child step") as child:
            assert child.parent_step == parent
            assert Step.get_current_step() == child

            with step_start("Grandchild step") as grandchild:
                assert grandchild.parent_step == child
                assert Step.get_current_step() == grandchild

    # Verify final state
    assert parent.completed
    assert child.completed
    assert grandchild.completed
    assert Step.get_current_step() is None

    # Verify logging with proper indentation
    assert mock_logger.call_args_list[0][0][0] == "1 Parent step"
    assert mock_logger.call_args_list[1][0][0] == "1.1   Child step"
    assert mock_logger.call_args_list[2][0][0] == "1.1.1     Grandchild step"


def test_step_sequence_numbering():
    """Test step sequence numbering works correctly."""
    # Reset counter
    Step.reset_for_test()

    steps = []
    with step_start("Step 1") as root1:
        steps.append((root1, 1, None))
        with step_start("Child 1.1") as child1:
            steps.append((child1, 2, root1))
        with step_start("Child 1.2") as child2:
            steps.append((child2, 3, root1))

    with step_start("Step 2") as root2:
        steps.append((root2, 4, None))

    # Verify sequence numbers and parent relationships
    for step, expected_seq, expected_parent in steps:
        assert step.sequence_number == expected_seq
        assert step.parent_step == expected_parent


def test_step_error_handling():
    """Test step error handling."""
    error_msg = "Test error"

    try:
        with step_start("Failing step"):
            raise ValueError(error_msg)
    except ValueError as e:
        assert str(e) == error_msg
        # Step should be marked as completed even if exception occurs
        assert Step.get_current_step() is None


@step
def step_func():
    """Test function with step decorator."""
    return "result"


@step(content="Custom {param}")
def step_with_param(param):
    """Test function with parameterized step decorator."""
    return param


def test_step_decorator():
    """Test step decorator functionality."""
    # Test basic decorator
    result = step_func()
    assert result == "result"

    # Test parameterized decorator
    result = step_with_param("test")
    assert result == "test"


def test_step_content_variants():
    """Test different step content variations."""
    contents = [
        "Simple step",
        "Step with numbers 123",
        "Step with symbols !@#",
        "Multi\nline\nstep",
        "Very " * 10 + "long step"
    ]

    for content in contents:
        with step_start(content) as step:
            assert step.content == content


def test_step_concurrent_execution():
    """Test steps behavior in concurrent execution."""

    def run_step():
        with step_start("Concurrent step") as step:
            return step.sequence_number

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: run_step(), range(3)))

    # Verify all sequence numbers are unique
    assert len(set(results)) == 3


def test_step_function_name_capture():
    """Test capturing function name in steps."""

    def test_function():
        step = Step("Test step")
        assert step.step_function == "test_function"

    test_function()
