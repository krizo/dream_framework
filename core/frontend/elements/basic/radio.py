"""Radio button element implementations."""
from typing import List

from core.frontend.elements.base_element import BaseElement


class RadioButton(BaseElement):
    """Radio button element implementation."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, expected_tag="input", **kwargs)


class RadioGroup:
    """Group of related radio buttons."""

    def __init__(self, name: str, buttons: List[RadioButton]):
        """
        Initialize radio group.

        @param name: Group name
        @param buttons: List of radio buttons in group
        """
        self.name = name
        self.buttons = buttons
