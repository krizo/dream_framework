from typing import Optional, List, Dict

from core.frontend.playwright.elements.ui_element import UIElement


class SelectElement(UIElement):
    """Select element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize select element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="select", **kwargs)

    def select_option(self,
                      value: Optional[str] = None,
                      label: Optional[str] = None,
                      index: Optional[int] = None) -> 'SelectElement':
        """
        Select option by value, label, or index.

        @param value: Option value
        @param label: Option label text
        @param index: Option index
        @return: Self for method chaining
        @raises ValueError: If no option specifier is provided
        """
        options = {}
        if value is not None:
            options["value"] = value
            log_value = f"value='{value}'"
        elif label is not None:
            options["label"] = label
            log_value = f"label='{label}'"
        elif index is not None:
            options["index"] = index
            log_value = f"index={index}"
        else:
            raise ValueError("Must provide either value, label, or index")

        self.get_locator().select_option(**options)
        return self

    def get_selected_value(self) -> Optional[str]:
        """
        Get selected option value.

        @return: Selected option value or None if nothing selected
        """
        return self.get_locator().evaluate("""select => {
            const option = select.options[select.selectedIndex];
            return option ? option.value : null;
        }""")

    def get_selected_text(self) -> Optional[str]:
        """
        Get selected option text.

        @return: Selected option text or None if nothing selected
        """
        return self.get_locator().evaluate("""select => {
            const option = select.options[select.selectedIndex];
            return option ? option.text : null;
        }""")

    def get_options(self) -> List[Dict[str, str]]:
        """
        Get all options in the select.

        @return: List of options with their values and texts
        """
        return self.get_locator().evaluate("""select => {
            return Array.from(select.options).map(option => ({
                value: option.value,
                text: option.text,
                disabled: option.disabled
            }));
        }""")