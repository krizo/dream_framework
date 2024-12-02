"""Test run configuration parser module."""
from core.configuration.config_parser import ConfigParser


class TestRunConfig(ConfigParser):
    """Parser for test run configuration settings."""

    SECTION_NAME = "TEST_RUN"

    @classmethod
    def get_app_under_test(cls) -> str:
        """
        Get application under test name.

        @return: Application name
        """
        return cls.get_value('app_under_test', 'example_app')

    @classmethod
    def get_app_version(cls) -> str:
        """
        Get application version.

        @return: Application version
        """
        return cls.get_value('app_version', '1.0.0')

    @classmethod
    def get_test_owner(cls) -> str:
        """
        Get default test owner.

        @return: Test owner name
        """
        return cls.get_value('test_owner', 'default_user')