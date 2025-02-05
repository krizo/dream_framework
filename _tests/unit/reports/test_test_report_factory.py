"""Tests for report component factory functionality."""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.custom_metric_model import CustomMetricModel
from models.step_model import StepModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from reports.report_factory import ReportComponentFactory


@pytest.fixture
def sample_steps():
    """Provide sample test steps."""
    return [
        StepModel(
            step_id="step_1",
            sequence_number=1,
            hierarchical_number="1",
            indent_level=0,
            step_function="test_func",
            content="First step",
            execution_record_id=1,
            test_function="test_example",
            start_time=datetime.now(),
            completed=True
        ),
        StepModel(
            step_id="step_2",
            sequence_number=2,
            hierarchical_number="1.1",
            indent_level=1,
            parent_step_id=1,
            step_function="test_func",
            content="Nested step",
            execution_record_id=1,
            test_function="test_example",
            start_time=datetime.now(),
            completed=True
        )
    ]


@pytest.fixture
def sample_execution():
    """Provide sample test execution with metrics."""
    execution = MagicMock(spec=TestExecutionRecordModel)
    execution.id = 1
    execution.test_case_id = 1
    execution.test_run_id = "TEST_RUN_1"
    execution.test_module = "test_module"
    execution.test_function = "test_func"
    execution.name = "Test execution"
    execution.description = "Test execution description"
    execution.result = "passed"
    execution.start_time = datetime.now()
    execution.end_time = datetime.now()
    execution.duration = 1.5
    execution.environment = "test"

    # Create mock metrics
    metrics = [
        CustomMetricModel(
            test_execution_id=1,
            name="response_time",
            value=150.5
        ),
        CustomMetricModel(
            test_execution_id=1,
            name="memory_usage",
            value=256.0
        )
    ]
    execution.custom_metrics = metrics

    return execution


def test_create_steps_log_page(sample_steps, tmp_path):
    """Test creating steps log page."""
    output_path = tmp_path / "steps_log.html"
    ReportComponentFactory.create_steps_log_page(
        sample_steps,
        output_path,
        "test_example"
    )

    assert output_path.exists()
    content = output_path.read_text()

    # Verify structure
    assert "Test Steps Log" in content
    assert "First step" in content
    assert "Nested step" in content

    # Verify step hierarchy
    assert 'indent-level: 0' in content
    assert 'indent-level: 1' in content


def test_create_metrics_log_page(sample_execution, tmp_path):
    """Test creating metrics log page."""
    output_path = tmp_path / "metrics_log.html"
    ReportComponentFactory.create_metrics_log_page(
        sample_execution,
        output_path,
        "test_func"
    )

    assert output_path.exists()
    content = output_path.read_text()

    # Verify structure
    assert "Test Metrics Log" in content
    assert "response_time" in content
    assert "150.5" in content
    assert "memory_usage" in content
    assert "256.0" in content


def test_chart_data_creation():
    """Test creating chart data for reports."""
    summary = {
        'total': 10,
        'attempted': 8,
        'failed': 2,
        'skipped': 2
    }

    chart_data = ReportComponentFactory.create_chart_data(summary)

    assert len(chart_data['labels']) == 3  # Passed, Failed, Skipped
    assert len(chart_data['datasets']) == 1
    assert len(chart_data['datasets'][0]['data']) == 3

    data = chart_data['datasets'][0]['data']
    assert data[0] == 6  # passed = attempted - failed
    assert data[1] == 2  # failed
    assert data[2] == 2  # skipped


def test_suite_chart_data_creation():
    """Test creating chart data for test suites."""
    suites = {
        'UI Tests': {
            'total': 5,
            'attempted': 4,
            'failed': 1,
            'skipped': 1
        },
        'API Tests': {
            'total': 8,
            'attempted': 7,
            'failed': 2,
            'skipped': 1
        }
    }

    chart_data = ReportComponentFactory.create_suite_chart_data(suites)

    # Verify structure
    assert len(chart_data['labels']) == 2
    assert chart_data['labels'] == ['UI Tests', 'API Tests']

    assert len(chart_data['datasets']) == 3  # Passed, Failed, Skipped
    assert chart_data['datasets'][0]['label'] == 'Passed'
    assert chart_data['datasets'][1]['label'] == 'Failed'
    assert chart_data['datasets'][2]['label'] == 'Skipped'

    # Verify data
    assert chart_data['datasets'][0]['data'] == [3, 5]  # Passed = attempted - failed
    assert chart_data['datasets'][1]['data'] == [1, 2]  # Failed
    assert chart_data['datasets'][2]['data'] == [1, 1]  # Skipped


def test_log_path_generation(tmp_path):
    """Test generating log file paths."""
    base_dir = tmp_path / "reports"
    test_func = "test_example"

    # Test steps log path
    steps_path = ReportComponentFactory.get_steps_log_path(base_dir, test_func)
    assert steps_path == base_dir / "steps_logs" / f"{test_func}_steps.html"

    # Test metrics log path
    metrics_path = ReportComponentFactory.get_metrics_log_path(base_dir, test_func)
    assert metrics_path == base_dir / "metrics_logs" / f"{test_func}_metrics.html"


def test_has_log_checks(tmp_path):
    """Test checking log file existence."""
    base_dir = tmp_path / "reports"
    test_func = "test_example"

    # Create test log files
    steps_dir = base_dir / "steps_logs"
    metrics_dir = base_dir / "metrics_logs"
    steps_dir.mkdir(parents=True)
    metrics_dir.mkdir(parents=True)

    steps_file = steps_dir / f"{test_func}_steps.html"
    metrics_file = metrics_dir / f"{test_func}_metrics.html"

    steps_file.touch()
    metrics_file.touch()

    # Verify checks
    assert ReportComponentFactory.has_steps_log(base_dir, test_func)
    assert ReportComponentFactory.has_metrics_log(base_dir, test_func)
    assert not ReportComponentFactory.has_steps_log(base_dir, "nonexistent")
    assert not ReportComponentFactory.has_metrics_log(base_dir, "nonexistent")


@pytest.fixture
def empty_steps():
    """Provide empty steps list."""
    return []


def test_error_handling(empty_steps, tmp_path):
    """Test error handling in component factory."""
    # Test with empty steps
    output_path = tmp_path / "empty_steps.html"
    ReportComponentFactory.create_steps_log_page(empty_steps, output_path, "test_func")
    assert output_path.exists()

    # Test with non-existent parent directory
    invalid_path = tmp_path / "nonexistent" / "test.html"
    with pytest.raises(FileNotFoundError, match="Parent directory does not exist"):
        ReportComponentFactory.create_steps_log_page([], invalid_path, "test_func")
    assert not invalid_path.exists()

    # Test with None values
    with pytest.raises(ValueError, match="steps and test_function cannot be None"):
        ReportComponentFactory.create_steps_log_page(None, output_path, None)

    # Test with empty filename
    invalid_file = tmp_path / ""
    with pytest.raises(IsADirectoryError):
        ReportComponentFactory.create_steps_log_page([], invalid_file, "test_func")