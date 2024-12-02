"""Tests for report factory module."""
from datetime import datetime
from pathlib import Path

import pytest

from models.step_model import StepModel
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


def test_create_log_page(sample_steps, tmp_path):
    """Test creation of log page."""
    output_file = tmp_path / "test_log.html"
    ReportComponentFactory.create_log_page(sample_steps, output_file)

    assert output_file.exists()
    content = output_file.read_text()

    # Verify basic structure
    assert "<html>" in content
    assert "<body>" in content
    assert "Test Execution Log" in content

    # Verify steps are included
    assert "First step" in content
    assert "Nested step" in content

    # Verify proper indentation
    assert 'margin-left: 20px' in content  # For nested step

    # Verify step completion status
    assert 'completed' in content


def test_create_chart_data():
    """Test creation of chart data."""
    summary = {
        'attempted': 10,
        'failed': 2,
        'skipped': 1
    }

    chart_data = ReportComponentFactory.create_chart_data(summary)

    assert 'labels' in chart_data
    assert 'datasets' in chart_data
    assert len(chart_data['labels']) == 3
    assert len(chart_data['datasets'][0]['data']) == 3

    # Verify values are calculated correctly
    data = chart_data['datasets'][0]['data']
    assert data[0] == 8  # passed = attempted - failed
    assert data[1] == 2  # failed
    assert data[2] == 1  # skipped


def test_create_suite_chart_data():
    """Test creation of suite chart data."""
    suites = {
        'Suite1': {
            'attempted': 5,
            'failed': 1,
            'skipped': 1
        },
        'Suite2': {
            'attempted': 3,
            'failed': 0,
            'skipped': 2
        }
    }

    chart_data = ReportComponentFactory.create_suite_chart_data(suites)

    assert 'labels' in chart_data
    assert len(chart_data['labels']) == 2
    assert 'Suite1' in chart_data['labels']
    assert 'Suite2' in chart_data['labels']

    # Verify datasets structure
    assert len(chart_data['datasets']) == 3  # passed, failed, skipped
    assert chart_data['datasets'][0]['label'] == 'Passed'
    assert chart_data['datasets'][1]['label'] == 'Failed'
    assert chart_data['datasets'][2]['label'] == 'Skipped'

    # Verify data calculation
    passed_data = chart_data['datasets'][0]['data']
    assert passed_data[0] == 4  # Suite1: attempted - failed = 5 - 1
    assert passed_data[1] == 3  # Suite2: attempted - failed = 3 - 0


def test_invalid_steps_handling():
    """Test handling of invalid steps data."""
    # Test with empty steps list
    output_file = Path("test_log.html")
    ReportComponentFactory.create_log_page([], output_file)

    # Test with None
    with pytest.raises(TypeError):
        ReportComponentFactory.create_log_page(None, output_file)


def test_chart_data_validation():
    """Test validation of chart data creation."""
    # Test with invalid summary
    with pytest.raises(KeyError):
        ReportComponentFactory.create_chart_data({})

    # Test with empty suites
    chart_data = ReportComponentFactory.create_suite_chart_data({})
    assert len(chart_data['labels']) == 0
    assert all(len(dataset['data']) == 0 for dataset in chart_data['datasets'])


def test_step_hierarchical_display(sample_steps, tmp_path):
    """Test proper display of step hierarchy."""
    output_file = tmp_path / "hierarchy_test.html"
    ReportComponentFactory.create_log_page(sample_steps, output_file)

    content = output_file.read_text()

    # Verify hierarchical numbers are displayed
    assert "1" in content
    assert "1.1" in content

    # Verify proper indentation levels
    assert 'margin-left: 0px' in content  # Root step
    assert 'margin-left: 20px' in content  # Nested step
