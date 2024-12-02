import shutil
from pathlib import Path

from _tests.fixtures import *
from core.logger import Log
from core.plugins.test_session_plugin import TestSessionPlugin

ROOT_DIR = Path(__file__).parent
CONFIG_DIR = ROOT_DIR / 'config'
LOG_DIR = ROOT_DIR / 'logs'
LOGGER_CONFIG_PATH = CONFIG_DIR / 'logger.ini'


def clean_logs_directory():
    """Clean logs directory by removing all files."""
    if LOG_DIR.exists():
        shutil.rmtree(LOG_DIR)

    LOG_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def reset_step_counter():
    """Reset step counter before each test."""
    Log.reset_step_counter()
    yield
    Log.reset_step_counter()


def pytest_configure(config):
    """Configure test session and plugins."""
    if not hasattr(config, 'workerinput'):  # Not running in worker
        clean_logs_directory()

    # Initialize plugins
    session_plugin = TestSessionPlugin()
    config.pluginmanager.register(session_plugin)


def pytest_runtest_setup(item):
    """Setup test execution."""
    if item.get_closest_marker('no_execution_record'):
        # Temporarily disable TestCasePlugin
        pluginmanager = item.config.pluginmanager
        test_case_plugin = next(
            (p for p in pluginmanager.get_plugins() if type(p).__name__ == 'TestCasePlugin'),
            None
        )
        if test_case_plugin:
            pluginmanager.unregister(test_case_plugin)
            item.user_properties.append(("disabled_plugin", test_case_plugin))


def pytest_runtest_teardown(item):
    """Restore test environment after test."""
    if item.get_closest_marker('no_execution_record'):
        # Re-enable TestCasePlugin if it was disabled
        disabled_plugin = next(
            (p[1] for p in item.user_properties if p[0] == "disabled_plugin"),
            None
        )
        if disabled_plugin:
            item.config.pluginmanager.register(disabled_plugin)


