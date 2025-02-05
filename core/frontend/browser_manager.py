"""Module for managing browser instances."""
from enum import Enum
from typing import Optional, Dict, Any
import time

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from core.frontend.frontend_config import FrontendConfig
from core.logger import Log


class BrowserType(Enum):
    """Supported browser types."""
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


class BrowserManager:
    """
    Singleton class for managing browser instances.
    Handles browser initialization and reuse between tests.
    """
    _instance: Optional['BrowserManager'] = None
    _driver: Optional[WebDriver] = None
    _current_browser: Optional[BrowserType] = None

    def __init__(self):
        """Initialize browser manager."""
        if BrowserManager._instance is not None:
            raise RuntimeError("BrowserManager is a singleton")
        BrowserManager._instance = self

    @classmethod
    def initialize(cls, browser_type: BrowserType = BrowserType.CHROME) -> 'BrowserManager':
        """
        Initialize browser manager with specified browser type.

        @param browser_type: Type of browser to initialize
        @return: BrowserManager instance
        """
        if cls._instance is None:
            cls._instance = cls()

        if cls._driver is not None and cls._current_browser == browser_type:
            return cls._instance

        cls._create_driver(browser_type)
        return cls._instance

    @classmethod
    def get_driver(cls) -> WebDriver:
        """
        Get current WebDriver instance.

        @return: WebDriver instance
        @raises RuntimeError: If browser not initialized
        """
        if cls._driver is None:
            raise RuntimeError("Browser not initialized")
        return cls._driver

    @classmethod
    def _setup_chrome_options(cls) -> webdriver.ChromeOptions:
        """Setup Chrome options from configuration."""
        options = webdriver.ChromeOptions()
        browser_options = FrontendConfig.get_browser_options()

        if browser_options['headless']:
            options.add_argument('--headless=new')
        if browser_options['incognito']:
            options.add_argument('--incognito')
        if browser_options['disable_infobars']:
            options.add_argument('--disable-infobars')
        if browser_options['disable_notifications']:
            options.add_argument('--disable-notifications')
        if browser_options['disable_extensions']:
            options.add_argument('--disable-extensions')
        if browser_options['disable_gpu']:
            options.add_argument('--disable-gpu')

        # Set binary path if configured
        browser_path = FrontendConfig.get_browser_path()
        if browser_path:
            options.binary_location = browser_path

        return options

    @classmethod
    def _create_driver(cls, browser_type: BrowserType) -> None:
        """
        Create new WebDriver instance.
        """
        if cls._driver is not None:
            cls._quit_driver()

        Log.info(f"Initializing {browser_type.value} browser")

        try:
            if browser_type == BrowserType.CHROME:
                chromedriver_path = FrontendConfig.get_chromedriver_path()
                service = ChromeService(chromedriver_path if chromedriver_path else ChromeDriverManager().install())
                options = cls._setup_chrome_options()
                cls._driver = webdriver.Chrome(service=service, options=options)

                window_config = FrontendConfig.get_window_config()
                if not FrontendConfig.get_browser_options()['headless']:
                    if window_config['size'] == 'maximized':
                        cls._driver.maximize_window()
                    else:
                        cls._driver.set_window_size(
                            window_config['width'],
                            window_config['height']
                        )

                cls._configure_timeouts()
                cls._current_browser = browser_type
                Log.info("Browser initialized successfully")

        except Exception as e:
            Log.error(f"Failed to initialize browser: {str(e)}")
            raise

    @classmethod
    def _configure_timeouts(cls) -> None:
        """Configure browser timeouts from settings."""
        timeouts = FrontendConfig.get_timeouts()

        cls._driver.set_page_load_timeout(timeouts['page_load'])
        cls._driver.implicitly_wait(timeouts['implicit_wait'])

    @classmethod
    def _quit_driver(cls) -> None:
        """Quit current WebDriver instance."""
        if cls._driver is not None:
            try:
                cls._driver.quit()
            except:
                pass
            finally:
                cls._driver = None
                cls._current_browser = None

    @classmethod
    def close(cls) -> None:
        """Close browser and cleanup resources."""
        cls._quit_driver()
        cls._instance = None

    @classmethod
    def refresh(cls) -> None:
        """Refresh current browser window."""
        if cls._driver is not None:
            cls._driver.refresh()
            time.sleep(1)

    @classmethod
    def clear_cookies(cls) -> None:
        """Clear all browser cookies."""
        if cls._driver is not None:
            cls._driver.delete_all_cookies()

    @classmethod
    def get_screenshot(cls, name: str) -> None:
        """
        Take browser screenshot.

        @param name: Screenshot name
        """
        if cls._driver is not None:
            screenshot_config = FrontendConfig.get_screenshot_config()
            screenshot_dir = Path(screenshot_config['dir'])
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshot_dir / f"{name}.png"
            cls._driver.save_screenshot(str(screenshot_path))
            Log.info(f"Screenshot saved: {screenshot_path}")
