"""Button element implementations."""
from core.frontend.elements.base_element import BaseElement


class Button(BaseElement):
    """Button element implementation."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, expected_tag="button", **kwargs)


class SubmitButton(Button):
    """Submit button implementation."""

    def __init__(self, name: str = "Submit button", **kwargs):
        super().__init__(name=name, **kwargs)