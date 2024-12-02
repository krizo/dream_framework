"""Plugin for managing test cases and execution records."""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pytest
from sqlalchemy.orm import Session

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from core.test_run import TestRun
from models.test_case_model import TestCaseModel


class TestCasePlugin:
    """Plugin for handling TestCase and TestExecutionRecord persistence."""

    _current_execution: Optional[TestExecutionRecord] = None
    _executions_by_worker: Dict[str, TestExecutionRecord] = {}

    def __init__(self, test_run: TestRun):
        """Initialize plugin with test run instance."""
        self.test_run = test_run
        self._test_executions: Dict[str, TestExecutionRecord] = {}
        self._db = AutomationDatabaseManager.get_database()

    @classmethod
    def get_current_execution(cls) -> Optional[TestExecutionRecord]:
        """Get current test execution."""
        try:
            worker = pytest.xdist.get_worker_id()
            worker_id = worker if worker else 'master'
        except (ImportError, AttributeError):
            worker_id = 'master'

        return cls._executions_by_worker.get(worker_id)

    @classmethod
    def set_current_execution(cls, execution: Optional[TestExecutionRecord]):
        """Set current test execution."""
        try:
            worker = pytest.xdist.get_worker_id()
            worker_id = worker if worker else 'master'
        except (ImportError, AttributeError):
            worker_id = 'master'

        if execution is None:
            cls._executions_by_worker.pop(worker_id, None)
        else:
            cls._executions_by_worker[worker_id] = execution

    def pytest_runtest_call(self, item):
        """Handle test execution."""
        try:
            # Ensure TestRun instance is available
            if not TestRun.get_instance():
                Log.info(f"Restoring TestRun before test execution: {self.test_run.test_run_id}")
                TestRun._instance = self.test_run

            test_full_path = item.nodeid
            test_module, test_function = test_full_path.split('::')

            # Find TestCase fixture
            test_case = None
            for arg_name, arg_value in item.funcargs.items():
                if isinstance(arg_value, TestCase):
                    test_case = arg_value
                    break

            if not test_case:
                Log.info("No TestCase fixture found - using default")
                test_case = TestCase(
                    name=test_function,
                    description=f"Auto-generated test case for {test_function}",
                    test_suite="Automated Tests",
                    scope="Unit",
                    component="Test"
                )

            test_case.set_test_location(test_module, test_function)

            with self._db.session_scope() as session:
                try:
                    # Ensure TestRun exists in database first
                    test_run_model = session.query(TestRun.get_model()) \
                        .filter_by(test_run_id=self.test_run.test_run_id) \
                        .first()

                    if not test_run_model:
                        session.add(self.test_run.to_model())
                        session.flush()

                    test_case_id = self._ensure_test_case(session, test_case)
                    test_case.id = test_case_id

                    if not TestRun.get_instance():
                        TestRun._instance = self.test_run

                    test_run_id = os.environ.get('XDIST_TEST_RUN_ID', self.test_run.test_run_id)

                    # Create execution record
                    execution_record = TestExecutionRecord(test_case)
                    execution_record.set_test_location(
                        test_module, test_function,
                        test_case.name, test_case.description
                    )
                    execution_record.initialize()
                    execution_record.start()

                    # Save execution record
                    execution_model = execution_record.to_model()
                    execution_model.test_run_id = test_run_id
                    session.add(execution_model)
                    session.flush()
                    execution_record.id = execution_model.id

                    if os.environ.get('PYTEST_XDIST_WORKER'):
                        session.commit()

                except Exception as e:
                    Log.error(f"Error in test case setup: {str(e)}")
                    session.rollback()
                    raise

                # Setup logging after ensuring execution record
                self._setup_logging(item, test_case, execution_record)

                test_case.set_execution_record(execution_record)
                self._test_executions[test_full_path] = execution_record
                self.set_current_execution(execution_record)
                Log.info(f"Test execution active with ID: {execution_record.id}")

        except Exception as e:
            Log.error(f"Error in test setup: {str(e)}")
            raise

    def _ensure_test_case(self, session: Session, test_case: TestCase) -> int:
        """Ensure test case exists in database."""
        # First try finding by test_id
        existing = session.query(TestCaseModel) \
            .filter_by(test_id=test_case.test_id) \
            .first()

        if existing:
            if self._should_update_test_case(TestCase.from_model(existing), test_case):
                Log.info(f"Updating test case {test_case.test_id}")
                existing.name = test_case.name
                existing.description = test_case.description
                existing.test_suite = test_case.test_suite
            return existing.id

        # Create new test case
        model = test_case.to_model()
        session.add(model)
        session.flush()
        Log.info(f"Created new test case with ID: {model.id}")
        return model.id

    def _should_update_test_case(self, existing: TestCase, current: TestCase) -> bool:
        """Check if test case should be updated."""
        return (
                existing.name != current.name or
                existing.description != current.description or
                existing.test_suite != current.test_suite
        )

    def _setup_logging(self, item, test_case, execution_record):
        """
        Configure logging for test execution.
        Creates log file for test in flat structure.

        @param item: pytest item
        @param test_case: current test case
        @param execution_record: current execution record
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get base log directory from test run
        test_log_dir = Path(self.test_run.get_log_dir()) / 'executions'

        worker_suffix = ""
        if os.environ.get('PYTEST_XDIST_WORKER'):
            worker_suffix = f"_{os.environ['PYTEST_XDIST_WORKER']}"

        test_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = test_log_dir / f"{test_case.test_function}{worker_suffix}_{execution_record.id}_{timestamp}.log"

        # Configure logging for this execution
        Log.switch_log_file(str(log_file))

        # Write execution header
        Log.separator("=")
        Log.info(f"Test Run ID: {self.test_run.test_run_id}")
        Log.info(f"Execution ID: {execution_record.id}")
        Log.info(f"Test Location: {test_case.test_id}")
        Log.info(f"Test Name: {test_case.name}")
        Log.info(f"Test Description: {test_case.description}")
        Log.info(f"Test Suite: {test_case.test_suite}")
        if os.environ.get('PYTEST_XDIST_WORKER'):
            Log.info(f"Worker: {os.environ['PYTEST_XDIST_WORKER']}")
        Log.separator("=")
