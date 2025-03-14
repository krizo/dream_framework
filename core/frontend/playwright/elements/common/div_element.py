from core.frontend.playwright.elements.ui_element import UIElement


class DivElement(UIElement):
    """Div element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize div element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="div", **kwargs)

