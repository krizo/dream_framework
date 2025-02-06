"""Textarea element implementation."""
from core.frontend.elements.base_element import BaseElement


class TextArea(BaseElement):
    """Textarea element implementation."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, expected_tag="textarea", **kwargs)