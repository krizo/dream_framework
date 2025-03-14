from typing import Optional

from core.frontend.playwright.elements.ui_element import UIElement


class LinkElement(UIElement):
    """Link element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize link element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="a", **kwargs)

    def get_href(self) -> Optional[str]:
        """
        Get link href attribute.

        @return: Href attribute value or None if not present
        """
        return self.get_attribute("href")
