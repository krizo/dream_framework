"""Checkbox element implementations."""
from typing import List

from core.frontend.elements.base_element import BaseElement


class Checkbox(BaseElement):
    """Checkbox element implementation."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, expected_tag="input", **kwargs)


class CheckboxGroup:
    """Group of related checkboxes."""

    def __init__(self, name: str, checkboxes: List[Checkbox]):
        """
        Initialize checkbox group.

        @param name: Group name
        @param checkboxes: List of checkboxes in group
        """
        self.name = name
        self.checkboxes = checkboxes