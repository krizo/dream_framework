"""Integration tests for report generation with large datasets."""
import random
from datetime import datetime, timedelta
from typing import Dict, Any

from _tests.unit.reports.test_report_common import verify_report_contents, setup_css_files
from core.automation_database import AutomationDatabase
from core.common_paths import LOG_DIR
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


class MetricsGenerator:
    """Helper class for generating various test metrics."""

    @staticmethod
    def generate_performance_metrics() -> Dict[str, Any]:
        """Generate performance-related metrics."""
        return {
            "response_time_ms": random.uniform(50, 2000),
            "processing_time_ms": random.uniform(10, 500),
            "cpu_usage_percent": random.uniform(0, 100),
            "memory_usage_mb": random.uniform(100, 1000),
            "thread_count": random.randint(1, 50),
            "active_connections": random.randint(1, 100),
            "queue_size": random.randint(0, 1000),
            "cache_hits": random.randint(1000, 10000),
            "cache_misses": random.randint(0, 1000),
        }

    @staticmethod
    def generate_business_metrics() -> Dict[str, Any]:
        """Generate business-related metrics."""
        return {
            "processed_records": random.randint(100, 10000),
            "successful_transactions": random.randint(90, 100),
            "failed_transactions": random.randint(0, 10),
            "revenue_amount": round(random.uniform(1000, 100000), 2),
            "customer_satisfaction": round(random.uniform(1, 5), 1),
            "processing_fee": round(random.uniform(1, 100), 2),
            "discount_applied": round(random.uniform(0, 0.5), 2),
        }

    @staticmethod
    def generate_error_metrics() -> Dict[str, Any]:
        """Generate error-related metrics."""
        error_types = ["ValidationError", "TimeoutError", "DatabaseError", "NetworkError"]
        return {
            "error_type": random.choice(error_types),
            "error_count": random.randint(1, 100),
            "retry_attempts": random.randint(1, 5),
            "error_rate": random.uniform(0.01, 0.1),
            "affected_records": random.randint(1, 1000),
            "recovery_time_ms": random.uniform(100, 5000),
        }

    @staticmethod
    def generate_api_metrics() -> Dict[str, Any]:
        """Generate API-related metrics."""
        endpoints = ["GET /users", "POST /orders", "PUT /products", "DELETE /items"]
        status_codes = [200, 201, 400, 401, 403, 404, 500]
        return {
            "endpoint": random.choice(endpoints),
            "status_code": random.choice(status_codes),
            "request_size_bytes": random.randint(100, 10000),
            "response_size_bytes": random.randint(100, 50000),
            "headers_count": random.randint(5, 20),
            "api_version": f"v{random.randint(1,3)}.{random.randint(0,9)}",
        }

    @staticmethod
    def generate_database_metrics() -> Dict[str, Any]:
        """Generate database-related metrics."""
        return {
            "query_time_ms": random.uniform(1, 1000),
            "rows_affected": random.randint(1, 10000),
            "index_usage_percent": random.uniform(0, 100),
            "transaction_size_kb": random.uniform(1, 1000),
            "deadlocks_count": random.randint(0, 10),
            "connection_pool_usage": random.uniform(0, 100),
        }


def generate_complex_test_data(db: AutomationDatabase, test_suites: int = 10, cases_per_suite: int = 20) -> str:
    """
    Generate complex test data with various metrics.

    @param db: Database instance
    @param test_suites: Number of test suites to generate
    @param cases_per_suite: Number of test cases per suite
    @return: Generated test run ID
    """
    test_run = TestRun.initialize(owner="integration_test", environment="test")
    Log.info(f"Initialized TestRun: {test_run.test_run_id}")

    with db.session_scope() as session:
        test_run_id = f"test_run_large_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_run = TestRunModel(
            test_run_id=test_run_id,
            test_type=TestRunType.SINGLE.value,
            status="completed",
            owner="integration_test",
            environment="test",
            start_time=datetime.now() - timedelta(hours=2),
            end_time=datetime.now(),
            duration=7200.0,
            branch="feature/large-tests",
            app_under_test="TestApp",
            app_version="2.0.0"
        )
        session.add(test_run)
        session.flush()

        metrics_generator = MetricsGenerator()
        metrics_functions = [
            metrics_generator.generate_performance_metrics,
            metrics_generator.generate_business_metrics,
            metrics_generator.generate_error_metrics,
            metrics_generator.generate_api_metrics,
            metrics_generator.generate_database_metrics
        ]

        # Generate test suites
        for suite_idx in range(test_suites):
            suite_name = f"Test Suite {suite_idx + 1}"
            Log.info(f"Generating suite: {suite_name}")

            for case_idx in range(cases_per_suite):
                # Create test case
                test_case = TestCaseModel(
                    test_id=f"{suite_name.lower().replace(' ', '_')}::test_{case_idx}",
                    test_module=f"module_{suite_idx}/test_case_{case_idx}.py",
                    test_function=f"test_function_{case_idx}",
                    name=f"Test {case_idx} in {suite_name}",
                    description=f"Complex test case {case_idx} for {suite_name}",
                    test_suite=suite_name
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
                    result=random.choice([
                        TestResult.PASSED.value,
                        TestResult.FAILED.value,
                        TestResult.SKIPPED.value,
                        TestResult.XFAILED.value,
                        TestResult.XPASSED.value
                    ]),
                    start_time=datetime.now() - timedelta(minutes=random.randint(1, 120)),
                    end_time=datetime.now() - timedelta(minutes=random.randint(0, 59)),
                    duration=random.uniform(0.1, 300.0),
                    environment="test",
                    failure="Test failure message" if random.random() < 0.2 else "",
                    failure_type="AssertionError" if random.random() < 0.2 else ""
                )
                session.add(execution)
                session.flush()

                # Add diverse metrics
                for metric_func in metrics_functions:
                    metrics = metric_func()
                    for name, value in metrics.items():
                        metric = CustomMetricModel(
                            test_execution_id=execution.id,
                            name=name,
                            value=value
                        )
                        session.add(metric)

                # Add complex steps
                step_count = random.randint(5, 15)
                steps = []
                for step_idx in range(step_count):
                    step = StepModel(
                        step_id=f"step_{execution.id}_{step_idx}",
                        sequence_number=step_idx + 1,
                        hierarchical_number=f"{step_idx + 1}",
                        indent_level=random.randint(0, 2),
                        step_function=f"verify_step_{step_idx + 1}",
                        content=f"Complex step {step_idx + 1} with detailed verification",
                        execution_record_id=execution.id,
                        test_function=execution.test_function,
                        completed=random.random() > 0.1,
                        start_time=execution.start_time + timedelta(seconds=step_idx * random.randint(1, 10))
                    )
                    steps.append(step)
                session.add_all(steps)

        Log.info(f"Generated {test_suites} suites with {cases_per_suite} cases each")
        return test_run_id


