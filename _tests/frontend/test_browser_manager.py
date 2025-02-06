"""Tests for browser manager functionality."""
import json
from enum import Enum

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from core.common_paths import LOG_DIR
from core.frontend.browser_manager import BrowserManager, BrowserType
from core.frontend.frontend_config import FrontendConfig


@pytest.fixture(autouse=True)
def cleanup_browser():
    """Cleanup browser after each test."""
    yield
    BrowserManager.close()


def test_browser_initialization():
    """Test basic browser initialization."""
    browser = BrowserManager.initialize()
    driver = browser.get_driver()

    assert driver is not None
    assert BrowserManager._current_browser == BrowserType.CHROME


def test_singleton_behavior():
    """Test BrowserManager singleton pattern."""
    browser1 = BrowserManager.initialize()
    browser2 = BrowserManager.initialize()

    assert browser1 is browser2
    assert browser1._driver is browser2._driver


def test_browser_reuse():
    """Test browser reuse between calls."""
    browser = BrowserManager.initialize()
    original_driver = browser.get_driver()

    # Second initialization should return same driver
    browser = BrowserManager.initialize()
    assert browser.get_driver() is original_driver


def test_browser_navigation():
    """Test basic browser navigation."""
    browser = BrowserManager.initialize()
    driver = browser.get_driver()

    test_url = "https://example.com/"
    driver.get(test_url)
    assert driver.current_url == test_url


def test_window_configuration():
    """Test window size configuration."""
    with patch.object(FrontendConfig, 'get_window_config') as mock_config:
        # Test maximized
        mock_config.return_value = {'size': 'maximized'}
        browser = BrowserManager.initialize()
        driver = browser.get_driver()

        size = driver.get_window_size()
        assert size['width'] > 0
        assert size['height'] > 0

        # Test custom size
        BrowserManager.close()
        mock_config.return_value = {
            'size': 'custom',
            'width': 1024,
            'height': 768
        }

        browser = BrowserManager.initialize()
        driver = browser.get_driver()

        size = driver.get_window_size()
        assert size['width'] == 1024
        assert size['height'] == 768


def test_cookie_management():
    """Test cookie management."""
    browser = BrowserManager.initialize()
    driver = browser.get_driver()

    # Set a cookie
    driver.get("https://example.com")
    driver.add_cookie({
        'name': 'test_cookie',
        'value': 'test_value'
    })

    # Verify cookie exists
    cookie = driver.get_cookie('test_cookie')
    assert cookie['value'] == 'test_value'

    # Clear cookies
    browser.clear_cookies()
    assert len(driver.get_cookies()) == 0


def test_screenshot_capture():
    """Test screenshot functionality."""
    screenshot_dir = Path("screenshots")
    screenshot_name = "test_screenshot"

    browser = BrowserManager.initialize()
    driver = browser.get_driver()

    driver.get("https://example.com")
    browser.get_screenshot(screenshot_name)

    screenshot_path = screenshot_dir / f"{screenshot_name}.png"
    assert screenshot_path.exists()
    screenshot_path.unlink()


def test_session_recording():
    """Test session recording functionality."""
    with patch.object(FrontendConfig, 'get_recording_config') as mock_config:
        recording_dir = LOG_DIR  / "recordings"
        if recording_dir.exists():
            # Cleanup before test
            for file in recording_dir.glob("*.har"):
                file.unlink()

        mock_config.return_value = {
            'enabled': True,
            'dir': str(recording_dir)
        }

        browser = BrowserManager.initialize()
        driver = browser.get_driver()

        # Perform some actions that will be recorded
        driver.get("https://example.com")
        driver.find_element(By.TAG_NAME, "body")

        # Close browser (should trigger recording save)
        BrowserManager.close()

        # Give some time for file to be written
        import time
        time.sleep(1)

        # Check if any .har files were created
        har_files = list(recording_dir.glob("*.har"))
        assert len(har_files) > 0, f"No HAR files found in {recording_dir}"

        # Verify content of HAR file
        with open(har_files[0]) as f:
            har_content = json.load(f)
            assert 'log' in har_content
            assert 'entries' in har_content['log']
            assert len(har_content['log']['entries']) > 0

        # Cleanup
        for file in har_files:
            file.unlink()


def test_browser_refresh():
    """Test browser refresh functionality."""
    browser = BrowserManager.initialize()
    driver = browser.get_driver()

    # Load page and modify content
    driver.get("https://example.com")
    original_title = driver.title
    driver.execute_script("document.title = 'Modified';")

    # Refresh and verify content is reset
    browser.refresh()
    assert driver.title == original_title


def test_error_handling():
    """Test error handling in browser operations."""
    # Test initialization with invalid browser type
    class InvalidBrowserType(Enum):
        INVALID = "invalid"

    with pytest.raises(ValueError, match="Invalid browser type"):
        BrowserManager.initialize(InvalidBrowserType.INVALID)

    # Test get_driver before initialization
    BrowserManager._instance = None
    BrowserManager._driver = None
    with pytest.raises(RuntimeError, match="Browser not initialized"):
        BrowserManager.get_driver()

    # Test invalid browser path
    with patch.object(FrontendConfig, 'get_browser_path') as mock_path:
        mock_path.return_value = "/invalid/path/to/browser"
        with pytest.raises(Exception):
            BrowserManager.initialize()

    # Test invalid chromedriver path
    with patch.object(FrontendConfig, 'get_chromedriver_path') as mock_driver_path:
        mock_driver_path.return_value = "/invalid/path/to/chromedriver"
        with pytest.raises(Exception):
            BrowserManager.initialize()


def test_headless_mode():
    """Test headless mode configuration."""
    with patch.object(FrontendConfig, 'get_browser_options') as mock_options:
        mock_options.return_value = {
            'headless': True,
            'incognito': True,
            'disable_infobars': True,
            'disable_notifications': True,
            'disable_extensions': True,
            'disable_gpu': True,
            'accept_insecure_certs': True
        }

        browser = BrowserManager.initialize()
        driver = browser.get_driver()

        # Verify browser works in headless mode
        driver.get("https://example.com")
        assert "Example" in driver.title
