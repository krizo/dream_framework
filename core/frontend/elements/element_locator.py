from typing import Optional

from selenium.webdriver.common.by import By


class ElementLocator:
    """Element locator encapsulation."""

    def __init__(self,
                 by: Optional[By] = None,
                 value: Optional[str] = None,
                 xpath: Optional[str] = None,
                 css: Optional[str] = None,
                 id: Optional[str] = None,
                 name: Optional[str] = None,
                 class_name: Optional[str] = None):
        """
        Initialize locator.

        @param by: Selenium By locator
        @param value: Locator value
        @param xpath: XPath locator
        @param css: CSS selector
        @param id: Element ID
        @param name: Element name attribute
        @param class_name: Element class name
        @raises ValueError: If no valid locator provided
        """
        if xpath is not None:
            self.by = By.XPATH
            self.value = xpath
        elif css is not None:
            self.by = By.CSS_SELECTOR
            self.value = css
        elif id is not None:
            self.by = By.ID
            self.value = id
        elif name is not None:
            self.by = By.NAME
            self.value = name
        elif class_name is not None:
            self.by = By.CLASS_NAME
            self.value = class_name
        elif by is not None and value is not None:
            self.by = by
            self.value = value
        else:
            raise ValueError("No valid locator provided")