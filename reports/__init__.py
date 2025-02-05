"""Reports module for test execution reporting."""
from pathlib import Path
from typing import Final

from core.common_paths import REPORTS_DIR

# Default output directory for reports
DEFAULT_OUTPUT_DIR: Final[Path] = REPORTS_DIR

__all__ = ['ReportGenerator', 'ReportConfig', 'ReportComponentFactory', 'DEFAULT_OUTPUT_DIR']

from .report_generator import ReportGenerator
from .report_config import ReportConfig
from .report_factory import ReportComponentFactory