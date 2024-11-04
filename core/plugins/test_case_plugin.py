import logging
import logging.config
from datetime import datetime
from typing import Dict

import pytest

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from core.test_result import TestResult


class TestNotFoundException(Exception):
    """Raised when TestCase fixture is not found in test."""
    pass


class TestCasePlugin:
    """
    Plugin for handling TestCase and TestExecutionRecord persistence during test execution.
    Ensures unique test cases based on module and function location.
    """
    _test_executions: Dict[str, TestExecutionRecord] = {}

    @staticmethod
    def _find_test_case_fixture(item) -> TestCase:
        """
        Find TestCase fixture in pytest item.

        @param item: pytest item
        @return: TestCase instance
        @raises TestNotFoundException: If no TestCase fixture is found
        """
        try:
            return next(fixture for fixture in item.funcargs.values() if isinstance(fixture, TestCase))
        except StopIteration:
            raise TestNotFoundException(
                "No TestCase fixture found. Each test must have a TestCase fixture provided."
            )

    @staticmethod
    def _setup_logging(item, test_case: TestCase):
        """
        Configure logging for test execution.

        @param item: pytest item
        @param test_case: TestCase instance
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        from conftest import LOGGER_CONFIG_PATH, LOG_DIR
        logging.config.fileConfig(
            LOGGER_CONFIG_PATH,
            defaults={
                'log_dir': str(LOG_DIR),
                'test_function': test_case.test_function,
                'timestamp': timestamp
            },
            disable_existing_loggers=False
        )

    def pytest_runtest_call(self, item):
        """
        Hook executed before test execution.
        Handles TestCase uniqueness and persistence.

        @param item: pytest item representing the test being run
        @raises TestNotFoundException: When no TestCase fixture is found
        @raises TestCaseError: When test case validation fails
        """
        if item.get_closest_marker('no_database_plugin'):
            return
        test_full_path = item.nodeid
        test_module, test_function = test_full_path.split('::')

        # Get and validate TestCase
        test_case = self._find_test_case_fixture(item)
        test_case.set_test_location(test_module, test_function)

        # Configure logging
        self._setup_logging(item, test_case)

        # Create execution record
        execution_record = TestExecutionRecord(test_case)
        test_case.set_execution_record(execution_record)
        execution_record.set_test_location(test_module, test_function, test_case.name, test_case.description)
        execution_record.start()

        self._test_executions[test_full_path] = execution_record

        try:
            db = AutomationDatabaseManager.get_database()

            # Handle test case persistence
            existing_test = db.fetch_test_case_by_test_id(test_case.test_id)
            if existing_test:
                test_case.id = existing_test.id
                Log.info(f"Using test case ID: {test_case.id}")
                # Update existing test case if needed
                if self._should_update_test_case(existing_test, test_case):
                    db.update_test_case(test_case)
            else:
                test_case_id = db.insert_test_case(test_case)
                test_case.id = test_case_id

            # Persist execution record
            execution_id = db.insert_test_execution(execution_record)
            execution_record.id = execution_id
            Log.separator()

        except Exception as e:
            Log.error(f"Error persisting test data: {str(e)}")
            raise

    @staticmethod
    def _should_update_test_case(existing: TestCase, current: TestCase) -> bool:
        """
        Check if test case should be updated.

        @param existing: Existing TestCase from database
        @param current: Current TestCase from test
        @return: True if update is needed
        """
        return (
                existing.name != current.name or
                existing.description != current.description or
                existing.test_suite != current.test_suite
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """
        Hook executed after test completion.
        Updates execution record with results.

        @param item: pytest item
        @param call: pytest call object
        """
        outcome = yield
        report = outcome.get_result()

        if call.when == "call":
            test_full_path = item.nodeid
            execution_record = self._test_executions.get(test_full_path)

            if execution_record is None:
                Log.error(f"No execution record found for {test_full_path}")
                return

            # Update execution record
            result = TestResult.from_pytest_report(report)
            execution_record.end(result)

            if call.excinfo:
                execution_record.set_failure(
                    str(call.excinfo.value),
                    call.excinfo.type.__name__
                )

            try:
                db = AutomationDatabaseManager.get_database()
                db.update_test_execution(execution_record)
                Log.info(f"Updated execution record: {execution_record.id}")
            except Exception as e:
                Log.error(f"Failed to update execution record: {str(e)}")
