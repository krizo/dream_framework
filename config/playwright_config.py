from pathlib import Path
from typing import Dict, Any, Optional

from core.configuration.config_parser import ConfigParser
from core.frontend.playwright.browser_types import BrowserType
from core.logger import Log


class PlaywrightConfig(ConfigParser):
    """Configuration parser for Playwright settings."""

    SECTION_NAME = "PLAYWRIGHT"

    @classmethod
    def get_browser_type(cls) -> BrowserType:
        """
        Get configured browser type.

        @return: BrowserType enum value
        """
        browser_type = cls.get_value('browser_type', 'chromium')
        try:
            return BrowserType(browser_type.lower())
        except ValueError:
            Log.warning(f"Invalid browser type {browser_type}, using chromium")
            return BrowserType.CHROMIUM

    @classmethod
    def get_headless(cls) -> bool:
        """
        Get headless mode setting.

        @return: True if browser should run in headless mode, False otherwise
        """
        return cls.get_value('headless', False)

    @classmethod
    def get_window_size(cls) -> str:
        """
        Get window size setting.

        @return: Window size configuration value ('maximized' or 'custom')
        """
        return cls.get_value('window_size', 'maximized')

    @classmethod
    def get_viewport_size(cls) -> Dict[str, int]:
        """
        Get viewport size configuration.

        @return: Dictionary with width and height values
        """
        window_size = cls.get_value('window_size', 'maximized')

        # Handle numeric dimensions (width,height format)
        if isinstance(window_size, str) and ',' in window_size:
            try:
                width, height = window_size.split(',')
                return {
                    'width': int(width.strip()),
                    'height': int(height.strip())
                }
            except (ValueError, TypeError):
                Log.warning(f"Invalid window_size format: {window_size}, using default")

        # Handle 'maximized' keyword
        if window_size == 'maximized':
            return {'width': 1920, 'height': 1080}

        # Handle custom dimensions from separate config values
        width = cls.get_value('viewport_width', 1280)
        height = cls.get_value('viewport_height', 720)
        return {'width': width, 'height': height}

    @classmethod
    def get_slow_mo(cls) -> int:
        """
        Get slow motion delay in milliseconds.

        @return: Delay in milliseconds
        """
        return cls.get_value('slow_mo', 0)

    @classmethod
    def get_timeout(cls) -> int:
        """
        Get default timeout in milliseconds.

        @return: Timeout in milliseconds
        """
        return cls.get_value('timeout', 30000)

    @classmethod
    def get_screenshots_dir(cls) -> Path:
        """
        Get screenshots directory path.

        @return: Path to screenshots directory
        """
        from core.common_paths import LOG_DIR
        screenshots_dir = cls.get_value('screenshots_dir', str(LOG_DIR / 'screenshots'))
        path = Path(screenshots_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_videos_dir(cls) -> Path:
        """
        Get videos directory path.

        @return: Path to videos directory
        """
        from core.common_paths import LOG_DIR
        videos_dir = cls.get_value('videos_dir', str(LOG_DIR / 'videos'))
        path = Path(videos_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_traces_dir(cls) -> Path:
        """
        Get traces directory path.

        @return: Path to traces directory
        """
        from core.common_paths import LOG_DIR
        traces_dir = cls.get_value('traces_dir', str(LOG_DIR / 'traces'))
        path = Path(traces_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def record_video(cls) -> bool:
        """
        Check if videos should be recorded.

        @return: True if videos should be recorded, False otherwise
        """
        return cls.get_value('record_video', False)

    @classmethod
    def record_trace(cls) -> bool:
        """
        Check if traces should be recorded.

        @return: True if traces should be recorded, False otherwise
        """
        return cls.get_value('record_trace', False)

    @classmethod
    def get_browser_args(cls) -> Dict[str, Any]:
        """
        Get browser launch arguments.

        @return: Dictionary with browser launch arguments
        """
        args = {
            'headless': cls.get_headless(),
            'slow_mo': cls.get_slow_mo(),
        }

        if cls.get_value('ignore_https_errors', False):
            args['ignore_https_errors'] = True

        return args