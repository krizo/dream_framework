"""Report generation module."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from core.automation_database import AutomationDatabase
from core.common_paths import TEMPLATES_DIR
from core.logger import Log
from core.test_result import TestResult
from helpers.data_time_helper import format_duration, format_timestamp, calculate_duration
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_run_model import TestRunModel
from reports.report_config import ReportConfig, ReportType, ReportSection
from reports.report_factory import ReportComponentFactory


@dataclass
class ReportData:
    """Container for report data."""
    test_run: TestRunModel
    executions: List[TestExecutionRecordModel]
    summary: Dict[str, Any]
    suite_summaries: Dict[str, Dict[str, Any]]


class ReportGenerator:
    """Main report generator class."""

    COLUMN_HEADERS: Dict[str, Tuple[str, str]] = {
        'test_name': ('Test Name', 'file-text'),
        'test_function': ('Function', 'code'),
        'description': ('Description', 'file'),
        'result': ('Result', 'check-circle'),
        'duration': ('Duration', 'clock'),
        'failure': ('Failure', 'alert-triangle'),
        'failure_type': ('Failure Type', 'alert-octagon'),
        'test_start': ('Start Time', 'calendar'),
        'test_end': ('End Time', 'calendar-check'),
        'steps': ('Steps', 'list'),
        'custom_metrics': ('Metrics', 'drafting-compass')
    }

    def __init__(self, config: ReportConfig, database: AutomationDatabase):
        """
        Initialize report generator.

        @param config: Report configuration
        @param database: Database instance
        """
        self.config = config
        self.db = database
        self.jinja_env = Environment(
            loader=FileSystemLoader([str(config.template_dir), str(TEMPLATES_DIR)]),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters and functions
        self.jinja_env.filters['format_duration'] = format_duration
        self.jinja_env.filters['format_timestamp'] = format_timestamp
        self.jinja_env.globals['calculate_duration'] = calculate_duration
        self.jinja_env.globals['icon'] = self._render_icon
        self.jinja_env.globals['get_column_header'] = self._get_column_header
        self.jinja_env.globals['render_status_icon'] = self._render_status_icon

    def generate_report(self, test_run_id: str, output_dir: Path) -> Optional[Path]:
        """
        Generate report for test run.

        @param test_run_id: Test run identifier
        @param output_dir: Output directory for report
        @return: Path to generated report
        """
        try:
            Log.info(f"Starting report generation for test run: {test_run_id}")
            with self.db.session_scope() as session:
                test_run = session.query(TestRunModel).filter_by(test_run_id=test_run_id).first()
                if not test_run:
                    Log.error(f"Test run {test_run_id} not found")
                    return None

                # Calculate duration if needed
                if test_run.start_time and test_run.end_time and test_run.duration is None:
                    test_run.duration = calculate_duration(test_run.start_time, test_run.end_time)

                executions = session.query(TestExecutionRecordModel) \
                    .filter_by(test_run_id=test_run_id) \
                    .order_by(TestExecutionRecordModel.start_time) \
                    .all()

                Log.info(f"Found {len(executions)} test executions")
                report_data = self._prepare_report_data(test_run, executions)
                return self._render_report(report_data, output_dir)

        except Exception as e:
            Log.error(f"Failed to generate report: {str(e)}")
            import traceback
            Log.error(traceback.format_exc())
            return None

    def _calculate_summary(self, executions: List[TestExecutionRecordModel]) -> Dict[str, Any]:
        """
        Calculate main summary statistics.

        @param executions: List of test executions
        @return: Dictionary with summary statistics
        """
        total = len(executions)
        failed = sum(1 for e in executions if e.result == TestResult.FAILED.value)
        skipped = sum(1 for e in executions if e.result == TestResult.SKIPPED.value)
        attempted = total - skipped
        passed_percent = ((attempted - failed) / attempted * 100) if attempted > 0 else 0.0

        summary = {
            'total': total,
            'attempted': attempted,
            'failed': failed,
            'skipped': skipped,
            'passed_percent': passed_percent,
            'result': 'FAILED' if passed_percent < self.config.table_config.failed_threshold else 'PASSED'
        }

        Log.debug(f"Calculated summary: {summary}")
        return summary

    @staticmethod
    def _calculate_suite_summaries(executions: List[TestExecutionRecordModel]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate summary statistics per test suite.

        @param executions: List of test executions
        @return: Dictionary with suite statistics
        """
        suites: Dict[str, Dict[str, Any]] = {}
        for execution in executions:
            if not execution.test_case:
                continue

            suite = execution.test_case.test_suite or 'Default Suite'
            if suite not in suites:
                suites[suite] = {
                    'total': 0,
                    'attempted': 0,
                    'failed': 0,
                    'skipped': 0,
                    'executions': [],
                    'start_time': None,
                    'end_time': None,
                    'duration': 0.0
                }

            stats = suites[suite]
            stats['total'] += 1
            stats['duration'] += execution.duration or 0.0

            if execution.result == TestResult.SKIPPED.value:
                stats['skipped'] += 1
            else:
                stats['attempted'] += 1
                if execution.result == TestResult.FAILED.value:
                    stats['failed'] += 1

            stats['executions'].append(execution)

            # Update suite timing
            if execution.start_time:
                if not stats['start_time'] or execution.start_time < stats['start_time']:
                    stats['start_time'] = execution.start_time
            if execution.end_time:
                if not stats['end_time'] or execution.end_time > stats['end_time']:
                    stats['end_time'] = execution.end_time

        # Calculate additional statistics
        for suite_data in suites.values():
            attempted = suite_data['attempted']
            failed = suite_data['failed']
            suite_data['passed_percent'] = ((attempted - failed) / attempted * 100) if attempted > 0 else 0.0
            suite_data['result'] = 'FAILED' if failed > 0 else 'PASSED'

        Log.debug(f"Calculated summaries for {len(suites)} test suites")
        return suites

    def _prepare_report_data(self, test_run: TestRunModel,
                             executions: List[TestExecutionRecordModel]) -> ReportData:
        """
        Prepare data for report.

        @param test_run: Test run model
        @param executions: List of test executions
        @return: ReportData instance
        """
        summary = self._calculate_summary(executions)
        suite_summaries = self._calculate_suite_summaries(executions)

        Log.debug("Report data prepared successfully")
        return ReportData(
            test_run=test_run,
            executions=executions,
            summary=summary,
            suite_summaries=suite_summaries
        )

    def _render_report(self, data: ReportData, output_dir: Path) -> Path:
        """
        Render report from templates.

        @param data: Report data to render
        @param output_dir: Output directory for report
        @return: Path to generated report
        """
        Log.info(f"Rendering report to directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Setup directory structure
        logs_dir = output_dir / 'steps_logs'
        logs_dir.mkdir(exist_ok=True)

        # Copy CSS files
        self._copy_css_files(output_dir)

        # Generate logs if enabled
        if self.config.show_logs:
            for execution in data.executions:
                if execution.steps:
                    steps_path = ReportComponentFactory.get_steps_log_path(output_dir=output_dir,
                                                                           test_function=execution.test_function)
                    ReportComponentFactory.create_steps_log_page(steps=execution.steps, output_path=steps_path,
                                                                 test_function=execution.test_function)

                # Generate metrics logs
                if execution.custom_metrics:
                    metrics_path = ReportComponentFactory.get_metrics_log_path(
                        output_dir=output_dir,
                        test_function=execution.test_function)
                    ReportComponentFactory.create_metrics_log_page(
                        execution=execution,
                        output_path=metrics_path,
                        test_function=execution.test_function
                    )
        try:
            # Select and render template
            template_name = 'one_pager.html' if self.config.report_type == ReportType.ONE_PAGER else 'drilldown_main.html'
            template = self.jinja_env.get_template(template_name)

            # Render main template
            content = template.render(
                config=self.config,
                test_run=data.test_run,
                summary=data.summary,
                suites=data.suite_summaries,
                current_time=datetime.now(),
                ReportSection=ReportSection,
                css_path=f"css/{self.config.css_template}.css"
            )

            # Save output
            output_file = output_dir / (
                f"report_{data.test_run.test_run_id}.html" if self.config.report_type == ReportType.ONE_PAGER else "index.html")
            output_file.write_text(content)

            # Generate additional pages for drilldown report
            if self.config.report_type == ReportType.DRILLDOWN:
                self._generate_drilldown_pages(data, output_dir)

            Log.info(f"Generated report: {output_file}")
            return output_file

        except Exception as e:
            Log.error(f"Error rendering report template: {str(e)}")
            raise

    def _generate_drilldown_pages(self, data: ReportData, output_dir: Path) -> None:
        """
        Generate additional pages for drilldown report.

        @param data: Report data
        @param output_dir: Output directory
        """
        suite_template = self.jinja_env.get_template('drilldown_suite.html')
        for suite_name, suite_data in data.suite_summaries.items():
            safe_name = suite_name.lower().replace(' ', '_')
            suite_file = output_dir / f"suite_{safe_name}.html"

            content = suite_template.render(
                config=self.config,
                test_run=data.test_run,
                suite_name=suite_name,
                suite_data=suite_data,
                current_time=datetime.now(),
                ReportSection=ReportSection,
                css_path=f"css/{self.config.css_template}.css"
            )
            suite_file.write_text(content)
            Log.debug(f"Generated suite page: {suite_file}")

    @staticmethod
    def _render_icon(name: str, class_name: str = '') -> Markup:
        """
        Render Lucide icon tag.

        @param name: Icon name
        @param class_name: Optional CSS class
        @return: HTML markup for icon
        """
        icon_html = f'<i data-lucide="{name}" class="lucide {class_name}"></i>'
        return Markup(icon_html)

    def _get_column_header(self, col: str) -> Markup:
        """
        Get column header with icon.

        @param col: Column name
        @return: HTML markup with header and icon
        """
        header, icon_name = self.COLUMN_HEADERS.get(col, (col.replace('_', ' ').title(), 'help-circle'))
        return Markup(f'{self._render_icon(icon_name)} {header}')

    def _render_status_icon(self, status: str) -> Markup:
        """
        Render status icon with appropriate color.

        @param status: Status string (PASSED/FAILED/SKIPPED)
        @return: HTML markup for status icon
        """
        icon_map = {
            'PASSED': ('check-circle', 'status-passed'),
            'FAILED': ('x-circle', 'status-failed'),
            'SKIPPED': ('alert-circle', 'status-skipped')
        }
        icon_name, class_name = icon_map.get(status, ('help-circle', ''))
        return self._render_icon(icon_name, class_name)

    def _copy_css_files(self, output_dir: Path) -> None:
        """
        Copy CSS files to output directory.
        Includes base layout, theme file, steps and custom metrics CSS.

        @param output_dir: Output directory path
        """
        css_dir = output_dir / 'css'
        css_dir.mkdir(exist_ok=True)

        # Copy base layout CSS
        base_css_src = self.config.template_dir.parent / 'css' / 'base-layout.css'
        if not base_css_src.exists():
            Log.error(f"Base layout CSS not found: {base_css_src}")
            return

        base_css_dest = css_dir / 'base-layout.css'
        base_css_dest.write_text(base_css_src.read_text())
        Log.debug("Copied base layout CSS")

        # Copy step logs CSS
        steps_css_src = self.config.template_dir.parent / 'css' / 'step_logs.css'
        if steps_css_src.exists():
            steps_css_dest = css_dir / 'step_logs.css'
            steps_css_dest.write_text(steps_css_src.read_text())
            Log.debug("Copied step logs CSS")
        else:
            Log.warning(f"Step logs CSS not found: {steps_css_src}")

        # Copy custom metrics CSS
        metrics_css_src = self.config.template_dir.parent / 'css' / 'custom_metrics_logs.css'
        if metrics_css_src.exists():
            metrics_css_dest = css_dir / 'custom_metrics_logs.css'
            metrics_css_dest.write_text(metrics_css_src.read_text())
            Log.debug("Copied custom metrics CSS")
        else:
            Log.warning(f"Custom metrics CSS not found: {metrics_css_src}")

        # Copy theme CSS
        theme_file = f"theme-{self.config.css_template}.css"
        theme_src = self.config.template_dir.parent / 'css' / theme_file

        if not theme_src.exists():
            Log.warning(f"Theme file not found: {theme_src}")
            theme_file = "theme-modern.css"
            theme_src = self.config.template_dir.parent / 'css' / theme_file
            if not theme_src.exists():
                Log.error("Modern theme fallback not found")
                return

        theme_dest = css_dir / theme_file
        theme_dest.write_text(theme_src.read_text())
        Log.debug(f"Copied theme CSS: {theme_file}")
