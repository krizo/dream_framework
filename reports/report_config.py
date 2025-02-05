"""Report configuration module."""
import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Any

from core.common_paths import TEMPLATES_DIR
from core.configuration.config_parser import ConfigParser
from core.logger import Log
from reports import DEFAULT_OUTPUT_DIR


class ReportType(Enum):
    """Available report types."""
    ONE_PAGER = "one_pager"
    DRILLDOWN = "drilldown"


class ReportSection(Enum):
    """Available report sections."""
    MAIN_SUMMARY = "main_summary"      # Overall test run summary
    TEST_RESULTS = "test_results"      # Test results by suite
    TEST_CASE_SUMMARY = "test_case_summary"  # Detailed test cases
    SUITE_DETAILS = "suite_details"    # Per-suite detailed view


@dataclass
class ReportTableConfig:
    """Configuration for report tables."""
    columns: List[str]
    custom_columns: List[str]
    failed_threshold: float

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.failed_threshold < 0 or self.failed_threshold > 100:
            raise ValueError("Failed threshold must be between 0 and 100")


@dataclass
class ReportConfig:
    """Main report configuration."""
    report_type: ReportType
    sections: List[ReportSection]
    table_config: ReportTableConfig
    show_logs: bool
    show_charts: bool
    css_template: str
    template_dir: Path = TEMPLATES_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.template_dir.exists():
            raise ValueError(f"Template directory does not exist: {self.template_dir}")

        # Validate and set CSS template
        self._set_css_template(self.css_template)

        # Convert string values to proper types
        self.show_logs = bool(self.show_logs)
        self.show_charts = bool(self.show_charts)

        # Validate sections
        if not self.sections:
            raise ValueError("At least one section must be specified")

        # Ensure all sections are valid ReportSection instances
        self.sections = [s if isinstance(s, ReportSection) else ReportSection(s) for s in self.sections]

        # Ensure report type is valid
        if not isinstance(self.report_type, ReportType):
            raise ValueError(f"Invalid report type: {self.report_type}")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _set_css_template(self, template: str):
        """Set CSS template with validation."""
        valid_templates = ["modern", "minimalist", "dark", "retro", "classic"]
        if template not in valid_templates:
            Log.warning(f"Invalid CSS template '{template}', using 'modern'")
            self.css_template = "modern"
        else:
            self.css_template = template


class ReportConfigParser(ConfigParser):
    """Parser for report configuration from config.ini."""

    SECTION_NAME = "REPORT"
    DEFAULT_COLUMNS = "test_name,result,duration,failure"

    @classmethod
    def _parse_string_list(cls, value: Any) -> List[str]:
        """
        Parse list of strings from configuration value.

        @param value: Value to parse (can be string or list)
        @return: List of strings
        """
        if not value:
            return []

        # If value is already a list
        if isinstance(value, list):
            return [str(item).strip() for item in value if item]

        # If value is a string, try different parsing methods
        if isinstance(value, str):
            try:
                # Try parsing as Python literal (for ["item1", "item2"] format)
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
            except (ValueError, SyntaxError):
                # If literal eval fails, treat as comma-separated
                return [item.strip() for item in value.split(',') if item.strip()]
            except Exception as e:
                Log.warning(f"Failed to parse list value: {str(e)}")
                return []

        Log.warning(f"Unsupported value type for list parsing: {type(value)}")
        return []

    @classmethod
    def get_config(cls) -> ReportConfig:
        """
        Get complete report configuration.

        @return: ReportConfig instance with parsed values
        """
        # Parse report type
        type_str = cls.get_value('type', 'one_pager')
        try:
            report_type = ReportType(type_str) if type_str else ReportType.ONE_PAGER
        except ValueError:
            Log.warning(f"Invalid report type: {type_str}, using default")
            report_type = ReportType.ONE_PAGER

        # Parse sections
        sections_str = cls.get_value('sections', 'main_summary,test_results')
        sections = []
        try:
            section_names = cls._parse_string_list(sections_str)
            for section in section_names:
                try:
                    sections.append(ReportSection(section.strip()))
                except ValueError:
                    Log.warning(f"Invalid section name: {section}")
        except Exception as e:
            Log.warning(f"Error parsing sections: {str(e)}")

        # Use defaults if no valid sections found
        if not sections:
            sections = [ReportSection.MAIN_SUMMARY, ReportSection.TEST_RESULTS]

        # Parse columns with defaults
        columns_value = cls.get_value('columns', cls.DEFAULT_COLUMNS)
        columns = cls._parse_string_list(columns_value)
        if not columns:
            columns = cls._parse_string_list(cls.DEFAULT_COLUMNS)

        # Parse custom columns
        custom_columns_value = cls.get_value('custom_columns', '[]')
        custom_columns = cls._parse_string_list(custom_columns_value)

        # Parse failed threshold with default
        try:
            failed_threshold = float(cls.get_value('failed_threshold', '90'))
        except (ValueError, TypeError):
            Log.warning("Invalid failed_threshold value, using default: 90")
            failed_threshold = 90.0

        # Parse output directory
        output_dir_str = cls.get_value('output_dir')
        output_dir = Path(output_dir_str) if output_dir_str else DEFAULT_OUTPUT_DIR

        # Parse boolean values
        show_logs = cls.get_value('show_logs', True)
        show_charts = cls.get_value('show_charts', True)
        css_template = cls.get_value('css_template', 'modern')

        # Create configuration
        return ReportConfig(
            report_type=report_type,
            sections=sections,
            table_config=ReportTableConfig(
                columns=columns,
                custom_columns=custom_columns,
                failed_threshold=failed_threshold
            ),
            show_logs=show_logs,
            show_charts=show_charts,
            css_template=css_template,
            template_dir=TEMPLATES_DIR,
            output_dir=output_dir
        )

    @classmethod
    def get_value_as_list(cls, key: str, default: List[Any] = None) -> List[Any]:
        """
        Get configuration value as list.

        @param key: Configuration key
        @param default: Default value if key not found
        @return: List value from configuration
        """
        value = cls.get_value(key)
        if value is None:
            return default if default is not None else []

        return cls._parse_string_list(value)