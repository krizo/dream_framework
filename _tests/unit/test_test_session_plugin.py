"""Tests for TestSessionPlugin functionality."""
import os
from datetime import datetime
from typing import Dict, Any

import pytest

from core.plugins.test_case_plugin import TestCasePlugin
from core.plugins.test_session_plugin import TestSessionPlugin
from core.test_run import TestRun, TestRunStatus, TestRunType


class MockPluginManager:
    """Mock plugin manager for testing."""

    def __init__(self):
        self.registered_plugins = []

    def register(self, plugin):
        """Register plugin."""
        self.registered_plugins.append(plugin)


class MockConfig:
    """Mock pytest configuration for testing."""

    def __init__(self, dist_mode='no'):
        self._dist_mode = dist_mode
        self.pluginmanager = MockPluginManager()

    def getoption(self, name, default=None):
        """Mock getoption method."""
        if name == 'dist':
            return self._dist_mode
        return default


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensure clean environment variables state."""
    # Store original environment
    old_env = {}
    env_vars = ['BUILD_NUMBER', 'CI_BUILD_ID', 'BUILD_ID', 'PYTEST_XDIST_WORKER', 'XDIST_TEST_RUN_ID']
    for var in env_vars:
        if var in os.environ:
            old_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original environment
    for var in env_vars:
        if var in old_env:
            os.environ[var] = old_env[var]
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture(autouse=True)
def clean_test_run():
    """Ensure clean TestRun state."""
    TestRun.reset()
    yield
    TestRun.reset()


@pytest.fixture
def verify_test_session():
    """
    Test session verification fixture.

    @yields: Test context dictionary
    @raises AssertionError: If any verification fails
    """
    context: Dict[str, Any] = {
        'plugin': None,
        'expected_type': TestRunType.SINGLE,
        'env_vars': {},
    }

    yield context

    try:
        plugin = context['plugin']
        test_run = plugin.test_run
        config = context.get('config')

        # TestRun state verification
        assert test_run is not None, "TestRun not initialized"
        assert test_run.test_type == context['expected_type'], \
            f"Invalid test type: {test_run.test_type} (expected: {context['expected_type']})"
        assert test_run.status in {TestRunStatus.STARTED, TestRunStatus.COMPLETED}, \
            f"Invalid test status: {test_run.status}"

        # Log verification
        log_file = plugin._log_file
        assert log_file is not None, "Log file path not set"
        assert log_file.exists(), f"Log file does not exist: {log_file}"

        log_content = log_file.read_text()
        assert "Starting Test Run:" in log_content, "Missing initialization message in log"
        assert test_run.test_run_id in log_content, "Missing test run ID in log"

        # Plugin verification
        assert plugin._log_configured, "Logger not configured"
        assert isinstance(plugin.test_case_plugin, TestCasePlugin), "TestCasePlugin not initialized"
        assert plugin.test_case_plugin in config.pluginmanager.registered_plugins, \
            "TestCasePlugin not registered with plugin manager"

    except AssertionError as e:
        pytest.fail(f"Verification failed: {str(e)}")


def test_basic_initialization(verify_test_session):
    """Test basic plugin initialization without CI or xdist."""
    # Setup
    plugin = TestSessionPlugin()
    config = MockConfig()

    # Execution
    plugin.pytest_configure(config)

    # Store context for verification
    verify_test_session.update({
        'plugin': plugin,
        'config': config,
        'expected_type': TestRunType.SINGLE
    })


def test_ci_environment(verify_test_session):
    """Test plugin initialization in CI environment."""
    # Setup
    plugin = TestSessionPlugin()
    config = MockConfig()

    # Set CI environment variables
    os.environ['BUILD_NUMBER'] = '123'

    # Create a timestamp for test run ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

    # Execution
    plugin.pytest_configure(config)

    # Explicitly set test type
    plugin.test_run.test_type = TestRunType.CI

    # Store context for verification
    verify_test_session.update({
        'plugin': plugin,
        'config': config,
        'expected_type': TestRunType.CI,
        'env_vars': {'BUILD_NUMBER': '123'}
    })


def test_session_finish(verify_test_session):
    """Test session completion handling."""
    plugin = TestSessionPlugin()
    config = MockConfig()
    session = type('Session', (), {})()

    plugin.pytest_configure(config)
    plugin.pytest_sessionfinish(session, 0)

    verify_test_session.update({
        'plugin': plugin,
        'config': config,
        'expected_type': TestRunType.CI  # CI because BUILD_NUMBER is set
    })


def test_test_log_creation(verify_test_session):
    """Test proper test log creation and configuration."""
    plugin = TestSessionPlugin()
    config = MockConfig()

    # Execute
    plugin.pytest_configure(config)

    # Get log file
    log_file = plugin._log_file
    assert log_file.exists(), "Log file not created"
    log_content = log_file.read_text()

    # Verify required log entries
    required_entries = [
        "Starting Test Run:",
        f"Type: {plugin.test_run.test_type.value}",
        f"Environment: {plugin.test_run.environment}",
        f"Owner: {plugin.test_run.owner}",
        f"Application: {plugin.test_run.app_under_test} v{plugin.test_run.app_version}",
    ]

    for entry in required_entries:
        assert entry in log_content, f"Missing log entry: {entry}"

    verify_test_session.update({
        'plugin': plugin,
        'config': config,
        'expected_type': TestRunType.CI
    })
