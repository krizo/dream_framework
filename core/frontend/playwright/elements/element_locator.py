from typing import Optional

from core.frontend.playwright.elements.locator_types import LocatorType


class ElementLocator:
    """Element locator with selector type."""

    def __init__(self,
                 locator_type: Optional[LocatorType] = None,
                 selector: Optional[str] = None,
                 **kwargs):
        """
        Initialize element locator.

        @param locator_type: Type of locator from ElementType enum
        @param selector: Selector string
        @param kwargs: Alternative way to specify locator (e.g., css="div.class")
        """
        if selector and locator_type:
            self.locator_type = locator_type
            self.selector = selector
        else:
            # Extract locator from kwargs
            for key, value in kwargs.items():
                try:
                    self.locator_type = LocatorType(key)
                    self.selector = value
                    break
                except ValueError:
                    continue
            else:
                if "selector" in kwargs:
                    # Default to CSS if only selector is provided
                    self.locator_type = LocatorType.CSS
                    self.selector = kwargs["selector"]
                else:
                    raise ValueError("No valid locator provided. Use locator_type and selector, "
                                     "or keyword arguments like css='.selector', xpath='//div'")

    def get_playwright_selector(self) -> str:
        """
        Get selector string in Playwright format.

        @return: Playwright-compatible selector string
        """
        if self.locator_type == LocatorType.CSS:
            return self.selector
        elif self.locator_type == LocatorType.XPATH:
            return f"xpath={self.selector}"
        elif self.locator_type == LocatorType.TEXT:
            return f"text={self.selector}"
        elif self.locator_type == LocatorType.ID:
            return f"#{self.selector}"
        elif self.locator_type == LocatorType.CLASS:
            return f".{self.selector}"
        elif self.locator_type == LocatorType.NAME:
            return f"[name='{self.selector}']"
        elif self.locator_type == LocatorType.TAG:
            return self.selector
        elif self.locator_type == LocatorType.ROLE:
            return f"role={self.selector}"
        elif self.locator_type == LocatorType.TEST_ID:
            return f"[data-testid='{self.selector}']"
        else:
            return self.selector

    def __str__(self) -> str:
        """
        String representation of the locator.

        @return: String description of locator
        """
        return f"{self.locator_type.value}='{self.selector}'"