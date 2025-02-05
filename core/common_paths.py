"""Common path configuration module."""
from pathlib import Path

# Root paths
ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / 'config'
LOG_DIR = ROOT_DIR / 'logs'
REPORTS_DIR = LOG_DIR / 'reports'
TEMPLATES_DIR = ROOT_DIR / 'reports' / 'templates'
LOGGER_CONFIG_PATH = CONFIG_DIR / 'logger.ini'

# Create required directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
