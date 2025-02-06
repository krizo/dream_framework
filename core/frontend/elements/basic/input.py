"""Input field implementations."""
from typing import Optional

from selenium.webdriver.common.by import By

from core.frontend.elements.base_element import BaseElement


class Input(BaseElement):
    """Base input field implementation."""

    def __init__(self,
                 name: str,
                 input_type: str = "text",
                 **kwargs):
        """
        Initialize input field.

        @param name: Field name
        @param input_type: Expected input type
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, expected_tag="input", **kwargs)
        self.input_type = input_type


class TextField(Input):
    """Text input field."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, input_type="text", **kwargs)


class EmailField(Input):
    """Email input field."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, input_type="email", **kwargs)


class PasswordField(Input):
    """Password input field."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, input_type="password", **kwargs)


class DateField(Input):
    """Date input field."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, input_type="date", **kwargs)


class RangeField(Input):
    """Range input field."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, input_type="range", **kwargs)