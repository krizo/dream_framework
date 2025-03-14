from core.frontend.playwright.elements.common.checkbox_element import CheckboxElement


class RadioElement(CheckboxElement):
    """Radio button element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize radio element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, **kwargs)