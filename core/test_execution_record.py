"""Module for managing test execution records."""
from datetime import datetime
from typing import Optional, Dict, Any, Type, List

from core.logger import Log
from core.test_result import TestResult
from helpers.database_helper import serialize_value


class TestExecutionRecord:
    """Class representing test execution record."""

    def __init__(self, test_case: 'TestCase', metrics: Optional[Dict[str, Any]] = None):
        """
        Initialize new test execution record.

        @param test_case: Associated TestCase instance
        @param metrics: Optional initial metrics dictionary
        """
        # Basic test execution info
        self.id: Optional[int] = None
        self.test_case = test_case

        # Get test_run_id from current TestRun instance
        from core.test_run import TestRun
        test_run = TestRun.get_instance()
        if not test_run:
            raise RuntimeError("No active TestRun found. TestRun must be initialized before creating TestExecutionRecord")

        self.test_run_id = test_run.test_run_id
        self._initialized = False
        
        # Test location info
        self.test_module: Optional[str] = None
        self.test_function: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        
        # Execution state
        self.result = TestResult.STARTED
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.failure = ""
        self.failure_type = ""
        self.environment = test_run.environment

        # Metrics
        self._metrics: Dict[str, Any] = {}
        if metrics:
            self._metrics.update(metrics)

    @classmethod
    def get_model(cls) -> Type['TestExecutionRecordModel']:
        """Get TestExecutionRecordModel class."""
        from models.test_case_execution_record_model import TestExecutionRecordModel
        return TestExecutionRecordModel

    @classmethod
    def from_model(cls, model: 'TestExecutionRecordModel', test_case: 'TestCase') -> 'TestExecutionRecord':
        """
        Create TestExecutionRecord from database model.

        @param model: Database model instance
        @param test_case: Associated TestCase instance
        @return: TestExecutionRecord instance
        """
        record = cls(test_case)
        record.id = model.id
        record.test_run_id = model.test_run_id
        record.test_module = model.test_module
        record.test_function = model.test_function
        record.name = model.name
        record.description = model.description
        record.result = TestResult(model.result)
        record.start_time = model.start_time
        record.end_time = model.end_time
        record.duration = model.duration
        record.failure = model.failure
        record.failure_type = model.failure_type
        record.environment = model.environment
        
        # Load metrics
        for metric in model.custom_metrics:
            record._metrics[metric.name] = metric.value

        record._initialized = True
        return record

    def initialize(self) -> None:
        """Initialize execution record with test case properties."""
        if self._initialized:
            return

        # Add test case properties as metrics
        self._add_test_case_metrics()
        self._initialized = True

    def _add_test_case_metrics(self) -> None:
        """Add test case properties to metrics."""
        properties = self.test_case.get_properties()
        for name, value in properties.items():
            self.add_custom_metric(f"test_case_{name}", value)

    def set_test_location(self, module: str, function: str, name: str, description: str) -> None:
        """Set test location information."""
        self.test_module = module
        self.test_function = function
        self.name = name
        self.description = description

    def start(self) -> None:
        """Mark test execution as started."""
        self.start_time = datetime.now()
        Log.info(f"Starting test execution of {self.test_function}")

    def end(self, result: TestResult) -> None:
        """
        Mark test execution as completed.

        @param result: Final test result
        """
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.result = result

        # Log completion
        if self.duration is not None:
            Log.info(f"Test execution completed in {self.duration:.2f}s with result: {result.value}")
            if result == TestResult.FAILED and self.failure:
                Log.error(f"Failure: {self.failure} ({self.failure_type})")

    def set_failure(self, message: str, failure_type: str) -> None:
        """
        Set failure information.

        @param message: Failure message
        @param failure_type: Type of failure
        """
        self.failure = message
        self.failure_type = failure_type

    def add_custom_metric(self, name: str, value: Any) -> None:
        """
        Add custom metric to execution record.

        @param name: Metric name
        @param value: Metric value
        """
        self._metrics[name] = serialize_value(value)

    def get_metric(self, name: str) -> Optional[Any]:
        """
        Get custom metric value by name.

        @param name: Metric name
        @return: Metric value if exists, None otherwise
        """
        return self._metrics.get(name)

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Get all metrics as list of dictionaries.

        @return: List of metric dictionaries with name and value
        """
        return [{"name": name, "value": value} for name, value in self._metrics.items()]

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.result is not None and self.result != TestResult.STARTED

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.result is not None and self.result.is_successful

    def to_model(self) -> 'TestExecutionRecordModel':
        """Convert to database model."""
        from models.test_case_execution_record_model import TestExecutionRecordModel
        from models.custom_metric_model import CustomMetricModel

        model = TestExecutionRecordModel(
            test_case_id=self.test_case.id,
            test_run_id=self.test_run_id,
            test_module=self.test_module,
            test_function=self.test_function,
            name=self.name,
            description=self.description,
            result=self.result.value,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            failure=self.failure,
            failure_type=self.failure_type,
            environment=self.environment
        )

        # Add metrics
        model.custom_metrics = [
            CustomMetricModel(name=name, value=value)
            for name, value in self._metrics.items()
        ]

        return model