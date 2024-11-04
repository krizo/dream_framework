import inspect
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Dict, Generator

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from models.step_model import StepModel


class Step:
    """
    Class representing a test step with support for nesting and tracking execution.
    Steps are persisted in database and logged during test execution.
    """
    _steps_by_worker: Dict[str, 'Step'] = {}  # For pytest-xdist support
    _step_sequence_by_worker: Dict[str, int] = {}
    _last_sequence_by_worker: Dict[str, int] = {}  # Track last sequence number per worker

    def __init__(self, content: str):
        """
        Initialize new step.

        @param content: Step description/content
        """
        sequence = self._get_and_increment_sequence()
        timestamp = int(time.time() * 1000000)  # Use microseconds for uniqueness
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

        frame = inspect.currentframe()
        try:
            while frame:
                if frame.f_code.co_name != '__init__':
                    self.step_function = frame.f_code.co_name
                    break
                frame = frame.f_back
        finally:
            del frame

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
        """
        Get currently executing step.

        @return: Current step or None if no step is executing
        """
        return cls._steps_by_worker.get(cls._get_worker_id())

    @classmethod
    def set_current_step(cls, step: Optional['Step']) -> None:
        """
        Set current step for execution tracking.

        @param step: Step to set as current or None to clear
        """
        worker_id = cls._get_worker_id()
        if step is None:
            cls._steps_by_worker.pop(worker_id, None)
        else:
            cls._steps_by_worker[worker_id] = step

    @classmethod
    def _get_and_increment_sequence(cls) -> int:
        """
        Get next sequence number for current worker and increment counter.

        @return: Next sequence number
        """
        worker_id = cls._get_worker_id()
        current = cls._last_sequence_by_worker.get(worker_id, 0)
        next_sequence = current + 1
        cls._last_sequence_by_worker[worker_id] = next_sequence
        return next_sequence

    @classmethod
    def _get_worker_id(cls) -> str:
        """
        Get current worker ID for pytest-xdist support.
        Falls back to 'master' if not running under xdist.

        @return: Worker ID string ('gw0', 'gw1', etc.) or 'master' if not using xdist
        """
        try:
            import os
            return os.environ.get('PYTEST_XDIST_WORKER', 'master')
        except Exception:
            return 'master'

    @classmethod
    def _get_current_step(cls) -> Optional['Step']:
        """Get current step for this worker."""
        worker_id = cls._get_worker_id()
        return cls._steps_by_worker.get(worker_id)

    @classmethod
    def _set_current_step(cls, step: Optional['Step']):
        """Set current step for this worker."""
        worker_id = cls._get_worker_id()
        if step is None:
            cls._steps_by_worker.pop(worker_id, None)
        else:
            cls._steps_by_worker[worker_id] = step

    def _calculate_hierarchical_number(self, session, execution_record_id: int) -> str:
        """
        Calculate hierarchical step number (e.g., 1.2.3).

        @param session: Database session
        @param execution_record_id: ID of current execution record
        @return: Hierarchical number string
        """
        if not self.parent_step:
            # Get count of root steps for this execution
            count = session.query(StepModel).filter(
                StepModel.execution_record_id == execution_record_id,
                StepModel.parent_step_id.is_(None)
            ).count()
            return str(count + 1)

        # Get parent's hierarchical number
        parent_number = self.parent_step.hierarchical_number

        # Get count of siblings
        siblings_count = session.query(StepModel).filter(
            StepModel.execution_record_id == execution_record_id,
            StepModel.parent_step_id == self.parent_step.id
        ).count()

        return f"{parent_number}.{siblings_count + 1}"

    @classmethod
    def _get_sequence(cls) -> int:
        """Get current step sequence for this worker."""
        worker_id = cls._get_worker_id()
        return cls._step_sequence_by_worker.get(worker_id, 0)

    def _get_step_pattern(self) -> str:
        """
        Get regex pattern for matching 'Step X:' prefix in text.

        @return: Regular expression pattern
        """
        return rf"^Step {self.sequence_number}:\s*"

    def _clean_content(self, content: str) -> str:
        """
        Clean step number prefix from content if exists.

        @param content: Original content
        @return: Cleaned content without step number prefix
        """
        import re
        return re.sub(self._get_step_pattern(), '', content)

    def start(self, session, execution_record) -> None:
        """
        Start step execution and persist initial state.

        @param session: Database session from session_scope
        @param execution_record: Current test execution record
        """
        self.start_time = datetime.now()

        # Calculate hierarchy information
        self.indent_level = self._calculate_indent_level()
        self.hierarchical_number = self._calculate_hierarchical_number(session, execution_record.id)

        # Clean content before saving
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
        """
        Mark step as completed and update in database.

        @param session: Database session from session_scope
        """
        self.completed = True
        if self.id:
            session.query(StepModel).filter_by(id=self.id).update({"completed": True})

        if Step._get_current_step() == self:
            Step._set_current_step(self.parent_step)

    def _log_step(self) -> None:
        """Log step execution with proper indentation."""
        indent = "  " * self.indent_level
        Log.step(f"{self.hierarchical_number} {indent}{self.content}")

    def _calculate_indent_level(self) -> int:
        """Calculate step indentation level."""
        level = 0
        current = self.parent_step
        while current:
            level += 1
            current = current.parent_step
        return level

    def _get_nesting_level(self) -> int:
        """
        Calculate step nesting level.

        @return: Nesting level (0 for root steps)
        """
        if not self.parent_step:
            return 0

        level = 0
        current = self.parent_step
        while current:
            level += 1
            current = current.parent_step
        return level

    @classmethod
    def reset_all(cls) -> None:
        """Reset all step data for all workers."""
        cls._steps_by_worker.clear()
        cls._step_sequence_by_worker.clear()
        cls._last_sequence_by_worker.clear()

    @classmethod
    def reset_worker(cls) -> None:
        """Reset step data for current worker."""
        worker_id = cls._get_worker_id()
        cls._steps_by_worker.pop(worker_id, None)
        cls._step_sequence_by_worker.pop(worker_id, None)
        cls._last_sequence_by_worker.pop(worker_id, None)

    @classmethod
    def reset_for_test(cls) -> None:
        """
        Reset all step data and initialize counters for testing.
        Should be used only in tests to ensure clean state.
        """
        cls._steps_by_worker.clear()
        cls._step_sequence_by_worker.clear()
        cls._last_sequence_by_worker.clear()
        worker_id = cls._get_worker_id()
        cls._last_sequence_by_worker[worker_id] = 0


