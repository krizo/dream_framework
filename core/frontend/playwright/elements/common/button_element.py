from core.frontend.playwright.elements.ui_element import UIElement


class ButtonElement(UIElement):
    """Button element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize button element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="button", **kwargs)

