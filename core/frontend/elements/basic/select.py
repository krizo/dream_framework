"""Select element implementations."""
from typing import Optional

from selenium.webdriver.support.select import Select as SeleniumSelect

from core.frontend.elements.base_element import BaseElement


class Select(BaseElement):
    """Select element implementation."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, expected_tag="select", **kwargs)

    def get_selenium_select(self) -> SeleniumSelect:
        """
        Get Selenium Select object.

        @return: SeleniumSelect instance
        """
        return SeleniumSelect(self.find())
