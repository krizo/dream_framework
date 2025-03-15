from abc import ABC
from typing import Optional, TypeVar

from playwright.sync_api import Page, Locator, expect

from core.frontend.playwright.elements.element_locator import ElementLocator
from core.frontend.playwright.elements.elements_config import UIElementConfig
from helpers.decorators import wait_until

T = TypeVar('T', bound='UIElement')


class UIElement(ABC):
    """Base class for all page elements."""

    def __init__(self,
                 name: str,
                 locator: Optional[ElementLocator] = None,
                 timeout: Optional[int] = None,
                 parent: Optional['UIElement'] = None,
                 expected_tag: Optional[str] = None,
                 **kwargs):
        """
        Initialize base element.

        @param name: Element name for logging
        @param locator: ElementLocator instance
        @param timeout: Wait timeout in seconds
        @param parent: Optional parent element
        @param expected_tag: Expected HTML tag name
        @param kwargs: Locator arguments if locator not provided
        """
        self._page_owner = None
        self.name = name
        self.timeout = timeout or UIElementConfig.get_default_timeout()
        self.parent = parent
        self.expected_tag = expected_tag

        # Create locator from kwargs if not provided
        self.locator = locator or ElementLocator(**kwargs)

        # Page and locator will be set when element is used
        self._page: Optional[Page] = None
        self._locator: Optional[Locator] = None

    def _get_page(self) -> Page:
        """
        Get the page instance from parent or context.

        @return: Playwright Page instance
        @raises ValueError: If page is not available
        """
        if self._page:
            return self._page

        if self.parent and self.parent._page:
            return self.parent._page

        raise ValueError(f"No page context available for element '{self.name}'")

    def set_page(self, page: Page) -> 'UIElement':
        """
        Set the page instance for this element.

        @param page: Playwright Page instance
        @return: Self for method chaining
        """
        self._page = page
        return self

    def set_page_owner(self, owner) -> 'UIElement':
        """
        Set the page owner (typically a PageObject) for this element.

        @param owner: Owner object with page property
        @return: Self for method chaining
        """
        self._page_owner = owner
        return self

    def get_locator(self) -> Locator:
            """
            Get Playwright locator for this element.
        
            @return: Playwright Locator instance
            """
            # Always get the fresh page
            if not hasattr(self, '_page_owner') or not self._page_owner:
                return None
        
            # Get the current page from the owner
            current_page = self._page_owner.page
            if self._page != current_page:
                self._page = current_page
                self._locator = None  # Reset locator if the page has changed
        
            if self._locator:
                return self._locator
        
            page = self._get_page()
            selector = self.locator.get_playwright_selector()
        
            # If element has parent, locate relative to parent
            if self.parent:
                parent_locator = self.parent.get_locator()
                self._locator = parent_locator.locator(selector)
            else:
                self._locator = page.locator(selector)
        
            return self._locator

    def wait_for(self) -> 'UIElement':
        """
        Wait for element to be visible.

        @return: Self for method chaining
        @raises TimeoutError: If element is not visible within timeout
        """
        locator = self.get_locator()
        locator.wait_for(timeout=self.timeout * 1000)  # Convert to ms

        # Verify tag if expected_tag is set and strict matching is enabled
        if self.expected_tag and UIElementConfig.get_strict_matching():
            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            assert tag.lower() == self.expected_tag.lower(), \
                f"Element '{self.name}' has tag '{tag}', expected '{self.expected_tag}'"

        return self

    def click(self, force: bool = False, timeout: Optional[int] = None) -> 'UIElement':
        """
        Click on the element.

        @param force: Force click bypassing actionability checks
        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        """
        options = {}
        if force:
            options["force"] = True

        if timeout:
            options["timeout"] = timeout * 1000  # Convert to ms
        elif self.timeout:
            options["timeout"] = self.timeout * 1000

        self.get_locator().click(**options)
        return self

    def is_visible(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is visible.

        @param timeout: Custom timeout for this operation
        @return: True if element is visible, False otherwise
        """
        try:
            actual_timeout = (timeout or self.timeout) * 1000  # Convert to ms
            return self.get_locator().is_visible(timeout=actual_timeout)
        except Exception:
            return False

    def is_enabled(self) -> bool:
        """
        Check if element is enabled.

        @return: True if element is enabled, False otherwise
        """
        try:
            return self.get_locator().is_enabled()
        except Exception:
            return False

    def get_text(self) -> str:
        """
        Get element text content.

        @return: Element text
        """
        return self.get_locator().text_content() or ""

    def get_attribute(self, name: str) -> Optional[str]:
        """
        Get attribute value.

        @param name: Attribute name
        @return: Attribute value or None if not present
        """
        return self.get_locator().get_attribute(name)

    def hover(self, timeout: Optional[int] = None) -> 'UIElement':
        """
        Hover over the element.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        """
        options = {}
        if timeout:
            options["timeout"] = timeout * 1000
        elif self.timeout:
            options["timeout"] = self.timeout * 1000

        self.get_locator().hover(**options)
        return self

    def expect_visible(self, timeout: Optional[int] = None) -> 'UIElement':
        """
        Expect element to be visible.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If element is not visible
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).to_be_visible(timeout=actual_timeout * 1000)
        return self

    def expect_hidden(self, timeout: Optional[int] = None) -> 'UIElement':
        """
        Expect element to be hidden.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If element is visible
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).to_be_hidden(timeout=actual_timeout * 1000)
        return self

    def expect_enabled(self, timeout: Optional[int] = None) -> 'UIElement':
        """
        Expect element to be enabled.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If element is disabled
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).to_be_enabled(timeout=actual_timeout * 1000)
        return self

    @wait_until(timeout=10, interval=0.5)
    def wait_for_enabled(self):
        """
        Wait for element to be enabled.
        """
        assert self.expect_enabled(), "Element is not enabled"
        return self


    def expect_disabled(self, timeout: Optional[int] = None) -> 'UIElement':
        """
        Expect element to be disabled.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If element is enabled
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).to_be_disabled(timeout=actual_timeout * 1000)
        return self