@contextmanager
def step_start(content: str, function_name: Optional[str] = None) -> Generator[Optional[Step], None, None]:
    """
    Context manager for step execution.
    Creates, starts, and completes step with proper cleanup.

    @param content: Step description
    @param function_name: Name of the original function (for decorated functions)
    @yield: Step instance or None if no execution record is found
    """

    from core.plugins.test_case_plugin import TestCasePlugin


    step = None
    execution_record = TestCasePlugin.get_current_execution()
    parent_step = Step.get_current_step()  # Get current step as parent

    if not execution_record:
        Log.warning(f"No active test execution found for step: {content}")
        yield None
        return

    db = AutomationDatabaseManager.get_database()

    try:
        with db.session_scope() as session:
            # Create new step with proper parent
            step = Step(content)
            step.parent_step = parent_step  # Set parent before starting

            # Set function name if provided (from decorator)
            # Otherwise, get it from the call stack
            if function_name:
                step.step_function = function_name
            else:
                frame = inspect.currentframe().f_back
                while frame:
                    if frame.f_code.co_name not in ['step_start', '__enter__', '__exit__']:
                        step.step_function = frame.f_code.co_name
                        break
                    frame = frame.f_back

            # Store the current step for nested steps
            Step.set_current_step(step)

            # Start the step (this will create DB record)
            step.start(session, execution_record)

            yield step

            # Complete the step
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
        # Restore parent step as current
        Step.set_current_step(parent_step)
