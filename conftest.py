import shutil
from pathlib import Path

import pytest

from core.logger import Log
from core.plugins.test_case_plugin import TestCasePlugin

ROOT_DIR = Path(__file__).parent
CONFIG_DIR = ROOT_DIR / 'config'
LOG_DIR = ROOT_DIR / 'logs'
LOGGER_CONFIG_PATH = CONFIG_DIR / 'logger.ini'


def clean_logs_directory():
    """
    Clean logs directory by removing all files and recreating the directory.

    """
    if LOG_DIR.exists():
        Log.info(f"Cleaning logs directory: {LOG_DIR}")
        shutil.rmtree(LOG_DIR)
        Log.info("Previous logs directory removed")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    Log.info("Fresh logs directory created")


def pytest_configure(config):
    """
    Configure pytest environment and logger setup.
        1. Clean logs directory
        2. Register plugins

    @param config: pytest.Config - Pytest configuration object
    """

    # Clean logs directory before test run
    clean_logs_directory()

    # Register plugins
    config.pluginmanager.register(TestCasePlugin())


@pytest.fixture(autouse=True)
def reset_step_counter():
    """
    Fixture to reset step counter before each test.

    @returns None - Yields control back to the test after setup
    """
    Log.reset_step_counter()
    yield
