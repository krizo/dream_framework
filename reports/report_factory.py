"""Factory for report components."""
from pathlib import Path
from typing import Dict, List, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.common_paths import TEMPLATES_DIR
from models.step_model import StepModel
from models.test_case_execution_record_model import TestExecutionRecordModel


class ReportComponentFactory:
    """Factory for creating report components."""

    @staticmethod
    def create_steps_log_page(steps: List[StepModel], output_path: Path, test_function: str) -> None:
        """
        Create HTML page with test execution logs.
        Steps are sorted by sequence number and formatted with proper indentation.

        @param steps: List of test steps to display
        @param output_path: Output file path
        @param test_function: Name of test function
        """
        # Sort steps by sequence number to maintain proper order
        sorted_steps = sorted(steps, key=lambda x: x.sequence_number)

        # Get execution time from first step
        execution_time = sorted_steps[0].start_time.strftime("%Y-%m-%d %H:%M:%S") if sorted_steps else "Unknown"

        # Setup Jinja environment
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('steps_log_template.html')

        # Render template with data
        content = template.render(
            steps=sorted_steps,
            test_function=test_function,
            execution_time=execution_time,
            total_steps=len(sorted_steps)
        )

        # Create steps_logs directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save output
        output_path.write_text(content)

    @staticmethod
    def create_metrics_log_page(execution: TestExecutionRecordModel, output_path: Path, test_function: str) -> None:
        """
        Create HTML page with test metrics.
        Metrics are displayed in a similar style to steps log.

        @param execution: Test execution record containing metrics
        @param output_path: Output file path
        @param test_function: Test function name
        """
        def pprint_filter(value: Any) -> str:
            import json
            if isinstance(value, (dict, list)):
                return json.dumps(value, indent=2)
            return str(value)

        # Setup Jinja environment
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )
        env.filters['pprint'] = pprint_filter
        template = env.get_template('metrics_log_template.html')

        # Render template with data
        content = template.render(
            metrics=execution.custom_metrics,
            test_function=test_function,
            test_case_name=execution.test_case.name if execution.test_case else execution.name,
            total_metrics=len(execution.custom_metrics)
        )

        # Create metrics_logs directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save output
        output_path.write_text(content)

    @staticmethod
    def get_steps_log_path(output_dir: Path, test_function: str) -> Path:
        """
        Get path for steps log file.

        @param output_dir: Base output directory
        @param test_function: Test function name
        @return: Path to steps log file
        """
        return output_dir / 'steps_logs' / f"{test_function}_steps.html"


    @staticmethod
    def has_steps_log(output_dir: Path, test_function: str) -> bool:
        """
        Check if steps log exists for given test function.

        @param output_dir: Base output directory
        @param test_function: Test function name
        @return: True if log exists, False otherwise
        """
        log_path = ReportComponentFactory.get_steps_log_path(output_dir, test_function)
        return log_path.exists()

    @staticmethod
    def get_metrics_log_path(output_dir: Path, test_function: str) -> Path:
        """
        Get path for metrics log file.

        @param output_dir: Base output directory
        @param test_function: Test function name
        @return: Path to metrics log file
        """
        return output_dir / 'metrics_logs' / f"{test_function}_metrics.html"

    @staticmethod
    def has_metrics_log(output_dir: Path, test_function: str) -> bool:
        """
        Check if metrics log exists for given test function.

        @param output_dir: Base output directory
        @param test_function: Test function name
        @return: True if log exists, False otherwise
        """
        log_path = ReportComponentFactory.get_metrics_log_path(output_dir, test_function)
        return log_path.exists()

    @staticmethod
    def create_chart_data(summary: Dict[str, Any]) -> Dict[str, Any]:
        """Create chart data from summary."""
        return {
            'labels': ['Passed', 'Failed', 'Skipped'],
            'datasets': [{
                'data': [
                    summary['attempted'] - summary['failed'],
                    summary['failed'],
                    summary['skipped']
                ],
                'backgroundColor': [
                    '#27ae60',  # Passed
                    '#c0392b',  # Failed
                    '#f39c12'  # Skipped
                ]
            }]
        }

    @staticmethod
    def create_suite_chart_data(suites: Dict[str, Dict]) -> Dict[str, Any]:
        """Create chart data for test suites."""
        labels = list(suites.keys())
        passed = []
        failed = []
        skipped = []

        for suite in suites.values():
            passed.append(suite['attempted'] - suite['failed'])
            failed.append(suite['failed'])
            skipped.append(suite['skipped'])

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Passed',
                    'data': passed,
                    'backgroundColor': '#27ae60'
                },
                {
                    'label': 'Failed',
                    'data': failed,
                    'backgroundColor': '#c0392b'
                },
                {
                    'label': 'Skipped',
                    'data': skipped,
                    'backgroundColor': '#f39c12'
                }
            ]
        }
