from typing import Optional

from playwright.sync_api import expect

from core.frontend.playwright.elements.ui_element import UIElement


class CheckboxElement(UIElement):
    """Checkbox element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize checkbox element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="input", **kwargs)

    def check(self, force: bool = False) -> 'CheckboxElement':
        """
        Check the checkbox.

        @param force: Force check bypassing actionability checks
        @return: Self for method chaining
        """
        options = {}
        if force:
            options["force"] = True

        self.get_locator().check(**options)
        return self

    def uncheck(self, force: bool = False) -> 'CheckboxElement':
        """
        Uncheck the checkbox.

        @param force: Force uncheck bypassing actionability checks
        @return: Self for method chaining
        """
        options = {}
        if force:
            options["force"] = True

        self.get_locator().uncheck(**options)
        return self

    def is_checked(self) -> bool:
        """
        Check if checkbox is checked.

        @return: True if checkbox is checked, False otherwise
        """
        return self.get_locator().is_checked()

    def expect_checked(self, timeout: Optional[int] = None) -> 'CheckboxElement':
        """
        Expect checkbox to be checked.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If checkbox is not checked
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).to_be_checked(timeout=actual_timeout * 1000)
        return self

    def expect_unchecked(self, timeout: Optional[int] = None) -> 'CheckboxElement':
        """
        Expect checkbox not to be checked.

        @param timeout: Custom timeout for this operation
        @return: Self for method chaining
        @raises AssertionError: If checkbox is checked
        """
        actual_timeout = timeout or self.timeout
        expect(self.get_locator()).not_to_be_checked(timeout=actual_timeout * 1000)
        return self