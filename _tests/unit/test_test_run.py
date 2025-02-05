from unittest.mock import patch, MagicMock

import pytest

from core.test_run import TestRun, TestRunStatus

pytestmark = pytest.mark.no_database_plugin


def test_singleton_initialization():
    """Test singleton initialization and access."""
    TestRun.reset()  # Ensure clean state

    # First initialization should work
    test_run1 = TestRun.initialize(owner="test_user")
    assert test_run1 is not None
    assert test_run1.owner == "test_user"


    # get_instance should return same instance
    test_run2 = TestRun.get_instance()
    assert test_run2 is test_run1

    # Direct instantiation should fail
    with pytest.raises(RuntimeError) as exc_info:
        TestRun(owner="direct_user")
    assert "TestRun instance already exists" in str(exc_info.value)

    # Reset should clear instance
    TestRun.reset()
    assert TestRun.get_instance() is None

    # After reset, should be able to initialize again
    test_run3 = TestRun.initialize(owner="new_user")
    assert test_run3 is not None
    assert test_run3 is not test_run1


def test_singleton_persistence():
    """Test singleton persistence across multiple accesses."""
    TestRun.reset()

    # Initialize with specific values
    test_run = TestRun.initialize(
        owner="test_user",
        environment="staging",
    )

    # Get instance multiple times and verify values persist
    for _ in range(3):
        instance = TestRun.get_instance()
        assert instance is test_run
        assert instance.owner == "test_user"
        assert instance.environment == "staging"


@pytest.mark.parametrize("instance_exists", [True, False])
def test_get_instance_behavior(instance_exists):
    """Test get_instance behavior with and without existing instance."""
    TestRun.reset()

    if instance_exists:
        original = TestRun.initialize(owner="test_user")
        instance = TestRun.get_instance()
        assert instance is original
        assert instance.owner == "test_user"
    else:
        instance = TestRun.get_instance()
        assert instance is None


def test_reset_cleanup():
    """Test that reset properly cleans up the instance."""
    TestRun.reset()

    # Create and modify instance
    test_run = TestRun.initialize(owner="test_user")
    test_run.complete()  # Change state

    # Reset and verify cleanup
    TestRun.reset()
    assert TestRun.get_instance() is None

    # Should be able to create new instance with different state
    new_run = TestRun.initialize(owner="new_user")
    assert new_run.owner == "new_user"
    assert new_run.status == TestRunStatus.STARTED  # Fresh state


def test_initialization_with_partial_args():
    """Test initialization with partial arguments and fallbacks."""
    TestRun.reset()

    with patch('core.configuration.test_run_config.TestRunConfig') as mock_config, \
            patch('git.Repo') as mock_repo:

        # Setup mocks
        mock_config.get_app_under_test.return_value = "example_app"
        mock_config.get_app_version.return_value = "1.0.0"
        mock_branch = MagicMock()
        mock_branch.name = 'default-branch'
        mock_repo.return_value.active_branch = mock_branch

        try:
            # Initialize with partial arguments
            test_run = TestRun.initialize(owner="test_user")

            # Verify provided values
            assert test_run.owner == "test_user"

            # Verify fallback values
            assert test_run.app_under_test == "example_app"
            assert test_run.app_version == "1.0.0"
            assert test_run.branch == "default-branch"

        except Exception as e:
            pytest.fail(f"Test failed with exception: {str(e)}")
