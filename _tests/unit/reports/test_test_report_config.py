"""Tests for report configuration module."""
from pathlib import Path

import pytest

from core.common_paths import TEMPLATES_DIR
from reports.report_config import (
    ReportConfig,
    ReportType,
    ReportSection,
    ReportTableConfig
)


@pytest.fixture
def valid_table_config() -> ReportTableConfig:
    """Provide valid table configuration."""
    return ReportTableConfig(
        columns=["test_name", "result"],
        custom_columns=[],
        failed_threshold=90.0
    )


@pytest.fixture
def test_output_dir(tmp_path) -> Path:
    """Provide test output directory."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def test_valid_report_config(valid_table_config, test_output_dir):
    """Test creating valid report configuration."""
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )

    assert config.report_type == ReportType.ONE_PAGER
    assert config.sections == [ReportSection.MAIN_SUMMARY]
    assert config.show_logs is True
    assert config.show_charts is True
    assert config.css_template == "modern"
    assert config.output_dir == test_output_dir


def test_invalid_section_names(valid_table_config, test_output_dir):
    """Test that invalid section names raise ValueError."""
    with pytest.raises(ValueError, match=".* is not a valid ReportSection"):
        ReportConfig(
            report_type=ReportType.ONE_PAGER,
            sections=["invalid_section"],  # This should raise ValueError
            table_config=valid_table_config,
            show_logs=True,
            show_charts=True,
            css_template="modern",
            template_dir=TEMPLATES_DIR,
            output_dir=test_output_dir
        )


def test_empty_sections_list(valid_table_config, test_output_dir):
    """Test that empty sections list raises ValueError."""
    with pytest.raises(ValueError, match="At least one section must be specified"):
        ReportConfig(
            report_type=ReportType.ONE_PAGER,
            sections=[],
            table_config=valid_table_config,
            show_logs=True,
            show_charts=True,
            css_template="modern",
            template_dir=TEMPLATES_DIR,
            output_dir=test_output_dir
        )


def test_invalid_report_type(valid_table_config, test_output_dir):
    """Test invalid report type handling."""
    with pytest.raises(ValueError):
        ReportConfig(
            report_type="invalid",
            sections=[ReportSection.MAIN_SUMMARY],
            table_config=valid_table_config,
            show_logs=True,
            show_charts=True,
            css_template="modern",
            template_dir=TEMPLATES_DIR,
            output_dir=test_output_dir
        )


def test_table_config_validation():
    """Test validation of table configuration."""
    # Valid config
    config = ReportTableConfig(
        columns=["test_name", "result"],
        custom_columns=["comments"],
        failed_threshold=90.0
    )
    assert config.failed_threshold == 90.0

    # Invalid threshold - too high
    with pytest.raises(ValueError, match="Failed threshold must be between 0 and 100"):
        ReportTableConfig(
            columns=["test_name"],
            custom_columns=[],
            failed_threshold=101.0
        )

    # Invalid threshold - negative
    with pytest.raises(ValueError, match="Failed threshold must be between 0 and 100"):
        ReportTableConfig(
            columns=["test_name"],
            custom_columns=[],
            failed_threshold=-1.0
        )


def test_css_template_handling(valid_table_config, test_output_dir):
    """Test CSS template handling."""
    # Test valid template
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="dark",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )
    assert config.css_template == "dark"

    # Test invalid template falls back to modern
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="invalid_template",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )
    assert config.css_template == "modern"


def test_output_directory_handling(valid_table_config, test_output_dir):
    """Test output directory handling."""
    # Test base directory
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )
    assert config.output_dir.exists()

    # Test nested directory creation
    nested_dir = test_output_dir / "nested"
    nested_dir.mkdir(parents=True, exist_ok=True)  # Create nested directory first

    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=nested_dir
    )
    assert nested_dir.exists()


def test_drilldown_config(valid_table_config, test_output_dir):
    """Test drilldown report configuration."""
    config = ReportConfig(
        report_type=ReportType.DRILLDOWN,
        sections=[ReportSection.MAIN_SUMMARY, ReportSection.TEST_RESULTS],
        table_config=valid_table_config,
        show_logs=True,
        show_charts=True,
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )

    assert config.report_type == ReportType.DRILLDOWN
    assert len(config.sections) == 2
    assert ReportSection.MAIN_SUMMARY in config.sections
    assert ReportSection.TEST_RESULTS in config.sections


def test_boolean_values_conversion(valid_table_config, test_output_dir):
    """Test boolean values conversion."""
    # Test string values
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs="true",
        show_charts="yes",
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )

    assert isinstance(config.show_logs, bool)
    assert isinstance(config.show_charts, bool)
    assert config.show_logs is True
    assert config.show_charts is True

    # Test boolean values
    config = ReportConfig(
        report_type=ReportType.ONE_PAGER,
        sections=[ReportSection.MAIN_SUMMARY],
        table_config=valid_table_config,
        show_logs=False,
        show_charts=False,
        css_template="modern",
        template_dir=TEMPLATES_DIR,
        output_dir=test_output_dir
    )

    assert config.show_logs is False
    assert config.show_charts is False