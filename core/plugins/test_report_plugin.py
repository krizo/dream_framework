"""Plugin for automatic test report generation."""
import os
from datetime import datetime
from pathlib import Path

from core.automation_database_manager import AutomationDatabaseManager
from core.logger import Log
from core.test_run import TestRun, TestRunStatus
from models.test_case_execution_record_model import TestExecutionRecordModel
from reports.report_config import ReportConfigParser
from reports.report_generator import ReportGenerator


class ReportingPlugin:
    """Plugin responsible for generating test execution reports."""

    # Define plugin order
    trylast = True  # This plugin should run last

    def __init__(self):
        """Initialize plugin state."""
        self.test_run = None
        self.start_time = None
        self.report_config = None
        self._is_xdist = False
        self._is_worker = False

    def pytest_configure(self, config):
        """
        Configure plugin and load reporting configuration.

        @param config: pytest Configuration object
        """
        try:
            # Load report configuration
            self.report_config = ReportConfigParser.get_config()

            # Check if running under xdist
            self._is_xdist = bool(config.getoption('dist', 'no') != 'no')
            self._is_worker = bool(os.environ.get('PYTEST_XDIST_WORKER'))

            if not self._is_worker:
                Log.info("Report generation configured")
                Log.info(f"Report type: {self.report_config.report_type.value}")
                self.start_time = datetime.now()

        except Exception as e:
            Log.error(f"Error configuring report plugin: {str(e)}")
            raise

    def pytest_sessionfinish(self, session, exitstatus):
        """
        Generate test execution report at the end of test session.

        @param session: pytest Session object
        @param exitstatus: session exit status
        """
        # Skip report generation for worker nodes
        if self._is_worker:
            Log.debug("Skipping report generation on worker node")
            return

        try:
            # Get test run from TestRun singleton
            self.test_run = TestRun.get_instance()
            if not self.test_run:
                Log.error("No active test run found")
                return

            # Generate report only if test run completed
            if self.test_run.status not in [TestRunStatus.COMPLETED, TestRunStatus.STARTED]:
                Log.warning(f"Skipping report generation - test run status: {self.test_run.status}")
                return

            db = AutomationDatabaseManager.get_database()

            # Create report generator
            generator = ReportGenerator(self.report_config, db)

            # Define report output directory
            report_dir = Path(self.test_run.get_log_dir()) / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            Log.info("Starting report generation...")
            Log.info(f"Report directory: {report_dir}")

            # Generate report
            report_path = generator.generate_report(
                self.test_run.test_run_id,
                report_dir
            )

            if report_path and report_path.exists():
                Log.info(f"Test report generated successfully: {report_path}")
                self._log_report_summary(db)
            else:
                Log.error("Failed to generate test report")

        except Exception as e:
            Log.error(f"Error generating test report: {str(e)}")
            import traceback
            Log.error(traceback.format_exc())

    def _log_report_summary(self, db):
        """
        Log summary of report generation.

        @param db: Database instance
        """
        try:
            with db.session_scope() as session:
                # Get execution statistics
                executions = session.query(TestExecutionRecordModel) \
                    .filter(TestExecutionRecordModel.test_run_id == self.test_run.test_run_id) \
                    .order_by(TestExecutionRecordModel.start_time) \
                    .all()

                total_duration = (datetime.now() - self.start_time).total_seconds()

                Log.separator("=")
                Log.info("Test Run Summary")
                Log.separator("-")
                Log.info(f"Test Run: {self.test_run.test_run_id}")
                Log.info(f"Environment: {self.test_run.environment}")
                Log.info(f"Type: {self.test_run.test_type.value}")
                Log.info(f"Start Time: {self.test_run.start_time}")
                Log.info(f"End Time: {self.test_run.end_time}")
                Log.info(f"Duration: {self.test_run.duration:.2f}s")
                Log.info(f"Total Tests: {len(executions)}")
                Log.info(f"Report Type: {self.report_config.report_type.value}")
                Log.info(f"Generation Time: {datetime.now()}")
                Log.info(f"Report Generation Duration: {total_duration:.2f}s")
                Log.separator("=")

        except Exception as e:
            Log.error(f"Error generating report summary: {str(e)}")

    def pytest_unconfigure(self, config):
        """Cleanup plugin resources."""
        if not self._is_worker:
            Log.info("Report plugin cleanup completed")

    @classmethod
    def get_metadata(cls) -> dict:
        """
        Get plugin metadata.

        @return: Dictionary with plugin metadata
        """
        return {
            'name': 'pytest-reporting',
            'version': '1.0.0',
            'description': 'Plugin for generating test execution reports',
            'author': 'Your Name',
            'requires': ['pytest>=7.0.0']
        }