"""Framework configuration parser module."""
from core.configuration.config_parser import ConfigParser


class FrameworkConfig(ConfigParser):
    """Parser for framework general settings."""

    SECTION_NAME = "FRAMEWORK"

    @classmethod
    def should_drop_database(cls) -> bool:
        """
        Check if database should be dropped during initialization.

        @return: True if database should be dropped, False otherwise
        """
        return cls.get_value('drop_database', False)

    @classmethod
    def get_test_owner(cls) -> str:
        """
        Get default test owner.

        @return: Test owner name
        """
        return cls.get_value('test_owner', 'default_user')

    @classmethod
    def get_test_environment(cls) -> str:
        """
        Get default test environment.

        @return: Test environment name
        """
        return cls.get_value('environment', 'local')
