"""Base page object implementation for Playwright."""
import re
from typing import Dict, Optional, TypeVar, Generic, List

from playwright.sync_api import Page, expect, Locator

from core.frontend.playwright.base_elements import BasePageElements
from core.frontend.playwright.playwright_manager import PlaywrightManager
from core.logger import Log
from core.step import step_start
from medmutual.run_env import RunEnvironment

T = TypeVar('T')


class BasePage(Generic[T], BasePageElements):
    """
    Base class for all page objects.
    Provides common methods for interacting with web pages.
    """

    # Base URL to be overridden by environment-specific settings
    _base_url = ""

    # Page path to be overridden by specific page classes
    _page_path = ""

    def __init__(self, page: Optional[Page] = None):
        """
        Initialize base page object.

        @param page: Playwright Page instance (optional, will use singleton if None)
        """
        self._manager: PlaywrightManager = PlaywrightManager.get_instance() or PlaywrightManager.initialize()
        self._env: RunEnvironment = RunEnvironment.get_instance()

        if page:
            self._page = page
        else:
            if self._page_path:
                self._page = self._manager.get_page_by_url(self._page_path)

            if not self._page:
                self._page = self._manager.get_page()
        self._explicit_page = None
        self._initialize_elements(self.page)


    @property
    def page(self) -> Page:
        """
        Get the current page instance.

        @return: Playwright Page instance
        """
        if self._explicit_page:
            return self._explicit_page

        return self._manager.get_page()

    @property
    def base_url(self) -> str:
        """
        Get the base URL for this page.
        Should be overridden by derived classes or environment configuration.

        @return: Base URL string
        """
        if not self._base_url:
            try:
                return self._env.base_url
            except AttributeError:
                Log.warning("No base URL found in environment configuration")
                return ""
        return self._base_url

    @property
    def page_path(self) -> str:
        """
        Get the page path (endpoint) for this page.
        Should be overridden by derived classes.

        @return: Page path string
        """
        return self._page_path

    @property
    def url(self) -> str:
        """
        Get the full URL for this page.

        @return: Full URL string
        """
        base = self.base_url.rstrip('/')
        path = self.page_path.lstrip('/')
        return f"{base}/{path}"

    @property
    def current_url(self) -> str:
        """
        Get the current page URL.

        @return: Current URL string
        """
        return self.page.url

    @property
    def title(self) -> str:
        """
        Get the current page title.

        @return: Page title
        """
        return self.page.title()

    def navigate_to(self) -> T:
        """
        Navigate to this page using its URL.

        @return: Self for method chaining
        """
        if self.url != self.current_url:
            with step_start(f"Navigate to {self.url}"):
                self.page.goto(self.url)
                return self

    def navigate_to_url(self, url: str) -> T:
        """
        Navigate to a specific URL.

        @param url: URL to navigate to
        @return: Self for method chaining
        """
        with step_start(f"Navigate to URL: {url}"):
            self.page.goto(url)
            return self

    def reload(self) -> T:
        """
        Reload the current page.

        @return: Self for method chaining
        """
        self.page.reload()
        return self

    def go_back(self) -> T:
        """
        Navigate back in browser history.

        @return: Self for method chaining
        """
        self.page.go_back()
        return self

    def go_forward(self) -> T:
        """
        Navigate forward in browser history.

        @return: Self for method chaining
        """
        self.page.go_forward()
        return self

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        """
        Check if page is displayed properly.
        Override this method in derived classes to implement page-specific checks.

        @param timeout: Optional timeout in milliseconds
        @return: True if page is displayed, False otherwise
        """
        # Basic check - we're on the right URL
        return bool(re.search(self.url, self.current_url))

    def wait_for_load_state(self, state: str = 'networkidle') -> T:
        """
        Wait for a specific load state.

        @param state: Load state to wait for ('load', 'domcontentloaded', 'networkidle')
        @return: Self for method chaining
        """
        self.page.wait_for_load_state(state)
        return self

    def wait_for_url(self, url_pattern: str, timeout: Optional[float] = None) -> T:
        """
        Wait for URL to match a pattern.

        @param url_pattern: URL pattern to match
        @param timeout: Optional timeout in milliseconds
        @return: Self for method chaining
        """
        self.page.wait_for_url(url_pattern, timeout=timeout)
        return self

    def wait_for_selector(self, selector: str, timeout: Optional[float] = None) -> Locator:
        """
        Wait for an element matching the selector to be visible.

        @param selector: CSS or XPath selector
        @param timeout: Optional timeout in milliseconds
        @return: Locator for the element
        """
        locator = self.page.locator(selector)
        locator.wait_for(timeout=timeout)
        return locator

    def fill_form(self, form_data: Dict[str, str]) -> T:
        """
        Fill form with provided data.
        Form data should be a dictionary with selectors as keys and values to fill.

        @param form_data: Dictionary with selectors and values
        @return: Self for method chaining
        """
        for selector, value in form_data.items():
            with step_start(f"Filling '{selector}' with value '{value}'"):
                self.page.fill(selector, value)
        return self

    def click(self, selector: str, force: bool = False) -> T:
        """
        Click an element.

        @param selector: CSS or XPath selector
        @param force: Force click, bypassing actionability checks
        @return: Self for method chaining
        """
        self.page.click(selector, force=force)
        return self

    def hover(self, selector: str) -> T:
        """
        Hover over an element.

        @param selector: CSS or XPath selector
        @return: Self for method chaining
        """
        self.page.hover(selector)
        return self

    def get_text(self, selector: str) -> str:
        """
        Get text from an element.

        @param selector: CSS or XPath selector
        @return: Element text content
        """
        return self.page.locator(selector).text_content() or ""

    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.

        @param selector: CSS or XPath selector
        @return: True if element is visible, False otherwise
        """
        return self.page.locator(selector).is_visible()

    def select_option(self, selector: str, value: Optional[str] = None, label: Optional[str] = None,
                      index: Optional[int] = None) -> T:
        """
        Select an option from a dropdown.

        @param selector: CSS or XPath selector for the select element
        @param value: Option value to select
        @param label: Option label to select
        @param index: Option index to select
        @return: Self for method chaining
        """
        if value:
            self.page.select_option(selector, value=value)
        elif label:
            self.page.select_option(selector, label=label)
        elif index is not None:
            self.page.select_option(selector, index=index)
        return self

    def mark_checkbox(self, selector: str) -> T:
        """
        Check a checkbox or radio button.

        @param selector: CSS or XPath selector
        @return: Self for method chaining
        """
        self.page.check(selector)
        return self

    def unmark_checkbox(self, selector: str) -> T:
        """
        Uncheck a checkbox.

        @param selector: CSS or XPath selector
        @return: Self for method chaining
        """
        with step_start(f"Unchecking: {selector}"):
            self.page.uncheck(selector)
            return self

    def take_screenshot(self, name: str, full_page: bool = True) -> str:
        """
        Take a screenshot of the current page.

        @param name: Name for the screenshot (without extension)
        @param full_page: Whether to take a screenshot of the full page or just the viewport
        @return: Path to the screenshot file
        """
        return self._manager.take_screenshot(name, self.page, full_page)

    def expect_url(self, url_pattern: str) -> T:
        """
        Expect the current URL to match a pattern.

        @param url_pattern: URL pattern to match
        @return: Self for method chaining
        """
        expect(self.page).to_have_url(re.compile(url_pattern))
        return self

    def expect_title(self, title_pattern: str) -> T:
        """
        Expect the page title to match a pattern.

        @param title_pattern: Title pattern to match
        @return: Self for method chaining
        """
        expect(self.page).to_have_title(re.compile(title_pattern))
        return self

    def expect_visible(self, selector: str) -> T:
        """
        Expect an element to be visible.

        @param selector: CSS or XPath selector
        @return: Self for method chaining
        """
        expect(self.page.locator(selector)).to_be_visible()
        return self

    def expect_text(self, selector: str, text: str) -> T:
        """
        Expect an element to contain specified text.

        @param selector: CSS or XPath selector
        @param text: Expected text
        @return: Self for method chaining
        """
        expect(self.page.locator(selector)).to_contain_text(text)
        return self

    def clear_cookies(self) -> T:
        """
        Clear cookies for the current context.

        @return: Self for method chaining
        """
        self._manager.clear_cookies()
        return self

    @classmethod
    def create(cls, page: Optional[Page] = None) -> T:
        """
        Factory method to create a page object.

        @param page: Playwright Page instance (optional)
        @return: Page object instance
        """
        return cls(page)

