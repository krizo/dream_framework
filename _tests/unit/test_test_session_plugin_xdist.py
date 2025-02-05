"""Tests for TestSessionPlugin functionality."""
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

from core.plugins.test_session_plugin import TestSessionPlugin
from core.test_run import TestRun, TestRunStatus, TestRunType
from models.test_run_model import TestRunModel


def test_xdist_handling(tmp_path):
    """Test handling of pytest-xdist configuration."""
    TestRun.reset()
    plugin = TestSessionPlugin()
    config = MagicMock()
    config.getoption.return_value = 'each'
    test_run_id = f"test_run_xdist_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # Przygotowanie modelu z właściwym typem
    test_run_model = TestRunModel(
        test_run_id=test_run_id,
        test_type=TestRunType.XDIST.value,
        status=TestRunStatus.STARTED.value,
        owner="test_user",
        environment="test",
        start_time=datetime.now()
    )

    # Konfiguracja mocków
    mock_db = MagicMock()
    session_mock = MagicMock()
    session_mock.query().filter_by().first.return_value = test_run_model
    mock_db.session_scope.return_value.__enter__.return_value = session_mock

    test_run_mock = MagicMock()
    test_run_mock.test_type = TestRunType.XDIST
    test_run_mock.test_run_id = test_run_id
    test_run_mock.worker_id = 'gw1'
    test_run_mock.get_log_dir.return_value = tmp_path
    test_run_mock.to_model.return_value = test_run_model

    with patch('core.automation_database_manager.AutomationDatabaseManager.get_database', return_value=mock_db), \
         patch('core.test_run.TestRun.initialize', return_value=test_run_mock), \
         patch('conftest.LOG_DIR', tmp_path), \
         patch.dict('os.environ', {
             'PYTEST_XDIST_WORKER': 'gw1',
             'XDIST_TEST_RUN_ID': test_run_id
         }, clear=True):

        plugin.pytest_configure(config)

        assert plugin._is_xdist
        assert plugin.test_run.worker_id == 'gw1'
        assert os.environ['XDIST_TEST_RUN_ID'] == test_run_id