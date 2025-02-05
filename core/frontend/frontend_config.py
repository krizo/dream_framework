"""Frontend configuration parser module."""
from typing import Dict, Any

from core.configuration.config_parser import ConfigParser


class FrontendConfig(ConfigParser):
    """Parser for frontend configuration settings."""

    SECTION_NAME = "FRONTEND"

    @classmethod
    def get_browser_path(cls) -> str:
        """Get browser executable path."""
        return cls.get_value('browser_path')

    @classmethod
    def get_chromedriver_path(cls) -> str:
        """Get chromedriver path."""
        return cls.get_value('chromedriver_path')

    @classmethod
    def get_window_config(cls) -> Dict[str, Any]:
        """Get window configuration."""
        return {
            'size': cls.get_value('window_size', 'maximized'),
            'width': cls.get_value('window_width', 1920),
            'height': cls.get_value('window_height', 1080)
        }

    @classmethod
    def get_browser_options(cls) -> Dict[str, bool]:
        """Get browser options."""
        return {
            'headless': cls.get_value('headless', False),
            'incognito': cls.get_value('incognito', True),
            'disable_infobars': cls.get_value('disable_infobars', True),
            'disable_notifications': cls.get_value('disable_notifications', True),
            'disable_extensions': cls.get_value('disable_extensions', True),
            'disable_gpu': cls.get_value('disable_gpu', True),
            'accept_insecure_certs': cls.get_value('accept_insecure_certs', True)
        }

    @classmethod
    def get_timeouts(cls) -> Dict[str, int]:
        """Get timeout settings."""
        return {
            'page_load': cls.get_value('page_load_timeout', 30),
            'implicit_wait': cls.get_value('implicit_wait', 10),
            'explicit_wait': cls.get_value('explicit_wait', 20)
        }

    @classmethod
    def get_screenshot_config(cls) -> Dict[str, Any]:
        """Get screenshot configuration."""
        return {
            'on_failure': cls.get_value('take_screenshot_on_failure', True),
            'dir': cls.get_value('screenshots_dir', 'screenshots')
        }