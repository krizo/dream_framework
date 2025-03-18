"""Module for managing test run lifecycle and state."""
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Type

from core.configuration.framework_config import FrameworkConfig
from core.configuration.test_run_config import TestRunConfig
from core.logger import Log


class TestRunType(Enum):
    """Type of test run."""
    CI = "ci"
    SINGLE = "single"
    XDIST = 'xdist'


class TestRunStatus(Enum):
    """Status of test run."""
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class TestRun:
    """Class representing a test run."""
    _instance: Optional['TestRun'] = None

    def __init__(self, owner: Optional[str] = None, environment: Optional[str] = None,
                 worker_id: str = 'master', test_run_id: Optional[str] = None, test_type: Optional[TestRunType] = None,
                 **kwargs):
        """
        Initialize test run instance.

        @param owner: Username or system running tests
        @param environment: Test environment name
        @param worker_id: ID of test worker (for distributed testing)
        @param test_run_id: Optional predefined test run ID (for xdist)
        @param kwargs: Additional properties to store
        """
        if self._instance is not None:
            raise RuntimeError("TestRun instance already exists")

        self.test_run_id = test_run_id
        self.test_type = test_type or self._detect_test_type()
        self.status = TestRunStatus.STARTED
        self.owner = owner or FrameworkConfig.get_test_owner()
        self.environment = environment or FrameworkConfig.get_test_environment()
        self.worker_id = worker_id
        self.start_time = datetime.now()
        self.end_time = None
        self.duration = None
        self.report = None

        # Additional properties
        self.branch = kwargs.get('branch', self._get_git_branch())
        self.app_under_test = kwargs.get('app_under_test', self._get_app_under_test())
        self.app_version = kwargs.get('app_version', self._get_app_version())
        self.build_id = self._get_build_id()  # Always check env vars for build ID

        from conftest import LOG_DIR
        self._log_dir = LOG_DIR

    @classmethod
    def initialize(cls, **kwargs) -> 'TestRun':
        """
        Initialize TestRun singleton instance.

        @param kwargs: Arguments for TestRun initialization
        @return: TestRun instance
        @raises RuntimeError: If TestRun already initialized
        """
        # Return existing instance if available
        if cls._instance is not None:
            Log.info(f"Using existing TestRun instance: {cls._instance.test_run_id}")
            return cls._instance

        worker_id = kwargs.get('worker_id', 'master')

        # Handle xdist mode
        if 'PYTEST_XDIST_ACTIVE' in os.environ:
            if worker_id == 'master':
                test_run_id = f"local_xdist_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                os.environ['XDIST_TEST_RUN_ID'] = test_run_id
                kwargs['test_type'] = TestRunType.XDIST
            else:
                test_run_id = os.environ.get('XDIST_TEST_RUN_ID')
                if not test_run_id:
                    raise RuntimeError("Missing test run ID in xdist worker")
                kwargs['test_run_id'] = test_run_id
                kwargs['test_type'] = TestRunType.XDIST

        instance = cls(**kwargs)
        cls._instance = instance
        Log.info(f"TestRun initialized: {instance.test_run_id}")
        return instance

    @classmethod
    def get_instance(cls) -> Optional['TestRun']:
        """
        Get current TestRun instance if exists.

        @return: Current TestRun instance or None
        """
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset TestRun singleton state."""
        if cls._instance:
            Log.info(f"Process {os.getpid()}: Resetting TestRun")
            cls._instance = None

    @classmethod
    def get_model(cls) -> Type['TestRunModel']:
        """Get TestRunModel class."""
        from models.test_run_model import TestRunModel
        return TestRunModel

    def _generate_run_id(self) -> str:
        """Generate unique run identifier."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        env_prefix = 'ci' if self._is_ci() else 'local'
        run_type = 'xdist' if 'PYTEST_XDIST_ACTIVE' in os.environ else 'single'
        return f"{env_prefix}_{run_type}_{timestamp}"

    def _detect_test_type(self) -> TestRunType:
        """Detect type of test run."""
        if self._is_ci():
            return TestRunType.CI
        return TestRunType.XDIST if 'PYTEST_XDIST_ACTIVE' in os.environ else TestRunType.SINGLE

    def _is_ci(self) -> bool:
        """Check if running in CI environment."""
        ci_vars = ['BUILD_NUMBER', 'CI_BUILD_ID', 'BUILD_ID']
        return any(var in os.environ for var in ci_vars)

    @staticmethod
    def _get_build_id() -> Optional[str]:
        """Get CI build ID if available."""
        for var in ['BUILD_NUMBER', 'CI_BUILD_ID', 'BUILD_ID']:
            if var in os.environ:
                return os.environ[var]
        return None

    @staticmethod
    def _get_git_branch() -> Optional[str]:
        """Get current git branch."""
        try:
            import git
            repo = git.Repo(search_parent_directories=True)
            return repo.active_branch.name
        except Exception:
            return None

    @staticmethod
    def _get_app_under_test() -> str:
        """Get name of application under test."""
        return TestRunConfig.get_app_under_test()

    @staticmethod
    def _get_app_version() -> str:
        """Get version of application under test."""
        return TestRunConfig.get_app_version()

    def get_log_dir(self) -> Path:
        """Get path to log directory for this run."""
        return self._log_dir

    def complete(self) -> None:
        """Mark test run as completed."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = TestRunStatus.COMPLETED
        Log.info(f"Test run {self.test_run_id} completed in {self.duration:.2f}s")

    def cancel(self) -> None:
        """Mark test run as cancelled."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = TestRunStatus.CANCELLED
        Log.info(f"Test run {self.test_run_id} cancelled")

    def to_model(self) -> 'TestRunModel':
        """Convert to database model."""
        from models.test_run_model import TestRunModel

        return TestRunModel(
            test_run_id=self.test_run_id,
            test_type=self.test_type.value,
            status=self.status.value,
            owner=self.owner,
            environment=self.environment,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            report=self.report,
            branch=self.branch,
            app_under_test=self.app_under_test,
            app_version=self.app_version,
            build_id=self.build_id
        )

    def get_metadata(self) -> Dict[str, Any]:
        """Get test run metadata."""
        return {
            'test_run_id': self.test_run_id,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'owner': self.owner,
            'environment': self.environment,
            'worker_id': self.worker_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'branch': self.branch,
            'app_under_test': self.app_under_test,
            'app_version': self.app_version,
            'build_id': self.build_id
        }