def test_large_onepager_report():
    """Integration test for one pager report with large dataset."""
    Log.info("Starting large one pager report generation test")
    TestRun.reset()

    # Initialize in-memory SQLite database
    db = AutomationDatabase('sqlite:///:memory:')
    Log.info("Creating database tables...")

    from models.base_model import Base

    # Ensure clean database state
    Base.metadata.drop_all(db.engine)
    Base.metadata.create_all(db.engine)

    # Verify all required tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    expected_tables = {'test_runs', 'test_cases', 'test_execution_records', 'custom_metrics', 'steps'}
    missing_tables = expected_tables - set(tables)

    if missing_tables:
        raise ValueError(f"Missing tables: {missing_tables}")

    Log.info(f"Database tables created successfully: {', '.join(tables)}")

    TestRun.initialize(
        owner="test_user",
        environment="test",
        worker_id="master",
        test_run_id=None,
        test_type=TestRunType.SINGLE
    )

    test_run_id = generate_complex_test_data(db, test_suites=10, cases_per_suite=20)
    Log.info(f"Generated large test dataset with ID: {test_run_id}")

    report_dir = LOG_DIR / "reports" / "one_pager"
    setup_css_files(report_dir, theme="classic")

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
        css_template="classic",
        output_dir=report_dir
    )

    generator = ReportGenerator(config, db)
    report_path = generator.generate_report(test_run_id, report_dir)

    assert report_path and report_path.exists(), f"Report file not found at {report_path}"
    Log.info(f"Generated large one pager report: {report_path}")

    verify_report_contents(report_path)

    TestRun.reset()
    return report_path


def test_large_drilldown_report():
    """Integration test for drilldown report with large dataset."""
    Log.info("Starting large drilldown report generation test")
    TestRun.reset()

    # Initialize in-memory SQLite database
    db = AutomationDatabase('sqlite:///:memory:')
    Log.info("Creating database tables...")

    from models.base_model import Base

    # Ensure clean database state
    Base.metadata.drop_all(db.engine)
    Base.metadata.create_all(db.engine)

    # Verify all required tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    expected_tables = {'test_runs', 'test_cases', 'test_execution_records', 'custom_metrics', 'steps'}
    missing_tables = expected_tables - set(tables)

    if missing_tables:
        raise ValueError(f"Missing tables: {missing_tables}")

    Log.info(f"Database tables created successfully: {', '.join(tables)}")

    # Initialize TestRun before data generation
    TestRun.initialize(
        owner="test_user",
        environment="test",
        worker_id="master",
        test_run_id=None,
        test_type=TestRunType.SINGLE
    )

    # Generate test data
    test_run_id = generate_complex_test_data(db, test_suites=15, cases_per_suite=25)
    Log.info(f"Generated large test dataset with ID: {test_run_id}")

    # Configure output directory for drilldown report
    report_dir = LOG_DIR / "reports" / "drilldown"
    setup_css_files(report_dir, theme="classic")

    # Create report configuration with classic theme
    config = ReportConfig(
        report_type=ReportType.DRILLDOWN,
        sections=[
            ReportSection.MAIN_SUMMARY,
            ReportSection.TEST_RESULTS,
            ReportSection.TEST_CASE_SUMMARY,
            ReportSection.SUITE_DETAILS
        ],
        table_config=ReportTableConfig(
            columns=[
                "test_name", "result", "duration", "steps", "custom_metrics",
                "failure", "failure_type", "test_start", "test_end"
            ],
            custom_columns=[],
            failed_threshold=80.0
        ),
        show_logs=True,
        show_charts=True,
        css_template="classic",
        output_dir=report_dir
    )

    # Generate report
    generator = ReportGenerator(config, db)
    report_path = generator.generate_report(test_run_id, report_dir)

    assert report_path and report_path.exists(), f"Report file not found at {report_path}"
    Log.info(f"Generated large drilldown report: {report_path}")

    # Verify drilldown specific elements
    suite_pages = list(report_dir.glob("suite_*.html"))
    assert len(suite_pages) == 15, f"Expected 15 suite pages, found {len(suite_pages)}"
    for suite_page in suite_pages:
        verify_report_contents(suite_page)

    # Verify main report
    verify_report_contents(report_path)

    TestRun.reset()
    return report_path