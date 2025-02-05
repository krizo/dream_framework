"""Tests for one pager report generation."""
from _tests.unit.reports.test_report_common import generate_test_data
from core.automation_database import AutomationDatabase
from core.common_paths import LOG_DIR
from core.logger import Log
from core.test_run import TestRun
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_run_model import TestRunModel
from reports.report_config import ReportConfig, ReportType, ReportSection, ReportTableConfig
from reports.report_generator import ReportGenerator


def test_generate_onepager_report():
    """Test generating one pager report."""
    Log.info("Starting one pager report generation test")
    TestRun.reset()

    # Initialize database
    db = AutomationDatabase('sqlite:///:memory:')
    db.create_tables()

    # Generate test data
    test_run_id = generate_test_data(db)
    Log.info(f"Generated test data with test_run_id: {test_run_id}")

    # Verify test data
    with db.session_scope() as session:
        test_run = session.query(TestRunModel).filter_by(test_run_id=test_run_id).first()
        if not test_run:
            raise ValueError(f"Test run {test_run_id} not found after generation!")

        executions = session.query(TestExecutionRecordModel) \
            .filter_by(test_run_id=test_run_id) \
            .all()
        Log.info(f"Verified test data - found {len(executions)} executions")

    # Configure output directory
    report_dir = LOG_DIR / "reports" / "one_pager"

    # Generate one-pager report
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[
            ReportSection.MAIN_SUMMARY,
            ReportSection.TEST_RESULTS,
            ReportSection.TEST_CASE_SUMMARY
        ],
        table_config=ReportTableConfig(
            columns=["test_name", "result", "duration", "steps", "custom_metrics"],
            custom_columns=[],
            failed_threshold=80.0
        ),
        show_logs=True,
        show_charts=True,
        css_template="modern",
        output_dir=report_dir
    )

    generator = ReportGenerator(config, db)
    report_path = generator.generate_report(test_run_id, report_dir)

    assert report_path and report_path.exists()
    Log.info(f"Generated one pager report: {report_path}")

    # Verify report structure
    assert (report_dir / "steps_logs").exists()
    assert (report_dir / "metrics_logs").exists()
    assert (report_dir / "css").exists()

    # Verify report content
    content = report_path.read_text()
    assert "Test Execution Report" in content
    assert test_run_id in content
    assert "API Tests" in content
    assert "UI Tests" in content
    assert "Integration Tests" in content

    TestRun.reset()
    return report_path
