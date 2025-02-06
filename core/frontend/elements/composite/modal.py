"""Modal dialog element implementations."""
from selenium.webdriver.support.wait import WebDriverWait

from core.frontend.elements.base_element import BaseElement


class Modal(BaseElement):
    """Modal dialog implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize modal dialog.

        @param name: Modal name
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, expected_tag="div", **kwargs)

        self.dialog = BaseElement(
            name=f"{name} dialog",
            xpath=".//div[contains(@class, 'modal-dialog')]",
            parent=self
        )

        self.content = BaseElement(
            name=f"{name} content",
            xpath=".//div[contains(@class, 'modal-content')]",
            parent=self.dialog
        )

        self.header = BaseElement(
            name=f"{name} header",
            xpath=".//div[contains(@class, 'modal-header')]",
            parent=self.content
        )

        self.title = BaseElement(
            name=f"{name} title",
            xpath=".//h5",
            parent=self.header
        )

        self.close_button = BaseElement(
            name=f"{name} close button",
            xpath=".//button[contains(@class, 'btn-close')]",
            parent=self.header
        )

        self.body = BaseElement(
            name=f"{name} body",
            xpath=".//div[contains(@class, 'modal-body')]",
            parent=self.content
        )

        self.footer = BaseElement(
            name=f"{name} footer",
            xpath=".//div[contains(@class, 'modal-footer')]",
            parent=self.content
        )

    def wait_until_open(self, timeout: int = 10) -> None:
        """
        Wait until modal is fully visible.

        @param timeout: Maximum time to wait in seconds
        """
        wait = WebDriverWait(self._driver, timeout)
        modal = self.find()
        wait.until(lambda _: 'show' in modal.get_attribute('class').split())

    def wait_until_closed(self, timeout: int = 10) -> None:
        """
        Wait until modal is fully hidden.

        @param timeout: Maximum time to wait in seconds
        """
        wait = WebDriverWait(self._driver, timeout)
        modal = self.find()
        wait.until(lambda _: 'show' not in modal.get_attribute('class').split())

    def is_open(self) -> bool:
        """
        Check if modal is open.

        @return: True if modal is open, False otherwise
        """
        try:
            element = self.find()
            return 'show' in element.get_attribute('class').split()
        except:
            return False