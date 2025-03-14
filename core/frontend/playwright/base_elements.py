from playwright.sync_api import Page

from core.frontend.playwright.elements.ui_element import UIElement


class BasePageElements:
    """
    Mixin for page element initialization.
    Allows UI elements to be defined as class attributes and initialized with page context.
    """

    def _initialize_elements(self, page: Page) -> None:
        """
        Initialize all UI elements with page context.
        Should be called from __init__ or a similar initialization method.

        @param page: Playwright Page instance
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, UIElement):
                attr.set_page(page)
                attr.set_page_owner(self)