"""Dynamic loading elements implementations."""
from typing import Optional

from core.frontend.elements.base_element import BaseElement


class LoadingIndicator(BaseElement):
    """Loading indicator/spinner element implementation."""

    def __init__(self,
                 name: str,
                 active_class: str = "active",
                 **kwargs):
        """
        Initialize loading indicator.

        @param name: Element name
        @param active_class: CSS class indicating active state
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, expected_tag="div", **kwargs)
        self.active_class = active_class

    def is_loading(self) -> bool:
        """
        Check if loading indicator is active.

        @return: True if loading is active, False otherwise
        """
        try:
            element = self.find()
            return self.active_class in element.get_attribute("class").split()
        except:
            return False

    def wait_until_loading(self, timeout: Optional[int] = None) -> None:
        """
        Wait until loading indicator is active.

        @param timeout: Maximum time to wait in seconds
        """
        wait_time = timeout or self.timeout
        self._wait.until(lambda _: self.is_loading())

    def wait_until_not_loading(self, timeout: Optional[int] = None) -> None:
        """
        Wait until loading indicator is inactive.

        @param timeout: Maximum time to wait in seconds
        """
        wait_time = timeout or self.timeout
        self._wait.until(lambda _: not self.is_loading())


