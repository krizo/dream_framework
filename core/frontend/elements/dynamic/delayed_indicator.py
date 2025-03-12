"""DelayedElement implementation."""
from typing import Optional

from core.frontend.elements.base_element import BaseElement


class DelayedElement(BaseElement):
    """Element that appears after a delay."""

    def __init__(self,
                 name: str,
                 visible_class: str = "visible",
                 **kwargs):
        """
        Initialize delayed element.

        @param name: Element name
        @param visible_class: CSS class indicating visibility
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, **kwargs)
        self.visible_class = visible_class

    def is_visible(self) -> bool:
        """
        Check if element is visible.

        @return: True if element is visible, False otherwise
        """
        try:
            element = self.find()
            return self.visible_class in element.get_attribute("class").split()
        except:
            return False

    def wait_until_visible(self, timeout: Optional[int] = None) -> None:
        """
        Wait until element becomes visible.

        @param timeout: Maximum time to wait in seconds
        """
        wait_time = timeout or self.timeout
        self._wait.until(lambda _: self.is_visible())

    def wait_until_hidden(self, timeout: Optional[int] = None) -> None:
        """
        Wait until element becomes hidden.

        @param timeout: Maximum time to wait in seconds
        """
        wait_time = timeout or self.timeout
        self._wait.until(lambda _: not self.is_visible())