import pytest
from typing import Optional, Dict

from core.automation_database import AutomationDatabase
from core.automation_database_manager import AutomationDatabaseManager
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
            test_case = next(fixture for fixture in item.funcargs.values() if isinstance(fixture, TestCase))
        except StopIteration:
            print("\nNo TestCase fixture found in test")
            return

        print(f"\nPytest hook: pytest_runtest_call")
        print(f"Found test case: {test_case.test_name}")

        test_full_path = item.nodeid
        test_case.test_module, test_case.test_function = test_full_path.split('::')
        test_case.start()
        self._test_cases[test_full_path] = test_case

        # Use DatabaseManager instead of direct database instance
        db = AutomationDatabaseManager.get_database()
        print("Inserting test case into database...")
        try:
            inserted_id = db.insert_test_case(test_case)
            print(f"Test case inserted successfully with ID: {inserted_id}")
        except Exception as e:
            print(f"Error inserting test case: {str(e)}")
            raise

    def pytest_runtest_makereport(self, item, call):
        """
        Hook executed after test completion.
        Updates TestCase with results and persists final state.

        @param item: pytest item representing the test
        @param call: pytest call object containing test execution information
        """
        if call.when == "call":
            test_full_path = item.nodeid
            test_case = self._test_cases.get(test_full_path)
            if test_case is None:
                return

            print(f"\nUpdating test case in database in pytest_runtest_makereport: {test_case.test_name}")
            test_case.end(not call.excinfo)

            if call.excinfo:
                test_case.failure = str(call.excinfo.value)
                test_case.failure_type = call.excinfo.type.__name__

            if test_case.start_time and test_case.end_time:
                duration = (test_case.end_time - test_case.start_time).total_seconds()
                test_case.duration = int(duration)

            db = AutomationDatabaseManager.get_database()
            db.update_test_case(test_case)
            print(f"Test case updated in database: {test_case.id}")
