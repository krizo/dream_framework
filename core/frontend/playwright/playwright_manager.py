from typing import Optional, Dict, Any, List

from playwright.sync_api import Playwright, Browser, BrowserContext, Page, BrowserType, sync_playwright

from config.playwright_config import PlaywrightConfig
from core.logger import Log


class PlaywrightManager:
    """
    Class for managing Playwright browser instances.
    Implements singleton pattern to ensure single browser instance.
    """

    _instance: Optional['PlaywrightManager'] = None
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None

    def __new__(cls, *args, **kwargs):
        """
        Create singleton instance or return existing one.

        @return: PlaywrightManager instance
        """
        if cls._instance is None:
            cls._instance = super(PlaywrightManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, browser_type: Optional[BrowserType] = None, **kwargs):
        """
        Initialize PlaywrightManager with browser type and options.

        @param browser_type: Type of browser to initialize
        @param kwargs: Additional browser launch arguments
        """
        # Skip initialization if already initialized
        if getattr(self, '_initialized', False):
            return

        self.config = PlaywrightConfig()
        self._browser_type = browser_type or self.config.get_browser_type()
        self._browser_args = self.config.get_browser_args()

        # Override with any provided kwargs
        self._browser_args.update(kwargs)

        # Record directories
        self._screenshots_dir = self.config.get_screenshots_dir()
        self._videos_dir = self.config.get_videos_dir()
        self._traces_dir = self.config.get_traces_dir()

        # Initialize Playwright
        self._start_playwright()
        self._initialized = True
        self._active_pages = []

    @classmethod
    def initialize(cls, browser_type: Optional[BrowserType] = None, **kwargs) -> 'PlaywrightManager':
        """
        Initialize PlaywrightManager as a singleton.

        @param browser_type: Type of browser to initialize
        @param kwargs: Additional browser launch arguments
        @return: PlaywrightManager instance
        """
        if cls._instance is None:
            return cls(browser_type, **kwargs)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Optional['PlaywrightManager']:
        """
        Get current instance if it exists.

        @return: PlaywrightManager instance or None
        """
        return cls._instance

    def get_page(self) -> Page:
        """
        Get current page or create a new one if needed.

        @return: Playwright Page instance
        """
        if not self._page:
            if self._context:
                self._page = self._context.new_page()
                self._active_pages.append(self._page)
                self._page.set_default_timeout(self.config.get_timeout())

        # Return the last page (most likely the active one)
        if self._active_pages:
            self._page = self._active_pages[-1]

        return self._page

    def get_all_pages(self) -> List[Page]:
        """
        Get all open pages.

        @return: List of all open Page instances
        """
        return self._active_pages

    def get_page_by_url(self, url_pattern: str) -> Optional[Page]:
        """
        Find page by URL pattern.

        @param url_pattern: URL pattern to match
        @return: Page instance or None if not found
        """
        import re
        pattern = re.compile(url_pattern)

        for page in self._active_pages:
            if pattern.search(page.url):
                return page

        return None

    def _parse_window_size(self) -> Dict[str, int]:
        """
        Parse window size from config.

        @return: Dictionary with width and height values
        """
        window_size = self.config.get_value('window_size', 'maximized')

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

        # Handle 'maximized' keyword - use large default size
        if window_size == 'maximized':
            return {'width': 1920, 'height': 1080}

        # Handle custom dimensions from separate config values
        width = self.config.get_value('viewport_width', 1280)
        height = self.config.get_value('viewport_height', 720)
        return {'width': width, 'height': height}

    def _start_playwright(self) -> None:
        """
        Start Playwright and browser.
        """
        try:
            self._playwright = sync_playwright().start()

            # Launch browser based on type
            browser_launcher = getattr(self._playwright, self._browser_type.value)

            # Get window dimensions
            viewport = self._parse_window_size()

            # Launch browser with default args
            self._browser = browser_launcher.launch(**self._browser_args)

            # Create context with viewport and recording options
            context_options = {
                'viewport': viewport,
                'record_video_dir': str(self._videos_dir) if self.config.record_video() else None,
            }

            self._context = self._browser.new_context(**context_options)

            # Start tracing if configured
            if self.config.record_trace():
                self._context.tracing.start(screenshots=True, snapshots=True)

            # Create initial page
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.config.get_timeout() * 1000)
            self._context.on("page", self._handle_new_page)

        except Exception as e:
            self.close()
            raise

    def _handle_new_page(self, page: Page) -> None:
        """
        Handle a new page or tab opened by the application.

        @param page: New page instance
        """
        self._active_pages.append(page)
        self._page = page

    def new_page(self) -> Page:
        """
        Create a new page.

        @return: New Playwright Page instance
        """
        if self._context is None:
            self._start_playwright()

        page = self._context.new_page()
        page.set_default_timeout(self.config.get_timeout() * 1000)
        return page

    def take_screenshot(self, name: str, page: Optional[Page] = None, full_page: bool = True) -> str:
        """
        Take a screenshot of the current page.

        @param name: Name for the screenshot (without extension)
        @param page: Page to take screenshot of (or current page if None)
        @param full_page: Whether to take a screenshot of the full page or just the viewport
        @return: Path to the screenshot file
        """
        try:
            target_page = page or self.get_page()
            if target_page is None:
                Log.warning("No page available for screenshot")
                return ""

            screenshot_path = self._screenshots_dir / f"{name}_{self._get_timestamp()}.png"
            target_page.screenshot(path=screenshot_path, full_page=full_page)
            Log.info(f"Screenshot saved to {screenshot_path}")
            return str(screenshot_path)

        except Exception as e:
            Log.error(f"Failed to take screenshot: {str(e)}")
            return ""

    def clear_cookies(self, page: Optional[Page] = None) -> None:
        """
        Clear cookies for the current context.

        @param page: Page instance (not used, kept for API compatibility)
        """
        if self._context is not None:
            self._context.clear_cookies()
            Log.info("Cookies cleared")

    def save_trace(self, path: Optional[str] = None) -> None:
        """
        Save trace if tracing is enabled.

        @param path: Path to save trace (optional, uses default if None)
        """
        if self._context is not None and self.config.record_trace():
            trace_path = path or str(self._traces_dir / f"trace_{self._get_timestamp()}.zip")
            self._context.tracing.stop(path=trace_path)
            Log.info(f"Trace saved to {trace_path}")

    def close(self) -> None:
        """
        Close browser and Playwright.
        """
        try:
            # Save trace before closing
            self.save_trace()

            # Close page, context, browser, and playwright in order
            if self._page is not None:
                self._page.close()
                self._page = None

            if self._context is not None:
                self._context.close()
                self._context = None

            if self._browser is not None:
                self._browser.close()
                self._browser = None

            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

            Log.info("Playwright resources closed successfully")

        except Exception as e:
            Log.error(f"Error closing Playwright resources: {str(e)}")

        finally:
            # Clear singleton instance
            PlaywrightManager._instance = None

    @staticmethod
    def _get_timestamp() -> str:
        """
        Get current timestamp in string format.

        @return: Timestamp string
        """
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
