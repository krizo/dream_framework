import logging
import logging.config
from datetime import datetime
from typing import Dict

import pytest

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from core.test_case import TestCase


class TestNotFoundException(Exception):
    pass


class TestCasePlugin:
    """ Plugin for handling TestCase persistence during test execution. """
    _test_cases: Dict[str, TestCase] = {}

    def pytest_runtest_call(self, item):
        """
        Hook executed before test execution.
        Handles initial persistence of TestCase.

        @param item: pytest item representing the test being run
        """
        try:
            test_case = next(fixture for fixture in item.funcargs.values()
                             if isinstance(fixture, TestCase))
        except StopIteration:
            Log.warning("No TestCase fixture found in test")
            return

        test_full_path = item.nodeid
        test_case.test_module, test_case.test_function = test_full_path.split('::')

        # Load logger configuration with proper formatting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        from conftest import LOGGER_CONFIG_PATH
        from conftest import LOG_DIR

        logging.config.fileConfig(
            LOGGER_CONFIG_PATH,
            defaults={
                'log_dir': str(LOG_DIR),
                'test_function': test_case.test_function,
                'timestamp': timestamp
            },
            disable_existing_loggers=False
        )
        test_case.start()
        self._test_cases[test_full_path] = test_case

        try:
            db = AutomationDatabaseManager.get_database()
            inserted_id = db.insert_test_case(test_case)
            Log.info(f"Test case inserted successfully. TestCase.Id: {inserted_id}")
        except Exception as e:
            Log.error(message="Error inserting test case", exception=e)
            raise

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """
        Hook executed after test completion.
        Updates TestCase with results and persists final state.

        @param item: pytest item representing the test
        @param call: pytest call object containing test execution information
        """
        # First yield to get the outcome
        outcome = yield
        report = outcome.get_result()

        if call.when == "call":
            test_full_path = item.nodeid
            test_case = self._test_cases.get(test_full_path)
            if test_case is None:
                Log.error(f"TestCase object hasn't been found for {test_full_path}")
                return

            test_case.end(not call.excinfo)

            try:
                db = AutomationDatabaseManager.get_database()
                db.update_test_case(test_case)
                Log.info(f"Test case updated in database. TestCase.Id: {test_case.id}")
            except Exception as e:
                Log.error("Failed to update test case in database", e)


def get_logger_config(test_function: str) -> dict:
    """
    Get logger configuration with dynamic values.

    @param test_function: str - Name of the test function
    @return dict - Configuration dictionary with the following keys:
        - log_dir: str - Directory path for log files
        - test_function - test function that invoked the test
        - timestamp: str - Current timestamp for log file names
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    from conftest import LOG_DIR
    return {
        'log_dir': str(LOG_DIR),  # Convert Path to string for logging config
        'test_function': test_function,
        'timestamp': timestamp
    }
