"""Module for managing database initialization."""
from models.custom_metric_model import CustomMetricModel
from models.step_model import StepModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_case_model import TestCaseModel
from models.test_run_model import TestRunModel

# Order is important
MODELS = [
    TestRunModel,
    TestCaseModel,
    TestExecutionRecordModel,
    CustomMetricModel,
    StepModel
]