from core.frontend.playwright.elements.ui_element import UIElement
from core.step import step_start


class AlertElement(UIElement):
    """
    Alert element implementation.

    Although alerts are not DOM elements, this class follows the element pattern
    for consistency with the rest of the framework.
    """

    def __init__(self, name: str = "Alert Dialog"):
        """
        Initialize alert element.

        @param name: Element name for logging
        """
        # We don't need a real locator for alerts, but we still call super
        super().__init__(name=name, css="body")

    def confirm(self) -> 'AlertElement':
        """
        Confirm an alert dialog if it appears.

        @return: Self for method chaining
        """
        with step_start(f"Confirming {self.name}"):
            page = self._get_page()
            page.once("dialog", lambda dialog: dialog.accept())
            return self

    def dismiss(self) -> 'AlertElement':
        """
        Dismiss an alert dialog if it appears.

        @return: Self for method chaining
        """
        with step_start(f"Dismissing {self.name}"):
            page = self._get_page()
            page.once("dialog", lambda dialog: dialog.dismiss())
            return self

    def get_text_and_confirm(self) -> str:
        """
        Get the text from an alert dialog and confirm it.

        @return: Text of the alert dialog
        """
        with step_start(f"Getting text from {self.name} and confirming"):
            page = self._get_page()
            alert_text = ""

            def handle_dialog(dialog):
                nonlocal alert_text
                alert_text = dialog.message
                dialog.accept()

            page.once("dialog", handle_dialog)
            return alert_text
