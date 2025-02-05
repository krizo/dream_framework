"""Integration test for report generation functionality."""
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from core.automation_database import AutomationDatabase
from core.common_paths import TEMPLATES_DIR
from core.logger import Log
from core.test_result import TestResult
from core.test_run import TestRun, TestRunType
from models.custom_metric_model import CustomMetricModel
from models.step_model import StepModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_case_model import TestCaseModel
from models.test_run_model import TestRunModel
from reports.report_config import ReportConfig, ReportType, ReportSection, ReportTableConfig
from reports.report_generator import ReportGenerator


def generate_test_data(db: AutomationDatabase) -> str:
    """
    Generate sample test data for report testing.

    @param db: Database instance
    @return: Generated test run ID
    """
    # Initialize TestRun
    test_run = TestRun.initialize(owner="test_user", environment="test")
    Log.info(f"Initialized TestRun: {test_run.test_run_id}")

    with db.session_scope() as session:
        # Create test run
        test_run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_run = TestRunModel(
            test_run_id=test_run_id,
            test_type=TestRunType.SINGLE.value,
            status="completed",
            owner="test_user",
            environment="test",
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now(),
            duration=1800.0
        )
        session.add(test_run)
        session.flush()

        # Create test suites
        for suite in ["API Tests", "UI Tests", "Integration Tests"]:
            for i in range(5):  # 5 test cases per suite
                test_case = TestCaseModel(
                    test_id=f"{suite.lower()}::test_{i}",
                    test_module=f"{suite.lower()}/test_module_{i}.py",
                    test_function=f"test_function_{i}",
                    name=f"Test {i} in {suite}",
                    description=f"Test case {i} for {suite}",
                    test_suite=suite
                )
                session.add(test_case)
                session.flush()

                # Create execution record
                execution = TestExecutionRecordModel(
                    test_case_id=test_case.id,
                    test_run_id=test_run_id,
                    test_module=test_case.test_module,
                    test_function=test_case.test_function,
                    name=test_case.name,
                    description=test_case.description,
                    result=TestResult.PASSED.value if i % 3 != 0 else TestResult.FAILED.value,
                    start_time=datetime.now() - timedelta(minutes=29),
                    end_time=datetime.now() - timedelta(minutes=28),
                    duration=60.0,
                    environment="test"
                )
                session.add(execution)
                session.flush()

                # Add metrics
                metrics = [
                    CustomMetricModel(
                        test_execution_id=execution.id,
                        name="response_time",
                        value=random.uniform(100, 500)
                    ),
                    CustomMetricModel(
                        test_execution_id=execution.id,
                        name="memory_usage",
                        value=random.randint(200, 400)
                    )
                ]
                for metric in metrics:
                    session.add(metric)

                # Add steps
                steps = []
                for j in range(3):
                    step = StepModel(
                        step_id=f"step_{execution.id}_{j}",
                        sequence_number=j + 1,
                        hierarchical_number=f"{j + 1}",
                        indent_level=0,
                        step_function=f"verify_step_{j + 1}",
                        content=f"Step {j + 1} of test {i}",
                        execution_record_id=execution.id,
                        test_function=execution.test_function,
                        completed=True,
                        start_time=execution.start_time + timedelta(seconds=j * 10)
                    )
                    steps.append(step)
                session.add_all(steps)

        return test_run_id


def setup_report_dir(base_dir: Path) -> Path:
    """
    Setup report directory structure.

    @param base_dir: Base output directory
    @return: Report directory path
    """
    # Use logs directory for reports
    report_dir = base_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Create CSS directory in logs
    css_dir = report_dir / "css"
    css_dir.mkdir(exist_ok=True)

    # Copy required CSS files from templates
    css_files = [
        "base-layout.css",
        "theme-modern.css",
        "theme-dark.css",
        "theme-classic.css",
        "theme-minimalist.css",
        "theme-retro.css",
        "step_logs.css",
        "custom_metrics_logs.css"
    ]

    css_source = TEMPLATES_DIR.parent / "css"
    if css_source.exists():
        for css_file in css_files:
            src = css_source / css_file
            if src.exists():
                shutil.copy2(src, css_dir / css_file)
            else:
                Log.warning(f"CSS file not found: {src}")

    return report_dir


def test_generate_reports():
    """Test generating both one-pager and drilldown reports."""
    Log.info("Starting test report generation")
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

    # Setup report directory
    report_dir = setup_report_dir(Path("logs"))

    # Generate one-pager report
    onepager_config = ReportConfig(
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
        output_dir=report_dir / "one_pager"
    )

    onepager_generator = ReportGenerator(onepager_config, db)
    onepager_path = onepager_generator.generate_report(test_run_id, report_dir / "one_pager")

    # Generate drilldown report
    drilldown_config = ReportConfig(
        report_type=ReportType.DRILLDOWN,
        sections=[
            ReportSection.MAIN_SUMMARY,
            ReportSection.TEST_RESULTS,
            ReportSection.TEST_CASE_SUMMARY,
            ReportSection.SUITE_DETAILS
        ],
        table_config=ReportTableConfig(
            columns=["test_name", "result", "duration", "steps", "custom_metrics"],
            custom_columns=[],
            failed_threshold=80.0
        ),
        show_logs=True,
        show_charts=True,
        css_template="modern",
        output_dir=report_dir / "drilldown"
    )

    drilldown_generator = ReportGenerator(drilldown_config, db)
    drilldown_path = drilldown_generator.generate_report(test_run_id, report_dir / "drilldown")

    # Verify reports
    assert onepager_path and onepager_path.exists()
    assert drilldown_path and drilldown_path.exists()

    # Verify CSS files
    css_dir = report_dir / "css"
    assert css_dir.exists()
    assert (css_dir / "base-layout.css").exists()
    assert (css_dir / "theme-modern.css").exists()

    # Verify drilldown structure
    suite_pages = list(drilldown_path.parent.glob("suite_*.html"))
    assert len(suite_pages) > 0, "No suite pages generated"

    Log.info(f"Generated reports in {report_dir}")
    Log.info(f"One-pager: {onepager_path}")
    Log.info(f"Drilldown: {drilldown_path}")

    TestRun.reset()

    return onepager_path, drilldown_path
