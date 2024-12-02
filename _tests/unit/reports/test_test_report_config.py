"""Tests for report configuration module."""
import pytest


@pytest.fixture
def template_dir(tmp_path):
    """Create temporary template directory."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir


@pytest.fixture
def sample_config():
    """Provide sample configuration content."""
    return """
[REPORT]
type = drilldown
sections = main_summary,test_suite_summary
custom_columns = ["comments", "jira_link"]
failed_threshold = 90
columns = ["test_name", "description", "result"]
show_logs = true
show_charts = true
css_template = dark
"""


def test_report_type_parsing(template_dir):
    """Test parsing report type from configuration."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        # Test valid types
        def mock_one_pager(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_one_pager
        config = ReportConfigParser.get_config()
        assert config.report_type == ReportType.ONE_PAGER

        # Test drilldown type
        def mock_drilldown(key, default=None):
            values = {
                'type': 'drilldown',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_drilldown
        config = ReportConfigParser.get_config()
        assert config.report_type == ReportType.DRILLDOWN

        # Test default value
        def mock_default(key, default=None):
            values = {
                'type': None,
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_default
        config = ReportConfigParser.get_config()
        assert config.report_type == ReportType.ONE_PAGER

        # Test invalid value
        def mock_invalid(key, default=None):
            values = {
                'type': 'invalid',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_invalid
        with pytest.raises(ValueError):
            ReportConfigParser.get_config()


def test_report_sections_parsing(template_dir):
    """Test parsing report sections from configuration."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        def mock_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary,test_suite_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_values

        config = ReportConfigParser.get_config()
        assert len(config.sections) == 2
        assert ReportSection.MAIN_SUMMARY in config.sections
        assert ReportSection.TEST_SUITE_SUMMARY in config.sections


def test_table_config_parsing(template_dir):
    """Test parsing table configuration."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        def mock_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name", "result"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_values

        config = ReportConfigParser.get_config()
        assert len(config.table_config.columns) == 2
        assert 'test_name' in config.table_config.columns
        assert 'result' in config.table_config.columns
        assert len(config.table_config.custom_columns) == 1
        assert config.table_config.failed_threshold == 90.0


def test_report_config_validation(template_dir):
    """Test report configuration validation."""
    # Test valid config
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=ReportTableConfig(
            columns=['test_name'],
            custom_columns=['comments'],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template='default',
        template_dir=template_dir
    )

    assert config is not None
    assert config.report_type == ReportType.ONE_PAGER

    # Test invalid failed threshold
    with pytest.raises(ValueError):
        ReportConfig(
            report_type=ReportType.ONE_PAGER,
            sections=[ReportSection.MAIN_SUMMARY],
            table_config=ReportTableConfig(
                columns=['test_name'],
                custom_columns=['comments'],
                failed_threshold=101.0  # Invalid value
            ),
            show_logs=True,
            show_charts=True,
            css_template='default',
            template_dir=template_dir
        )


def test_config_file_integration(sample_config, template_dir):
    """Test reading configuration from file."""
    config_file = template_dir / "test_config.ini"
    with open(config_file, 'w') as f:
        f.write(sample_config)

    with patch('reports.report_config.ReportConfigParser._config_path', config_file), \
            patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        def mock_values(key, default=None):
            values = {
                'type': 'drilldown',
                'sections': 'main_summary,test_suite_summary',
                'columns': '["test_name", "description", "result"]',
                'custom_columns': '["comments", "jira_link"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'dark'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_values

        config = ReportConfigParser.get_config()

        assert config.report_type == ReportType.DRILLDOWN
        assert len(config.sections) == 2
        assert len(config.table_config.custom_columns) == 2
        assert config.table_config.failed_threshold == 90.0
        assert config.css_template == 'dark'


def test_default_values(template_dir):
    """Test default configuration values."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        def mock_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '[]',
                'custom_columns': '[]',
                'failed_threshold': '100',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_values

        config = ReportConfigParser.get_config()

        assert config.report_type == ReportType.ONE_PAGER
        assert ReportSection.MAIN_SUMMARY in config.sections
        assert config.table_config.failed_threshold == 100.0
        assert bool(config.show_logs) is True
        assert bool(config.show_charts) is True
        assert config.css_template == 'default'


def test_custom_columns_validation(template_dir):
    """Test validation of custom columns configuration."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        # Test valid custom columns
        def mock_valid_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments", "jira_link"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_valid_values
        config = ReportConfigParser.get_config()
        assert len(config.table_config.custom_columns) == 2
        assert "comments" in config.table_config.custom_columns
        assert "jira_link" in config.table_config.custom_columns

        # Test invalid format
        def mock_invalid_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': 'invalid_format',  # Invalid format
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_invalid_values
        config = ReportConfigParser.get_config()
        assert isinstance(config.table_config.custom_columns, list)
        assert len(config.table_config.custom_columns) == 0

        # Test empty list
        def mock_empty_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '[]',  # Empty list
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_empty_values
        config = ReportConfigParser.get_config()
        assert isinstance(config.table_config.custom_columns, list)
        assert len(config.table_config.custom_columns) == 0

        # Test None value
        def mock_none_values(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': None,  # None value
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_none_values
        config = ReportConfigParser.get_config()
        assert isinstance(config.table_config.custom_columns, list)
        assert len(config.table_config.custom_columns) == 0


def test_output_dir_configuration(template_dir):
    """Test output directory configuration."""
    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        # Test custom output directory
        def mock_with_output_dir(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default',
                'output_dir': '/custom/output/dir'
            }
            return values.get(key, default)

        mock_get.side_effect = mock_with_output_dir
        config = ReportConfigParser.get_config()
        assert config.output_dir == Path('/custom/output/dir')

        # Test default output directory
        def mock_without_output_dir(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default',
                'output_dir': None
            }
            return values.get(key, default)

        mock_get.side_effect = mock_without_output_dir
        config = ReportConfigParser.get_config()
        assert config.output_dir == DEFAULT_OUTPUT_DIR


"""Tests for report configuration module."""
import pytest
from pathlib import Path
from unittest.mock import patch

from reports import DEFAULT_OUTPUT_DIR
from reports.report_config import (
    ReportConfigParser, ReportType, ReportSection,
    ReportTableConfig, ReportConfig
)

# ... (poprzednie fixtury) ...

def test_output_dir_configuration(template_dir, tmp_path):
    """Test output directory configuration."""
    custom_output = tmp_path / "custom_output"

    with patch('reports.report_config.ReportConfigParser.get_value') as mock_get:
        # Test custom output directory
        def mock_with_output_dir(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default',
                'output_dir': str(custom_output)
            }
            return values.get(key, default)

        mock_get.side_effect = mock_with_output_dir
        config = ReportConfigParser.get_config()
        assert config.output_dir == custom_output
        assert config.output_dir.exists()

        # Test default output directory
        def mock_without_output_dir(key, default=None):
            values = {
                'type': 'one_pager',
                'sections': 'main_summary',
                'columns': '["test_name"]',
                'custom_columns': '["comments"]',
                'failed_threshold': '90',
                'show_logs': 'true',
                'show_charts': 'true',
                'css_template': 'default',
                'output_dir': None
            }
            return values.get(key, default)

        mock_get.side_effect = mock_without_output_dir
        config = ReportConfigParser.get_config()
        assert config.output_dir == DEFAULT_OUTPUT_DIR


def test_invalid_output_dir(template_dir, tmp_path):
    """Test handling of invalid output directory."""
    # Test non-existent parent directory
    invalid_dir = tmp_path / "nonexistent" / "reports"

    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=ReportTableConfig(
            columns=['test_name'],
            custom_columns=['comments'],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template='default',
        template_dir=template_dir,
        output_dir=invalid_dir
    )

    # Should create all parent directories
    assert invalid_dir.exists()

    # Test with relative path
    relative_dir = Path("reports/output")
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=ReportTableConfig(
            columns=['test_name'],
            custom_columns=['comments'],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template='default',
        template_dir=template_dir,
        output_dir=relative_dir
    )

    assert relative_dir.exists()
    relative_dir.rmdir()  # Cleanup


def test_output_dir_creation(template_dir, tmp_path):
    """Test automatic creation of output directory."""
    output_dir = tmp_path / "reports" / "output"
    assert not output_dir.exists()

    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=ReportTableConfig(
            columns=['test_name'],
            custom_columns=['comments'],
            failed_threshold=90.0
        ),
        show_logs=True,
        show_charts=True,
        css_template='default',
        template_dir=template_dir,
        output_dir=output_dir
    )

    assert output_dir.exists()


def test_output_dir_permissions(template_dir, tmp_path):
    """Test handling of output directory permissions."""
    output_dir = tmp_path / "reports" / "output"
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    # Create directory with read-only permissions
    output_dir.parent.chmod(0o555)

    try:
        with pytest.raises(PermissionError):
            config = ReportConfig(
                report_type=ReportType.ONE_PAGER,
                sections=[ReportSection.MAIN_SUMMARY],
                table_config=ReportTableConfig(
                    columns=['test_name'],
                    custom_columns=['comments'],
                    failed_threshold=90.0
                ),
                show_logs=True,
                show_charts=True,
                css_template='default',
                template_dir=template_dir,
                output_dir=output_dir
            )
    finally:
        # Restore permissions for cleanup
        output_dir.parent.chmod(0o755)
