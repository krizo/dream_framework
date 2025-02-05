from enum import Enum


class TestResult(Enum):
    """
    Enumeration of possible test execution results.
    Based on pytest outcome states.

    @param STARTED Test just started, no execution done yet
    @param PASSED: Test passed successfully
    @param FAILED: Test failed due to assertion error or exception
    @param SKIPPED: Test was skipped (e.g., by pytest.skip())
    @param XFAILED: Test was expected to fail and did fail
    @param XPASSED: Test was expected to fail but passed
    @param ERROR: Test had setup/teardown error
    @param RERUN: Test was rerun (e.g., by pytest-rerunfailures)
    """
    STARTED = "started"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAILED = "xfailed"
    XPASSED = "xpassed"
    ERROR = "error"
    RERUN = "rerun"

    @classmethod
    def from_pytest_report(cls, report) -> 'TestResult':
        """
        Convert pytest report outcome to TestResult.

        @param report: pytest report object
        @return: Corresponding TestResult enum value
        """
        outcome = report.outcome
        if outcome == "passed" and hasattr(report, "wasxfail"):
            return cls.XPASSED
        elif outcome == "skipped" and hasattr(report, "wasxfail"):
            return cls.XFAILED
        else:
            return cls(outcome)

    @property
    def is_successful(self) -> bool:
        """
        Check if the status represents a successful test execution.

        @return: True if the test is considered successful, False otherwise
        """
        return self in [TestResult.PASSED, TestResult.XFAILED]

    @property
    def is_completed(self) -> bool:
        """
        Check if the status represents a completed test execution.

        @return: True if the test is considered completed, False otherwise
        """
        return self != TestResult.RERUN

    def __str__(self) -> str:
        return self.value
