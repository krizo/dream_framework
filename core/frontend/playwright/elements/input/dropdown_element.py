from core.frontend.playwright.elements.ui_element import UIElement
from core.step import step_start

class DropdownElement(UIElement):
    """Dropdown element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize dropdown element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, **kwargs)

    def select_option(self, option_text: str) -> 'DropdownElement':
        """
        Select option by visible text.

        @param option_text: Text of the option to select
        @return: Self for method chaining
        """
        with step_start(f"Selecting '{option_text}' from dropdown '{self.name}'"):
            # First click the dropdown button to open it
            self.get_locator().click()

            # Find and click the option with the given text
            page = self._get_page()
            option_locator = page.locator(f"li a.dropdown-item:text-is(\" {option_text} \")")
            option_locator.click()

        return self

    def get_selected_text(self) -> str:
        """
        Get the text of the selected option.

        @return: Selected option text
        """
        return self.get_locator().inner_text().strip()