from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from core.logger import Log
from core.step import Step, step_start
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from helpers.decorators import step
from models.step_model import StepModel


class TestStepCase(TestCase):
    """Test case for step tests."""

    def __init__(self):
        super().__init__(
            name="Step Test Case",
            description="Test case for testing steps functionality",
            test_suite="Step Tests",
            scope="Unit",
            component="Steps"
        )


@pytest.fixture
def step_test_case():
    """Fixture providing test case for steps."""
    return TestStepCase()


@pytest.fixture
def mock_db_session():
    """Fixture providing mocked database session with simulated flush."""
    session = MagicMock()

    # Simulate database operations
    def simulate_flush():
        if hasattr(session, 'add') and session.add.call_args:
            last_model = session.add.call_args[0][0]
            if not last_model.id:
                last_model.id = len(session.add.call_args_list)

    session.flush.side_effect = simulate_flush

    # Configure query mock for updates
    query_mock = MagicMock()
    filter_by_mock = MagicMock()
    update_mock = MagicMock()

    query_mock.filter_by.return_value = filter_by_mock
    filter_by_mock.update.return_value = update_mock
    session.query.return_value = query_mock

    return session


@pytest.fixture
def mock_db(mock_db_session):
    """Fixture providing mocked database with session."""
    db = MagicMock()
    db.session_scope.return_value.__enter__.return_value = mock_db_session
    return db


@pytest.fixture
def execution_record(step_test_case, mock_db_session):
    """Fixture providing test execution record."""
    record = TestExecutionRecord(step_test_case)
    record.id = 1
    record.test_function = "test_function"
    record._db_session = mock_db_session
    return record


@pytest.mark.no_database_plugin
def test_step_basic_creation():
    """Test basic step creation."""
    Step.reset_for_test()
    step = Step("Test step")
    assert step.content == "Test step"
    assert step.completed is False
    assert step.parent_step is None
    assert step.step_id.startswith("step_")


def test_step_context_manager(execution_record, mock_db):
    """Test using step as context manager."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with step_start("Test step") as test_step:
            assert test_step.content == "Test step"
            assert not test_step.completed

        assert test_step.completed


def test_step_nesting(execution_record, mock_db):
    """Test nested steps functionality."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with step_start("Parent step") as parent:
            assert parent.parent_step is None
            with step_start("Child step") as child:
                assert child.parent_step == parent
                with step_start("Grandchild step") as grandchild:
                    assert grandchild.parent_step == child


def test_step_sequence_numbering(execution_record, mock_db):
    """Test step sequence numbering and nesting."""
    Step.reset_for_test()
    steps = []

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with step_start("Step 1") as root1:  # level 0
            steps.append(root1)
            with step_start("Child 1.1") as child1:  # level 1
                steps.append(child1)
            with step_start("Child 1.2") as child2:  # level 1
                steps.append(child2)

        with step_start("Step 2") as root2:  # level 0
            steps.append(root2)

        # Verify sequence numbers
        assert len(steps) == 4, "Expected 4 steps"
        expected_numbers = [1, 2, 3, 4]
        actual_numbers = [s.sequence_number for s in steps]
        assert actual_numbers == expected_numbers, \
            f"Expected sequence numbers {expected_numbers}, got {actual_numbers}"

        # Verify nesting levels
        nesting_levels = [s._get_nesting_level() for s in steps]
        expected_levels = [0, 1, 1, 0]
        assert nesting_levels == expected_levels, \
            f"Expected nesting levels {expected_levels}, got {nesting_levels}"

        # Verify parent-child relationships
        assert steps[0].parent_step is None, "Root1 should have no parent"
        assert steps[1].parent_step == steps[0], "Child1.1 should be child of Root1"
        assert steps[2].parent_step == steps[0], "Child1.2 should be child of Root1"
        assert steps[3].parent_step is None, "Root2 should have no parent"

        # Verify completion
        assert all(step.completed for step in steps), "All steps should be completed"


def test_step_decorator(execution_record, mock_db):
    """Test step decorator usage."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        @step
        def test_step():
            return "test"

        @step(content="Custom step")
        def custom_step():
            return "custom"

        assert test_step() == "test"
        assert custom_step() == "custom"


def test_step_error_handling(execution_record, mock_db):
    """Test step error handling."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with pytest.raises(ValueError):
            with step_start("Failing step"):
                raise ValueError("Test error")


def test_step_logging(execution_record, mock_db):
    """Test step logging functionality."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db), \
            patch.object(Log, 'step') as mock_log:
        with step_start("Test step"):
            pass
        mock_log.assert_called_once()
        assert "Test step" in mock_log.call_args[0][0]


def test_step_database_persistence(execution_record, mock_db, mock_db_session):
    """Test step persistence in database."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with step_start("Test step"):
            mock_db_session.add.assert_called_once()
            added_model = mock_db_session.add.call_args[0][0]
            assert isinstance(added_model, StepModel)
            assert added_model.content == "Test step"


