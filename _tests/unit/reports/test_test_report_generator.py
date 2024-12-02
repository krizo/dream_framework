"""Tests for report generator functionality."""
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from jinja2 import Environment

from core.automation_database import AutomationDatabase
from core.common_paths import TEMPLATES_DIR
from core.test_result import TestResult
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_case_model import TestCaseModel
from models.test_run_model import TestRunModel
from reports.report_config import ReportConfig, ReportType, ReportSection, ReportTableConfig
from reports.report_generator import ReportGenerator, ReportData


@pytest.fixture
def mock_db():
    """Provide mock database."""
    return MagicMock(spec=AutomationDatabase)


@pytest.fixture
def mock_test_run():
    """Provide mock test run data."""
    return TestRunModel(
        test_run_id="TEST_RUN_001",
        test_type="single",
        status="completed",
        owner="test_user",
        environment="test",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration=10.5,
        branch="main"
    )


@pytest.fixture
def mock_executions():
    """Provide mock test execution records."""
    test_case = TestCaseModel(
        id=1,
        test_id="test_module::test_func",
        test_module="test_module",
        test_function="test_func",
        name="Test Case",
        description="Test Description",
        test_suite="Test Suite"
    )

    return [
        TestExecutionRecordModel(
            id=1,
            test_case=test_case,
            test_case_id=1,
            test_run_id="TEST_RUN_001",
            test_module="test_module",
            test_function="test_func",
            name="Test Case 1",
            description="Test Description 1",
            result=TestResult.PASSED.value,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=5.0,
            environment="test"
        ),
        TestExecutionRecordModel(
            id=2,
            test_case=test_case,
            test_case_id=1,
            test_run_id="TEST_RUN_001",
            test_module="test_module",
            test_function="test_func",
            name="Test Case 2",
            description="Test Description 2",
            result=TestResult.FAILED.value,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=5.0,
            failure="Test failed",
            failure_type="AssertionError",
            environment="test"
        )
    ]


@pytest.fixture
def report_config(tmp_path):
    """Provide test report configuration."""
    return ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY, ReportSection.TEST_CASE_SUMMARY],
        table_config=ReportTableConfig(
            columns=["test_name", "result", "duration"],
            custom_columns=["comments"],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template="default",
        template_dir=TEMPLATES_DIR,
        output_dir=tmp_path
    )


@pytest.fixture
def report_generator(mock_db, report_config):
    """Provide configured report generator."""
    return ReportGenerator(report_config, mock_db)


def test_report_data_preparation(report_generator, mock_test_run, mock_executions):
    """Test preparation of report data."""
    report_data = report_generator._prepare_report_data(mock_test_run, mock_executions)

    assert isinstance(report_data, ReportData)
    assert report_data.test_run == mock_test_run
    assert report_data.executions == mock_executions

    # Verify summary calculations
    assert report_data.summary["total"] == 2
    assert report_data.summary["failed"] == 1
    assert report_data.summary["passed_percent"] == 50.0

    # Verify suite summaries
    assert "Test Suite" in report_data.suite_summaries
    suite_data = report_data.suite_summaries["Test Suite"]
    assert suite_data["total"] == 2
    assert suite_data["failed"] == 1
    assert suite_data["passed_percent"] == 50.0


def test_generate_one_pager_report(report_generator, mock_db, mock_test_run, mock_executions, tmp_path):
    """Test generation of one-pager report."""
    # Setup mock database session
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_test_run
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_executions

    mock_db.session_scope.return_value.__enter__.return_value = mock_session

    # Generate report
    report_path = report_generator.generate_report("TEST_RUN_001", tmp_path)

    assert report_path.exists()
    assert report_path.suffix == ".html"

    # Verify report content
    content = report_path.read_text()
    assert "Test Execution Report" in content
    assert mock_test_run.test_run_id in content
    assert "Test Suite" in content


