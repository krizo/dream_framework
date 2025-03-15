from core.frontend.playwright.elements.ui_element import UIElement


class SpanElement(UIElement):
    """Span element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize span element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="span", **kwargs)

