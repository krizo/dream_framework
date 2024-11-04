import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from core.logger import Log
from core.test_result import TestResult
from helpers.database_helper import serialize_value
from models.custom_metric_model import CustomMetricModel
from models.test_case_execution_record_model import TestExecutionRecordModel


@dataclass
class MetricValue:
    """
    Represents a single metric for Custom Metrics.
    
    @param name: Name of the metric
    @param value: Value of the metric (can be any serializable type)
    """
    name: str
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary format for serialization."""
        return {
            "name": self.name,
            "value": self.value,
        }


class TestExecutionRecord:
    """
    Represents a single execution of a test case with metric tracking.
    
    This class handles:
    - Test execution lifecycle (start, end, failure)
    - Metric collection and management
    - Database persistence through model conversion
    - Test case property tracking
    """

    def __init__(self, test_case: 'TestCase', metrics: Optional[Dict[str, Any]] = None):
        """
        Initialize new test execution record.

        @param test_case: Associated TestCase instance
        @param metrics: Optional initial metrics dictionary
        """
        # Basic test execution info
        self.id: Optional[int] = None
        self.test_case = test_case
        self.test_run_id: str = os.getenv('PYTEST_XDIST_TESTRUNUID') or datetime.now().strftime("%y%m%d%H%M%S%f")

        # Test status
        self.result: Optional[TestResult] = TestResult.STARTED
        self.failure: str = ""
        self.failure_type: str = ""

        # Timing info
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None

        # Test location
        self.test_module: str = test_case.test_module
        self.test_function: str = test_case.test_function
        self.test_name: str = test_case.name
        self.test_description: str = test_case.description
        self.environment: str = None

        # Metrics storage
        self._metrics: Dict[str, MetricValue] = {}
        self._initialized: bool = False

        # Initialize metrics if provided
        if metrics:
            for name, value in metrics.items():
                self.add_custom_metric(name, value)

        # Auto-initialize if metrics provided
        if metrics:
            self.initialize()

    def _add_test_case_metrics(self):
        """Add only custom test case properties as metrics."""
        if not self._initialized:
            self.initialize()
        else:
            custom_properties = self.test_case.get_custom_properties()
            for prop_name, prop_value in custom_properties.items():
                if prop_value is not None:
                    self.add_custom_metric(prop_name, prop_value)

    def initialize(self):
        """
        Initialize execution record with only custom properties and execution metrics.

        This method:
        - Sets initial timestamps
        - Adds test case properties as metrics
        - Records basic execution information
        - Ensures one-time initialization
        """
        if self._initialized:
            return

        self._initialized = True
        self.start_time = datetime.now()

        # Add only custom properties as metrics
        custom_properties = self.test_case.get_custom_properties()
        for prop_name, prop_value in custom_properties.items():
            if prop_value is not None:
                self.add_custom_metric(prop_name, prop_value)

    def start(self):
        """
        Start test execution and record initial state.

        This method:
        - Ensures initialization
        - Logs start of execution
        - Records initial state
        """
        self.initialize()
        Log.info(f"Starting test execution of {self.test_function}")

    def end(self, result: TestResult):
        """
        End test execution and record final state.

        @param result: TestResult enum value indicating execution result
        """
        self.end_time = datetime.now()
        self.result = result
        self.duration = (self.end_time - self.start_time).total_seconds() if self.start_time else None

        Log.separator()
        Log.info(f"Test execution {self.test_run_id} completed")

    def add_custom_metric(self, name: str, value: Any):
        """
        Add or update a custom metric with current timestamp.

        @param name: Metric name
        @param value: Metric value (will be serialized if needed)
        """
        metric = MetricValue(name=name, value=serialize_value(value))
        self._metrics[name] = metric

    def get_metric(self, name: str) -> Optional[Any]:
        """
        Get current value of a metric by name.

        @param name: Metric name
        @return: Current value of metric or None if not found
        """
        metric = self._metrics.get(name)
        return metric.value if metric else None

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Get all metrics as list of dictionaries.

        @return: List of metric dictionaries with name, value, and timestamp
        """
        return [metric.to_dict() for metric in self._metrics.values()]

    def set_failure(self, failure: str, failure_type: str):
        """
        Record test failure details.

        @param failure: Failure description
        @param failure_type: Type/category of failure
        """
        self.failure = failure
        self.failure_type = failure_type

    def set_test_location(self, module: str, function: str, name: str, description: str):
        """
        Set test module and function information.

        @param module: Test module name/path
        @param function: Test function name
        @param name: Test name
        @param description: Test description
        """
        self.test_module = module
        self.test_function = function
        self.test_name = name
        self.test_description = description

    def set_environment(self, environment: str):
        """
        Set test execution environment.

        @param environment: Environment name/identifier
        """
        self.environment = environment
        self.add_custom_metric("environment", environment)

    def to_model(self) -> TestExecutionRecordModel:
        """
        Convert execution record to database model.

        @return: TestExecutionRecordModel instance ready for persistence
        """
        model = TestExecutionRecordModel(
            test_case_id=self.test_case.id,
            test_run_id=self.test_run_id,
            test_function=self.test_function,
            test_module=self.test_module,
            name=self.test_case.name,
            description=self.test_case.description,
            result=self.result.value if self.result else TestResult.STARTED.value,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            failure=self.failure,
            failure_type=self.failure_type,
            environment=self.environment
        )

        # Convert metrics to model
        for metric in self._metrics.values():
            model.custom_metrics.append(
                CustomMetricModel(
                    name=metric.name,
                    value=metric.value
                )
            )

        return model

    @classmethod
    def from_model(cls, model: TestExecutionRecordModel, test_case: 'TestCase') -> Optional['TestExecutionRecord']:
        """
        Create execution record from database model.

        @param model: Database model to convert from
        @param test_case: Associated TestCase instance
        @return: New TestExecutionRecord instance or None if invalid model
        """
        if not model or not test_case:
            return None

        # Create initial metrics from model
        initial_metrics = {
            metric.name: metric.value
            for metric in model.custom_metrics
        }

        # Create record with initial metrics
        record = cls(test_case, metrics=initial_metrics)

        # Set all model fields
        record.id = model.id
        record.test_run_id = model.test_run_id
        record.result = TestResult(model.result)  # Convert string to enum
        record.start_time = model.start_time
        record.end_time = model.end_time
        record.failure = model.failure
        record.failure_type = model.failure_type
        record.duration = model.duration
        record.test_function = model.test_function
        record.test_module = model.test_module
        record.environment = model.environment

        # Force initialized state since we loaded from model
        record._initialized = True
        return record

    @property
    def is_completed(self) -> bool:
        """Check if test execution is completed."""
        return self.result.is_completed if self.result else False

    @property
    def is_successful(self) -> bool:
        """Check if test execution was successful."""
        return self.result.is_successful if self.result else False