def test_generate_drilldown_report(mock_db, mock_test_run, mock_executions, tmp_path):
    """Test generation of drilldown report."""
    config = ReportConfig(
        report_type=ReportType.DRILLDOWN,
        sections=[ReportSection.MAIN_SUMMARY, ReportSection.TEST_SUITE_SUMMARY],
        table_config=ReportTableConfig(
            columns=["test_name", "result"],
            custom_columns=[],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template="default",
        template_dir=TEMPLATES_DIR,
        output_dir=tmp_path
    )

    generator = ReportGenerator(config, mock_db)

    # Setup mock database session
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_test_run
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_executions

    mock_db.session_scope.return_value.__enter__.return_value = mock_session

    # Generate report
    report_path = generator.generate_report("TEST_RUN_001", tmp_path)

    assert report_path.exists()
    assert report_path.name == "index.html"

    # Verify suite pages were created
    suite_page = report_path.parent / "suite_test_suite.html"
    assert suite_page.exists()


def test_report_error_handling(report_generator, mock_db, tmp_path):
    """Test error handling during report generation."""
    # Setup mock to raise exception
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    mock_db.session_scope.return_value.__enter__.return_value = mock_session

    report_path = report_generator.generate_report("NONEXISTENT_RUN", tmp_path)
    assert report_path is None


test_cases = [
    pytest.param(
        [],
        0,
        "PASSED",
        id="empty_test_suite"
    ),
    pytest.param(
        [MagicMock(result=TestResult.PASSED.value)],
        100,
        "PASSED",
        id="single_passed_test"
    ),
    pytest.param(
        [MagicMock(result=TestResult.FAILED.value)],
        0,
        "FAILED",
        id="single_failed_test"
    ),
    pytest.param(
        [MagicMock(result=TestResult.SKIPPED.value)],
        0,
        "PASSED",
        id="single_skipped_test"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.PASSED.value),
            MagicMock(result=TestResult.PASSED.value),
        ],
        100,
        "PASSED",
        id="all_tests_passed"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.FAILED.value),
            MagicMock(result=TestResult.FAILED.value),
        ],
        0,
        "FAILED",
        id="all_tests_failed"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.PASSED.value),
            MagicMock(result=TestResult.FAILED.value),
            MagicMock(result=TestResult.SKIPPED.value),
        ],
        50,
        "FAILED",
        id="mixed_test_results"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.SKIPPED.value),
            MagicMock(result=TestResult.SKIPPED.value),
        ],
        0,
        "PASSED",
        id="all_tests_skipped"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.PASSED.value),
            MagicMock(result=TestResult.PASSED.value),
            MagicMock(result=TestResult.FAILED.value),
        ],
        66.67,
        "FAILED",
        id="mostly_passed_tests"
    ),
    pytest.param(
        [
            MagicMock(result=TestResult.FAILED.value),
            MagicMock(result=TestResult.FAILED.value),
            MagicMock(result=TestResult.PASSED.value),
        ],
        33.33,
        "FAILED",
        id="mostly_failed_tests"
    ),
]


@pytest.mark.parametrize("executions,expected_percent,expected_status", test_cases)
def test_summary_calculations(report_generator, executions, expected_percent, expected_status):
    """Test summary statistics calculations with different scenarios."""
    for execution in executions:
        execution.test_case = MagicMock(test_suite="Test Suite")

    summary = report_generator._calculate_summary(executions)

    assert summary["total"] == len(executions)

    assert round(summary["passed_percent"], 2) == expected_percent

    assert summary["result"] == expected_status

    attempted = len([e for e in executions if e.result != TestResult.SKIPPED.value])
    failed = len([e for e in executions if e.result == TestResult.FAILED.value])
    skipped = len([e for e in executions if e.result == TestResult.SKIPPED.value])

    assert summary["attempted"] == attempted
    assert summary["failed"] == failed
    assert summary["skipped"] == skipped


def test_custom_template_handling(mock_db, tmp_path):
    """Test handling of custom template directory."""
    custom_template_dir = tmp_path / "templates"
    custom_template_dir.mkdir()

    # Create custom template
    template_content = """
    <!DOCTYPE html>
    <html>
        <body>
            <h1>Custom Template</h1>
            <p>Test Run: {{test_run.test_run_id}}</p>
        </body>
    </html>
    """

    (custom_template_dir / "one_pager.html").write_text(template_content)

    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=ReportTableConfig(
            columns=["test_name"],
            custom_columns=[],
            failed_threshold=90.0
        ),
        show_logs=False,
        show_charts=False,
        css_template="default",
        template_dir=custom_template_dir,
        output_dir=tmp_path
    )

    generator = ReportGenerator(config, mock_db)
    assert isinstance(generator.jinja_env, Environment)
    assert str(custom_template_dir) in generator.jinja_env.loader.searchpath


def test_css_template_handling(report_generator, mock_db, mock_test_run, mock_executions, tmp_path):
    """Test handling of different CSS templates."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_test_run
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_executions

    mock_db.session_scope.return_value.__enter__.return_value = mock_session

    report_path = report_generator.generate_report("TEST_RUN_001", tmp_path)

    content = report_path.read_text()
    assert "default.css" in content or "dark.css" in content or "modern-light.css" in content
