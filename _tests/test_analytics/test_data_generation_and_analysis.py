import random
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pytest

from core.automation_database import AutomationDatabase
from core.logger import Log
from core.test_result import TestResult
from models.custom_metric_model import CustomMetricModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_case_model import TestCaseModel

pytestmark = pytest.mark.no_database_plugin

@pytest.fixture
def test_db():
    """Create in-memory database for testing."""
    db = AutomationDatabase('sqlite:///:memory:')
    db.create_tables()
    return db


@pytest.fixture
def test_data(test_db):
    """Generate test data directly in database."""
    with test_db.session_scope() as session:
        # Create test case
        test_case = TestCaseModel(
            test_id="payment_tests::test_payment_processing",
            test_module="payment_tests.py",
            test_function="test_payment_processing",
            name="Payment Processing Test",
            description="Verify payment processing flow",
            test_suite="Payment Tests",
            properties={
                "SCOPE": "E2E",
                "COMPONENT": "Payment Gateway",
                "TEST_LEVEL": "Integration"
            }
        )
        session.add(test_case)
        session.flush()

        # Generate test executions
        base_time = datetime.now() - timedelta(days=30)
        environments = ['dev', 'staging', 'prod']

        for i in range(100):  # Generate 100 executions
            # Randomize test conditions
            env = random.choice(environments)
            is_success = random.random() > 0.1  # 90% success rate
            exec_time = base_time + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            duration = random.uniform(0.1, 2.0)

            # Create execution record
            execution = TestExecutionRecordModel(
                test_case_id=test_case.id,
                test_run_id=f"RUN_{i + 1}",
                test_module=test_case.test_module,
                test_function=test_case.test_function,
                name=test_case.name,
                description=test_case.description,
                result=is_success,
                start_time=exec_time,
                end_time=exec_time + timedelta(seconds=duration),
                duration=duration,
                environment=env
            )

            # Add failure details if test failed
            if not is_success:
                failure_type = random.choice(["TimeoutError", "ValidationError", "NetworkError"])
                execution.failure_type = failure_type
                execution.failure = f"Test failed with {failure_type}"

            session.add(execution)
            session.flush()

            # Add custom metrics
            metrics = [
                CustomMetricModel(
                    test_execution_id=execution.id,
                    name="payment_amount",
                    value=round(random.uniform(10.0, 999.99), 2)
                ),
                CustomMetricModel(
                    test_execution_id=execution.id,
                    name="processing_time_ms",
                    value=random.randint(100, 500)
                ),
                CustomMetricModel(
                    test_execution_id=execution.id,
                    name="memory_usage_mb",
                    value=random.randint(200, 400)
                ),
                CustomMetricModel(
                    test_execution_id=execution.id,
                    name="transaction_id",
                    value=f"tx_{random.randint(10000, 99999)}"
                )
            ]

            # Add error metrics for failed tests
            if not is_success:
                metrics.extend([
                    CustomMetricModel(
                        test_execution_id=execution.id,
                        name="error_type",
                        value=failure_type
                    ),
                    CustomMetricModel(
                        test_execution_id=execution.id,
                        name="error_details",
                        value={
                            "message": f"Test failed with {failure_type}",
                            "timestamp": exec_time.isoformat(),
                            "additional_info": {
                                "endpoint": "/api/payments",
                                "request_id": f"req_{random.randint(1000, 9999)}"
                            }
                        }
                    )
                ])

            for metric in metrics:
                session.add(metric)

        return test_case.id


def test_analyze_test_stability(test_db, test_data):
    """Analyze test stability across environments."""
    with test_db.session_scope() as session:
        executions = session.query(TestExecutionRecordModel) \
            .filter(TestExecutionRecordModel.test_case_id == test_data) \
            .all()

        env_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
        for execution in executions:
            env = execution.environment
            env_stats[env]["total"] += 1
            env_stats[env]["passed" if execution.result else "failed"] += 1

        Log.info("Test Stability Analysis")
        Log.separator()

        for env, stats in env_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            Log.info(f"Environment: {env}")
            Log.info(f"Total Executions: {stats['total']}")
            Log.info(f"Success Rate: {success_rate:.2f}%")

            assert success_rate > 0, f"Success rate for {env} below 80%"
            assert stats["total"] > 5, f"Too few executions for {env}"


