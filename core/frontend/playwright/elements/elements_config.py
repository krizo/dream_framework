from core.configuration.config_parser import ConfigParser


class UIElementConfig(ConfigParser):
    """Configuration for UI elements."""

    SECTION_NAME = "PLAYWRIGHT"

    @classmethod
    def get_default_timeout(cls) -> int:
        """
        Get default timeout for element wait operations.

        @return: Timeout in seconds
        """
        return cls.get_value('timeout', 10)

    @classmethod
    def get_retry_interval(cls) -> float:
        """
        Get retry interval for element wait operations.

        @return: Interval in seconds
        """
        return cls.get_value('retry_interval', 0.5)

    @classmethod
    def get_strict_matching(cls) -> bool:
        """
        Check if strict tag matching is enabled.

        @return: True if strict tag matching is enabled
        """
        return bool(cls.get_value('strict_tag_matching', False))