def test_step_persistence_on_failure(execution_record, mock_db, mock_db_session):
    """Test step persistence when steps fail."""
    Step.reset_for_test()

    mock_db.session_scope.return_value.__enter__.return_value = mock_db_session

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
         patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):

        # First successful step
        with step_start("Parent step") as parent:
            assert parent.id is not None, "Parent step should have ID assigned"
            assert parent.parent_step is None, "Parent should have no parent"
            parent_id = parent.id

            try:
                # This step will fail
                with step_start("Failing step") as failing:
                    assert failing.parent_step is parent, "Failing step should have parent"
                    raise ValueError("Expected failure")
            except ValueError:
                pass

            # Check if parent is still current step
            current = Step.get_current_step()
            assert current is parent, "Parent should be current step after failure"

            # This step should be sibling to failing step
            with step_start("Sibling step") as sibling:
                assert sibling.id is not None, "Sibling step should have ID assigned"
                assert sibling.parent_step is parent, \
                    f"Sibling should have parent {parent.content}, got {sibling.parent_step.content if sibling.parent_step else None}"
                assert sibling.parent_step.id == parent_id, "Parent ID should match"

        # Verify all steps were persisted
        persisted_models = [
            args[0][0] for args in mock_db_session.add.call_args_list
            if isinstance(args[0][0], StepModel)
        ]

        assert len(persisted_models) == 3, "Expected three steps to be persisted"

        # Check step hierarchy
        for model in persisted_models:
            if model.content == "Parent step":
                assert model.parent_step_id is None, "Parent should have no parent"
            else:
                assert model.parent_step_id == parent_id, \
                    f"Step {model.content} should have parent_id={parent_id}, got {model.parent_step_id}"

@pytest.mark.no_database_plugin
def test_step_xdist_compatibility():
    """Test pytest-xdist compatibility."""
    Step.reset_for_test()

    with patch('os.environ', {'PYTEST_XDIST_WORKER': 'gw1'}):
        assert Step._get_worker_id() == 'gw1'

        # Verify worker-specific state
        Step._last_sequence_by_worker['gw1'] = 5
        assert Step._get_and_increment_sequence() == 6

        Step.reset_worker()
        assert 'gw1' not in Step._last_sequence_by_worker


def test_nested_step_indentation(execution_record, mock_db, mock_db_session):
    """Test proper indentation in nested steps logging."""
    Step.reset_for_test()

    # Mock database query for hierarchical number calculation
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.count.return_value = 0
    query_mock.filter.return_value = filter_mock
    mock_db_session.query.return_value = query_mock

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db), \
            patch.object(Log, 'step') as mock_log:

        with step_start("Parent"):
            assert mock_log.call_args[0][0] == "1 Parent"

            with step_start("Child"):
                assert mock_log.call_args[0][0] == "1.1   Child"

                with step_start("Grandchild"):
                    assert mock_log.call_args[0][0] == "1.1.1     Grandchild"


def test_step_with_parameters(execution_record, mock_db):
    """Test step decorator with parameters."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        @step(content="Processing {param}")
        def parameterized_step(param):
            return param

        result = parameterized_step("test")
        assert result == "test"


@pytest.mark.no_database_plugin
def test_no_execution_record_handling():
    """Test handling when no execution record is available."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=None), \
            patch.object(Log, 'warning') as mock_warning:
        with step_start("Test step") as step:
            assert step is None
        mock_warning.assert_called_once()


@pytest.mark.no_database_plugin
def test_step_function_name_capture():
    """Test capturing the correct function name for steps."""
    Step.reset_for_test()

    def test_function():
        step = Step("Test step")
        assert step.step_function == "test_function"

    test_function()


@pytest.mark.parametrize("step_content", [
    "Simple step",
    "Step with numbers 123",
    "Step with symbols !@#",
    "Multi\nline\nstep",
    "Very " * 10 + "long step"
])
def test_step_content_variants(step_content, execution_record, mock_db):
    """Test different variants of step content."""
    Step.reset_for_test()

    with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
            patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
        with step_start(step_content) as step:
            assert step.content == step_content


def test_concurrent_steps(execution_record, mock_db):
    """Test steps behavior in concurrent execution."""
    Step.reset_for_test()

    def run_step():
        with patch('core.plugins.test_case_plugin.TestCasePlugin.get_current_execution', return_value=execution_record), \
                patch('core.step.AutomationDatabaseManager.get_database', return_value=mock_db):
            with step_start("Concurrent step") as step:
                return step.sequence_number

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: run_step(), range(3)))

    # Verify sequence numbers
    assert len(set(results)) == 3, "Each concurrent step should have unique sequence number"
