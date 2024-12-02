"""Plugin responsible for managing test session and its plugins."""
import logging
import os
from datetime import datetime
from sqlite3 import IntegrityError

from core.automation_database_manager import AutomationDatabaseManager
from core.configuration.framework_config import FrameworkConfig
from core.logger import Log
from core.plugins.test_case_plugin import TestCasePlugin
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult
from core.test_run import TestRun, TestRunType
from models.custom_metric_model import CustomMetricModel
from models.test_case_execution_record_model import TestExecutionRecordModel


class TestSessionPlugin:
    """Plugin responsible for managing test session and its plugins."""

    def __init__(self):
        """Initialize plugin state."""
        self.test_run = None
        self.test_case_plugin = None
        self._current_test = None
        self._is_xdist = False
        self._log_configured = False
        self._log_file = None
        self._log_handler = None

    def pytest_configure(self, config):
        """
        Configure test session and initialize test run infrastructure.
        Handles different setup for master vs worker nodes in both single and distributed testing modes.

        @param config: pytest Configuration object
        @raises RuntimeError: If worker can't find test run ID or test run in database
        """
        # Detect if running in distributed mode (pytest-xdist)
        self._is_xdist = bool(config.getoption('dist', 'no') != 'no')
        worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')

        # Master node configuration - responsible for test run initialization
        if worker_id == 'master':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

            # Generate unique test run ID based on mode
            if self._is_xdist:
                test_run_id = f"test_run_xdist_{timestamp}"
                os.environ['XDIST_TEST_RUN_ID'] = test_run_id
                test_type = TestRunType.XDIST
            else:
                test_run_id = f"test_run_local_single_{timestamp}"
                test_type = TestRunType.SINGLE

            # Initialize test run and persist in database within a transaction
            db = AutomationDatabaseManager.get_database()
            with db.session_scope() as session:
                test_run = TestRun.initialize(
                    owner=FrameworkConfig.get_test_owner(),
                    environment=FrameworkConfig.get_test_environment(),
                    worker_id=worker_id,
                    test_run_id=test_run_id,
                    test_type=test_type
                )

                # Save to database only if it's a new test run
                try:
                    existing = session.query(TestRun.get_model()) \
                        .filter_by(test_run_id=test_run.test_run_id) \
                        .first()

                    if existing is None:
                        test_run_model = test_run.to_model()
                        session.add(test_run_model)
                        session.commit()
                        Log.info(f"Created new test run with ID: {test_run.test_run_id}")
                    else:
                        Log.info(f"Using existing test run with ID: {test_run.test_run_id}")

                except IntegrityError:
                    session.rollback()
                    Log.info(f"Test run {test_run.test_run_id} already exists in database")

                self.test_run = test_run
        else:
            test_run_id = os.environ.get('XDIST_TEST_RUN_ID')
            if not test_run_id:
                raise RuntimeError("Missing test run ID in xdist worker."
                                   "Ensure master node properly initialized the test run.")

            # Retrieve test run data from database
            db = AutomationDatabaseManager.get_database()
            with db.session_scope() as session:
                test_run_model = session.query(TestRun.get_model()) \
                    .filter_by(test_run_id=test_run_id) \
                    .first()

                if not test_run_model:
                    raise RuntimeError(f"Test run {test_run_id} not found in database")

                self.test_run = TestRun(
                    owner=test_run_model.owner,
                    environment=test_run_model.environment,
                    worker_id=worker_id,
                    test_run_id=test_run_model.test_run_id,
                    test_type=TestRunType(test_run_model.test_type)
                )

        self._setup_test_run_logging()
        self.test_case_plugin = TestCasePlugin(self.test_run)
        config.pluginmanager.register(self.test_case_plugin)

    def pytest_runtest_setup(self, item):
        """
        Setup before each test.
        Ensures logging is properly configured.

        @param item: pytest test item
        """
        # Ensure log handler is active
        if not self._log_configured or not self._log_file.exists():
            print("WARNING: Log configuration lost, reconfiguring...")  # Debug
            self._setup_test_run_logging()
        else:
            print(
                f"Log file status before test: exists={self._log_file.exists()}, size={self._log_file.stat().st_size}")  # Debug

    def pytest_runtest_makereport(self, item, call):
        """Handle test reports and finalize test executions."""
        if call.when == "call":  # Test has finished executing
            test_execution = self.test_case_plugin.get_current_execution()
            if test_execution:
                result = TestResult.PASSED if call.excinfo is None else TestResult.FAILED

                if call.excinfo:
                    test_execution.set_failure(
                        str(call.excinfo.value),
                        call.excinfo.type.__name__
                    )

                # Finalize execution
                test_execution.end(result)

                # Update database state
                db = AutomationDatabaseManager.get_database()
                ExecutionModel = TestExecutionRecord.get_model()

                try:
                    with db.session_scope() as session:
                        existing = session.query(ExecutionModel) \
                            .filter_by(
                            test_case_id=test_execution.test_case.id,
                            test_run_id=self.test_run.test_run_id,
                            test_function=test_execution.test_function
                        ).first()

                        if existing:
                            existing.result = result.value
                            existing.end_time = test_execution.end_time
                            existing.duration = test_execution.duration
                            existing.failure = test_execution.failure
                            existing.failure_type = test_execution.failure_type

                            # Update metrics
                            existing.custom_metrics.clear()
                            for metric in test_execution.get_all_metrics():
                                existing.custom_metrics.append(
                                    CustomMetricModel(
                                        name=metric['name'],
                                        value=metric['value']
                                    )
                                )
                        else:
                            Log.warning("No execution record found to update")

                except Exception as e:
                    Log.error(f"Failed to update execution record: {str(e)}")
                    raise

    def pytest_sessionfinish(self, session, exitstatus):
        """
        Handle test session completion.
        Updates test run status and ensures all logs are written.

        @param session: pytest session object
        @param exitstatus: session exit status
        """
        if exitstatus == 0:
            self.test_run.complete()

            # Switch to test run log
            Log.switch_log_file(str(self._log_file))

            Log.separator("=")
            Log.info("Test Run Summary")
            Log.separator("-")

            # Get all executions for this run
            db = AutomationDatabaseManager.get_database()
            try:
                with db.session_scope() as session:
                    # Update TestRun in the DB:
                    existing = session.query(TestRun.get_model()) \
                        .filter_by(test_run_id=self.test_run.test_run_id) \
                        .first()
                    if existing:
                        existing.status = self.test_run.status.value
                        existing.end_time = self.test_run.end_time
                        existing.duration = self.test_run.duration

                    # Fetching execution records for summary
                    executions = session.query(TestExecutionRecordModel) \
                        .filter(TestExecutionRecordModel.test_run_id == self.test_run.test_run_id) \
                        .order_by(TestExecutionRecordModel.start_time) \
                        .all()

                    # Log summary stats
                    total = len(executions)
                    passed = sum(1 for e in executions if e.result == TestResult.PASSED.value)
                    failed = sum(1 for e in executions if e.result == TestResult.FAILED.value)

                    Log.info(f"Total tests: {total}")
                    Log.info(f"Passed: {passed}")
                    Log.info(f"Failed: {failed}")
                    Log.separator("-")

                    # Log individual test results
                    for execution in executions:
                        Log.info(f"Test: {execution.test_function}")
                        Log.info(f"  Result: {execution.result}")
                        if execution.duration:
                            Log.info(f"  Duration: {execution.duration:.2f}s")
                        else:
                            Log.warning("  Duration: N/A")
                        if execution.failure:
                            Log.info(f"  Failure: {execution.failure}")

                        # Log metrics
                        metrics = [m for m in execution.custom_metrics]
                        if metrics:
                            Log.info("  Metrics:")
                            for metric in metrics:
                                Log.info(f"    {metric.name}: {metric.value}")
                        Log.separator("-")

                    Log.info(f"Test run {self.test_run.test_run_id} completed in {self.test_run.duration:.2f}s")
                    Log.separator("=")
                    session.commit()

            except Exception as e:
                Log.error(f"Error updating test run state: {str(e)}")
                raise

    def pytest_runtest_teardown(self, item):
        """
        Cleanup after each test.
        Ensures logs are flushed and synced to disk.

        @param item: pytest test item
        """
        try:
            logger = Log.get_logger()
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.flush()
                    os.fsync(handler.stream.fileno())  # Force write to disk

            print(
                f"Flushed and synced handlers after test: {item.name}, log size={self._log_file.stat().st_size}")  # Debug
        except Exception as e:
            print(f"Error in test teardown: {str(e)}")  # Debug

    def _create_log_file(self) -> None:
        """
        Create log file and directory structure.
        Ensures log directory exists and creates/truncates log file.
        """
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._log_file.touch(exist_ok=True)
        self._log_file.write_text("")  # Clear any existing content

    def _setup_test_run_logging(self) -> None:
        """
        Configure logging for test run.
        Creates main test run log file.
        """
        if self._log_configured:
            return

        # Create log path for test run
        log_dir = self.test_run.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = log_dir / f"{self.test_run.test_run_id}.log"

        # calculate the dates between two days

        # Configure main test run logging
        Log.reconfigure_file_handler(str(self._log_file))

        # Log test run info - only setup
        Log.separator("=")
        Log.info(f"Starting Test Run: {self.test_run.test_run_id}")
        Log.info(f"Type: {self.test_run.test_type.value}")
        Log.info(f"Environment: {self.test_run.environment}")
        Log.info(f"Owner: {self.test_run.owner}")
        Log.info(f"Start Time: {self.test_run.start_time}")
        Log.info(f"Application: {self.test_run.app_under_test} v{self.test_run.app_version}")
        if self.test_run.build_id:
            Log.info(f"Build ID: {self.test_run.build_id}")
        Log.info(f"Branch: {self.test_run.branch}")
        Log.separator("=")

        self._log_configured = True

    def _ensure_log_handler(self) -> None:
        """
        Ensure log handler is active and properly configured.
        Re-adds handler if it was removed or not found.
        """
        if not self._log_handler:
            return

        logger = Log.get_logger()
        if self._log_handler not in logger.handlers:
            logger.addHandler(self._log_handler)
