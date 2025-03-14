from typing import Optional

from core.frontend.playwright.elements.ui_element import UIElement


class InputElement(UIElement):
    """Input element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize input element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="input", **kwargs)

    def fill(self, value: str, force: bool = False) -> 'InputElement':
        """
        Fill input with value.

        @param value: Value to fill
        @param force: Force fill bypassing actionability checks
        @return: Self for method chaining
        """
        options = {}
        if force:
            options["force"] = True

        self.get_locator().fill(value, **options)
        return self

    def clear(self) -> 'InputElement':
        """
        Clear input value.

        @return: Self for method chaining
        """
        self.get_locator().clear()
        return self

    def type(self, text: str, delay: Optional[int] = None) -> 'InputElement':
        """
        Type text into input with optional delay between keystrokes.

        @param text: Text to type
        @param delay: Delay between keystrokes in milliseconds
        @return: Self for method chaining
        """
        options = {}
        if delay is not None:
            options["delay"] = delay

        self.get_locator().type(text, **options)
        return self

    def get_value(self) -> str:
        """
        Get input value.

        @return: Current input value
        """
        return self.get_locator().input_value()