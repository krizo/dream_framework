"""Common test utilities for report tests."""
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


def generate_test_data(db: AutomationDatabase) -> str:
    """
    Generate sample test data for report testing.

    @param db: Database instance to populate
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





def setup_css_files(report_dir: Path, theme: str = "classic") -> None:
    """
    Set up CSS files for report directory.

    @param report_dir: Report output directory
    @param theme: Theme name to use
    """
    css_dir = report_dir / "css"
    css_dir.mkdir(parents=True, exist_ok=True)

    # Required CSS files
    css_files = [
        "base-layout.css",
        f"theme-{theme}.css",
        "step_logs.css",
        "custom_metrics_logs.css"
    ]

    template_css_dir = TEMPLATES_DIR.parent / "css"
    copied_files = []

    # Copy CSS files
    for css_file in css_files:
        src = template_css_dir / css_file
        dst = css_dir / css_file
        if src.exists():
            shutil.copy2(src, dst)
            copied_files.append(css_file)
            Log.info(f"Copied CSS file: {css_file}")
        else:
            Log.warning(f"CSS file not found: {src}")

    # Verify required files
    required_files = ["base-layout.css", f"theme-{theme}.css"]
    missing_files = [f for f in required_files if f not in copied_files]
    if missing_files:
        raise ValueError(f"Missing required CSS files: {missing_files}")

    Log.info(f"CSS setup completed in {css_dir}")


def verify_report_contents(report_path: Path) -> None:
    """
    Verify common report contents.

    @param report_path: Path to report file
    """
    content = report_path.read_text()

    # Verify CSS links - using more flexible search
    assert 'href="css/base-layout.css"' in content, "Missing base CSS link"
    assert 'href="css/theme-' in content, "Missing theme CSS link"

    # Verify basic structure
    assert "Test Execution Report" in content, "Missing report title"
    assert "metric-container" in content, "Missing metrics container"
    assert '<table' in content, "Missing data table"

    # Verify report elements
    required_elements = [
        "Start Time",
        "End Time",
        "Duration",
        "Owner",
        "Environment"
    ]
    for element in required_elements:
        assert element in content, f"Missing required element: {element}"

    # Verify metrics files
    metrics_dir = report_path.parent / "metrics_logs"
    assert metrics_dir.exists(), "Missing metrics directory"

    metrics_files = list(metrics_dir.glob("*_metrics.html"))
    assert metrics_files, "No metrics files found"

    # Verify metrics content
    metrics_content = metrics_files[0].read_text()
    performance_metrics = [
        "response_time_ms",
        "cpu_usage_percent",
        "processed_records",
        "memory_usage_mb"
    ]
    has_performance_metrics = any(metric in metrics_content for metric in performance_metrics)
    assert has_performance_metrics, f"Missing performance metrics in {metrics_files[0]}"
