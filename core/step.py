"""Module for managing test steps with execution tracking."""
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Generator, Optional

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from models.step_model import StepModel


class Step:
    """
    Class representing a test step with support for nesting and execution tracking.
    Steps are persisted in database and logged during test execution.
    """

    # Class level attributes for tracking steps across workers
    _steps_by_worker: Dict[str, 'Step'] = {}
    _step_sequence_by_worker: Dict[str, int] = {}
    _last_sequence_by_worker: Dict[str, int] = {}

    def __init__(self, content: str):
        """Initialize new step."""
        sequence = self._get_and_increment_sequence()
        timestamp = int(datetime.now().timestamp() * 1000000)  # microseconds
        worker_id = self._get_worker_id()
        self.step_id = f"step_{timestamp}_{worker_id}_{sequence}"

        self.content = content
        self.completed = False
        self.start_time = None
        self.id = None
        self._parent_step = None
        self.sequence_number = sequence
        self.indent_level = 0
        self.hierarchical_number = ""
        self.step_function = self._get_function_name()

    def _get_function_name(self) -> str:
        """Get name of the function containing this step."""
        import inspect
        for frame in inspect.stack()[1:]:
            if frame.function not in ['__init__', 'step_start', '__exit__']:
                return frame.function
        return "unknown"

    @classmethod
    def _get_and_increment_sequence(cls) -> int:
        """Get next sequence number for current worker and increment counter."""
        worker_id = cls._get_worker_id()
        current = cls._last_sequence_by_worker.get(worker_id, 0)
        next_sequence = current + 1
        cls._last_sequence_by_worker[worker_id] = next_sequence
        return next_sequence

    @property
    def parent_step(self) -> Optional['Step']:
        """Get parent step."""
        return self._parent_step

    @parent_step.setter
    def parent_step(self, parent: Optional['Step']) -> None:
        """Set parent step."""
        self._parent_step = parent

    @classmethod
    def get_current_step(cls) -> Optional['Step']:
        """Get currently executing step."""
        worker_id = cls._get_worker_id()
        return cls._steps_by_worker.get(worker_id)

    @classmethod
    def set_current_step(cls, step: Optional['Step']) -> None:
        """Set current step for execution tracking."""
        worker_id = cls._get_worker_id()
        if step is None:
            cls._steps_by_worker.pop(worker_id, None)
        else:
            cls._steps_by_worker[worker_id] = step

    @classmethod
    def _get_worker_id(cls) -> str:
        """Get current worker ID for pytest-xdist support."""
        try:
            import pytest
            worker = pytest.xdist.get_worker_id()
            return worker if worker else 'master'
        except (ImportError, AttributeError):
            return 'master'

    @classmethod
    def reset_worker(cls) -> None:
        """Reset step data for current worker."""
        worker_id = cls._get_worker_id()
        cls._steps_by_worker.pop(worker_id, None)
        cls._step_sequence_by_worker.pop(worker_id, None)
        cls._last_sequence_by_worker.pop(worker_id, None)

    @classmethod
    def reset_all(cls) -> None:
        """Reset all step data for all workers."""
        cls._steps_by_worker.clear()
        cls._step_sequence_by_worker.clear()
        cls._last_sequence_by_worker.clear()

    @classmethod
    def reset_for_test(cls) -> None:
        """Reset all step data and initialize counters for testing."""
        cls.reset_all()
        worker_id = cls._get_worker_id()
        cls._last_sequence_by_worker[worker_id] = 0

    def start(self, session, execution_record) -> None:
        """Start step execution and persist initial state."""
        self.start_time = datetime.now()
        self.indent_level = self._calculate_indent_level()
        self.hierarchical_number = self._calculate_hierarchical_number(session, execution_record.id)

        cleaned_content = self._clean_content(self.content)
        model = StepModel(
            step_id=self.step_id,
            sequence_number=self.sequence_number,
            hierarchical_number=self.hierarchical_number,
            indent_level=self.indent_level,
            parent_step_id=self.parent_step.id if self.parent_step else None,
            step_function=self.step_function,
            content=cleaned_content,
            execution_record_id=execution_record.id,
            test_function=execution_record.test_function,
            start_time=self.start_time,
            completed=False
        )

        session.add(model)
        session.flush()
        self.id = model.id
        self.content = cleaned_content
        self._log_step()

    def complete(self, session) -> None:
        """Mark step as completed and update in database."""
        self.completed = True
        if self.id:
            session.query(StepModel).filter_by(id=self.id).update({"completed": True})
        
        if Step.get_current_step() == self:
            Step.set_current_step(self.parent_step)

    def _log_step(self) -> None:
        """Log step execution with proper indentation."""
        indent = "  " * self.indent_level
        Log.step(f"{self.hierarchical_number} {indent}{self.content}")

    def _calculate_hierarchical_number(self, session, execution_record_id: int) -> str:
        """Calculate hierarchical step number (e.g., 1.2.3)."""
        if not self.parent_step:
            count = session.query(StepModel).filter(
                StepModel.execution_record_id == execution_record_id,
                StepModel.parent_step_id.is_(None)
            ).count()
            return str(count + 1)

        parent_number = self.parent_step.hierarchical_number
        siblings_count = session.query(StepModel).filter(
            StepModel.execution_record_id == execution_record_id,
            StepModel.parent_step_id == self.parent_step.id
        ).count()

        return f"{parent_number}.{siblings_count + 1}"

    def _calculate_indent_level(self) -> int:
        """Calculate step indentation level."""
        level = 0
        current = self.parent_step
        while current:
            level += 1
            current = current.parent_step
        return level

    def _clean_content(self, content: str) -> str:
        """Clean step content."""
        import re
        pattern = rf"^Step {self.sequence_number}:\s*"
        return re.sub(pattern, '', content)


@contextmanager
def step_start(content: str, function_name: Optional[str] = None) -> Generator[Optional[Step], None, None]:
    """Context manager for step execution."""
    from core.plugins.test_case_plugin import TestCasePlugin
    execution_record = TestCasePlugin.get_current_execution()
    parent_step = Step.get_current_step()

    if not execution_record:
        Log.warning(f"No active test execution found for step: {content}")
        yield None
        return

    db = AutomationDatabaseManager.get_database()
    step = None

    try:
        with db.session_scope() as session:
            step = Step(content)
            step.parent_step = parent_step

            if function_name:
                step.step_function = function_name

            Step.set_current_step(step)
            step.start(session, execution_record)
            yield step
            step.complete(session)

    except Exception as e:
        Log.error(f"Step failed: {str(e)}")
        if step and step.id:
            try:
                with db.session_scope() as session:
                    step.complete(session)
            except Exception as db_error:
                Log.error(f"Failed to complete step: {str(db_error)}")
        raise

    finally:
        Step.set_current_step(parent_step)