from typing import Dict

from core.frontend.playwright.elements.ui_element import UIElement


class FormElement(UIElement):
    """Form element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize form element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="form", **kwargs)

    def submit(self) -> 'FormElement':
        """
        Submit the form.

        @return: Self for method chaining
        """
        # Use JavaScript to submit the form
        self.get_locator().evaluate("form => form.submit()")
        return self

    def fill_fields(self, data: Dict[str, str]) -> 'FormElement':
        """
        Fill multiple form fields.

        @param data: Dictionary mapping field names/selectors to values
        @return: Self for method chaining
        """
        page = self._get_page()
        form_locator = self.get_locator()

        for selector, value in data.items():
            form_locator.locator(selector).fill(value)

        return self