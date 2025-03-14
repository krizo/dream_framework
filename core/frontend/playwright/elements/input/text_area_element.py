from core.frontend.playwright.elements.input.input_element import InputElement


class TextAreaElement(InputElement):
    """Textarea element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize textarea element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="textarea", **kwargs)