def test_analyze_performance_patterns(test_db, test_data):
    """Analyze performance patterns and trends."""
    with test_db.session_scope() as session:
        # Get successful executions with their metrics
        metrics = session.query(
            TestExecutionRecordModel,
            CustomMetricModel.name,
            CustomMetricModel.value
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.test_case_id == test_data,
            TestExecutionRecordModel.result == True,
            CustomMetricModel.name.in_(['processing_time_ms', 'memory_usage_mb'])
        ).all()

        # Organize metrics by environment
        env_metrics = defaultdict(lambda: defaultdict(list))
        for execution, metric_name, metric_value in metrics:
            env_metrics[execution.environment][metric_name].append(float(metric_value))

        Log.info("Performance Analysis")
        Log.separator()

        for env, metrics in env_metrics.items():
            proc_times = metrics['processing_time_ms']
            mem_usage = metrics['memory_usage_mb']

            Log.info(f"Environment: {env}")
            Log.info(f"Processing Time (avg): {np.mean(proc_times):.2f}ms")
            Log.info(f"Processing Time (p95): {np.percentile(proc_times, 95):.2f}ms")
            Log.info(f"Memory Usage (avg): {np.mean(mem_usage):.2f}MB")

            assert np.mean(proc_times) < 500, f"High average processing time in {env}"
            assert np.percentile(proc_times, 95) < 600, f"High P95 processing time in {env}"


def test_analyze_failure_patterns(test_db, test_data):
    """Analyze patterns in test failures."""
    with test_db.session_scope() as session:
        # Get failed executions with their error details
        failed_executions = session.query(
            TestExecutionRecordModel,
            CustomMetricModel
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.test_case_id == test_data,
            TestExecutionRecordModel.result == False,
            CustomMetricModel.name == 'error_details'
        ).all()

        failure_patterns = defaultdict(lambda: defaultdict(int))
        for execution, metric in failed_executions:
            failure_type = execution.failure_type
            env = execution.environment
            failure_patterns[failure_type][env] += 1

        Log.info("Failure Pattern Analysis")
        Log.info("=======================")

        for failure_type, env_counts in failure_patterns.items():
            Log.info(f"Failure Type: {failure_type}")
            for env, count in env_counts.items():
                Log.info(f"{env}: {count} occurrences")

            total_failures = sum(env_counts.values())
            assert total_failures < 20, f"Too many {failure_type} failures"


def test_analyze_performance_trends(test_db, test_data):
    """Analyze performance trends over time."""
    with test_db.session_scope() as session:
        # Get metrics ordered by time
        metrics = session.query(
            TestExecutionRecordModel.start_time,
            TestExecutionRecordModel.environment,
            CustomMetricModel.value
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.test_case_id == test_data,
            CustomMetricModel.name == 'processing_time_ms',
            TestExecutionRecordModel.result == TestResult.PASSED.value
        ).order_by(
            TestExecutionRecordModel.start_time
        ).all()

        # Analyze trends by environment
        env_trends = defaultdict(list)
        for start_time, env, value in metrics:
            env_trends[env].append((start_time, float(value)))

        Log.info("Performance Trends Analysis")

        for env, trend_data in env_trends.items():
            times = [t[1] for t in trend_data]

            # Calculate trends using rolling average
            window = 5
            rolling_avg = [
                sum(times[i:i + window]) / window
                for i in range(len(times) - window + 1)
            ]

            Log.info(f"Environment: {env}")
            Log.info(f"Initial Average: {np.mean(times[:10]):.2f}ms")
            Log.info(f"Final Average: {np.mean(times[-10:]):.2f}ms")

            # Check for significant degradation
            assert np.mean(times[-10:]) < np.mean(times[:10]) * 1.5, \
                f"Significant performance degradation detected in {env}"
