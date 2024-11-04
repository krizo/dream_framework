from pathlib import Path
from typing import List, Tuple

import pytest

from core.step import step_start
from core.test_case import TestCase
from models.step_model import StepModel


class ComplexWorkflowTest(TestCase):
    """Test case for complex workflow simulation."""

    def __init__(self):
        super().__init__(
            name="Complex Workflow Integration Test",
            description="Testing step hierarchies and persistence in real database",
            test_suite="Integration Tests",
            scope="E2E",
            component="Steps"
        )


@pytest.fixture
def workflow_test():
    return ComplexWorkflowTest()


def get_log_entries(log_file: Path) -> List[str]:
    """Helper function to read step entries from log file."""
    step_entries = []
    with open(log_file, 'r') as f:
        for line in f:
            if '| STEP     |' in line:
                step_content = line.split('| STEP     |')[1].strip()
                step_entries.append(step_content)
    return step_entries


def verify_step_hierarchy(steps: List[StepModel], expected_hierarchy: List[Tuple[int, str, int]]):
    """
    Verify step hierarchy matches expected structure.
    
    @param steps: List of step models from database
    @param expected_hierarchy: List of tuples (sequence_number, content, expected_parent_id)
    """
    step_map = {step.sequence_number: step for step in steps}

    for seq_num, content, parent_seq in expected_hierarchy:
        step = step_map[seq_num]
        assert step.content == content, f"Step {seq_num} content mismatch"

        if parent_seq == 0:  # Root step
            assert step.parent_step_id is None, f"Step {seq_num} should be root"
        else:
            parent = step_map[parent_seq]
            assert step.parent_step_id == parent.id, \
                f"Step {seq_num} should have parent {parent_seq}"


def test_complex_workflow_with_steps(workflow_test, real_db):
    """
    Complex integration test for steps with database verification.
    Tests various step patterns including:
    - Nested steps
    - Sequential steps
    - Steps with decorators
    - Step content variations
    """
    from helpers.decorators import step

    @step(content="Processing item {item}")  # Now step should be properly imported
    def process_item(item: str):
        with step_start(f"Validating {item}"):
            pass
        with step_start(f"Transforming {item}"):
            with step_start("Applying rules"):
                pass
        with step_start(f"Saving {item}"):
            pass
        return f"Processed {item}"

    @step  # Simple decorator without parameters
    def cleanup_operation():
        return "Cleanup completed"

    @step(content="Working with {first} and {second}")
    def multiple_params(first: str, second: str):
        with step_start(f"Combining {first} + {second}"):
            pass
        return f"{first}-{second}"

    @step(content="Static content")
    def static_step():
        pass

    # Main test execution
    with step_start("Initialize workflow") as init_step:
        with step_start("Setup environment"):
            with step_start("Configure settings"):
                pass
            with step_start("Verify configuration"):
                pass

        with step_start("Process items"):
            items = ["A", "B", "C"]
            for item in items:
                process_item(item)  # This should now work with parameters

        # Testing different parameter patterns
        multiple_params("X", "Y")
        multiple_params(first="P", second="Q")
        static_step()
        cleanup_operation()

    # Database verification
    with real_db.session_scope() as session:
        steps = session.query(StepModel) \
            .filter(StepModel.test_function == workflow_test._execution_record.test_function) \
            .order_by(StepModel.sequence_number) \
            .all()

        # Basic verification
        assert len(steps) > 0, "No steps found in database"
        assert all(step.completed for step in steps), "All steps should be completed"
        assert all(step.execution_record_id == workflow_test._execution_record.id for step in steps), \
            "All steps should be linked to test execution"

        # Print steps for debugging
        print("\nTest execution summary:")
        print(f"Total steps: {len(steps)}")
        for step in steps:
            print(f"Step {step.sequence_number}: {step.content} " +
                  f"(Parent: {step.parent_step_id})")

        # Sequence verification
        sequence_numbers = [step.sequence_number for step in steps]
        assert sequence_numbers == list(range(1, len(steps) + 1)), \
            f"Expected sequence numbers {list(range(1, len(steps) + 1))}, got {sequence_numbers}"

        # Content verification
        assert any("Processing item A" in step.content for step in steps), \
            "Missing 'Processing item A' step"
        assert any("Working with X and Y" in step.content for step in steps), \
            "Missing multiple parameters step"
        assert any("Static content" in step.content for step in steps), \
            "Missing static content step"
