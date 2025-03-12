"""Base element implementations for page objects."""
from abc import ABC
from typing import Optional, Any, TypeVar, Type, Union

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from core.frontend.browser_manager import BrowserManager
from core.frontend.elements.element_locator import ElementLocator
from core.logger import Log

T = TypeVar('T', bound='BaseElement')


class BaseElement(ABC):
    """Base class for all page elements."""

    def __init__(self,
                 name: str,
                 timeout: int = 10,
                 parent: Optional['BaseElement'] = None,
                 expected_tag: Optional[str] = None,
                 **kwargs):
        """
        Initialize base element.

        @param name: Element name for logging
        @param timeout: Wait timeout in seconds
        @param parent: Optional parent element
        @param expected_tag: Expected HTML tag name
        @param kwargs: Locator arguments
        """
        self.name = name
        self.timeout = timeout
        self.parent = parent
        self.expected_tag = expected_tag
        self.locator = ElementLocator(**kwargs)

        self._driver = BrowserManager.get_driver()
        self._wait = WebDriverWait(self._driver, timeout)

    def find(self, timeout: Optional[int] = None) -> WebElement:
        """
        Find element on page.

        @param timeout: Optional custom timeout
        @return: WebElement instance
        @raises TimeoutException: If element not found within timeout
        """
        wait_time = timeout or self.timeout

        try:
            element = self._find_element(wait_time)
            if self.expected_tag:
                assert element.tag_name == self.expected_tag, \
                    f"Expected tag {self.expected_tag}, got {element.tag_name}"
            return element
        except TimeoutException:
            Log.error(f"Element {self.name} not found within {wait_time}s")
            raise

    def is_displayed(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is displayed.

        @param timeout: Optional custom timeout
        @return: True if element is displayed, False otherwise
        """
        try:
            element = self.find(timeout)
            return element.is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    def is_enabled(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is enabled.

        @param timeout: Optional custom timeout
        @return: True if element is enabled, False otherwise
        """
        try:
            element = self.find(timeout)
            return element.is_enabled()
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_until_visible(self, timeout: Optional[int] = None) -> None:
        """
        Wait until element is visible.

        @param timeout: Optional custom timeout
        @raises TimeoutException: If element not visible within timeout
        """
        wait_time = timeout or self.timeout
        wait = WebDriverWait(self._driver, wait_time)
        wait.until(
            EC.visibility_of_element_located((self.locator.by, self.locator.value))
        )

    def wait_until_clickable(self, timeout: Optional[int] = None) -> None:
        """
        Wait until element is clickable.

        @param timeout: Optional custom timeout
        @raises TimeoutException: If element not clickable within timeout
        """
        wait_time = timeout or self.timeout
        wait = WebDriverWait(self._driver, wait_time)
        wait.until(
            EC.element_to_be_clickable((self.locator.by, self.locator.value))
        )

    def wait_until_invisible(self, timeout: Optional[int] = None) -> None:
        """
        Wait until element is invisible.

        @param timeout: Optional custom timeout
        @raises TimeoutException: If element still visible after timeout
        """
        wait_time = timeout or self.timeout
        wait = WebDriverWait(self._driver, wait_time)
        wait.until(
            EC.invisibility_of_element_located((self.locator.by, self.locator.value))
        )

    def get_attribute(self, name: str) -> Optional[str]:
        """
        Get element attribute value.

        @param name: Attribute name
        @return: Attribute value or None if not found
        """
        element = self.find()
        return element.get_attribute(name)

    def get_property(self, name: str) -> Any:
        """
        Get element property value.

        @param name: Property name
        @return: Property value
        """
        element = self.find()
        return element.get_property(name)

    def has_class(self, class_name: str) -> bool:
        """
        Check if element has given CSS class.

        @param class_name: Class name to check
        @return: True if element has class, False otherwise
        """
        element = self.find()
        classes = element.get_attribute("class").split()
        return class_name in classes

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """
        Create element instance with given parameters.

        @param kwargs: Element parameters
        @return: Element instance
        """
        return cls(**kwargs)

    def scroll_into_view(self):
        """Scroll element into viewport."""
        element = self.find()
        self._driver.execute_script("arguments[0].scrollIntoView(true);", element)
        # Add small margin at the top to ensure element is fully visible
        self._driver.execute_script("window.scrollBy(0, -100);")

    def _find_element(self, timeout: int) -> WebElement:
        """
        Internal find element implementation.

        @param timeout: Wait timeout
        @return: WebElement instance
        """
        if self.parent:
            parent = self.parent.find(timeout)
            return parent.find_element(self.locator.by, self.locator.value)

        wait = WebDriverWait(self._driver, timeout)
        return wait.until(
            EC.presence_of_element_located((self.locator.by, self.locator.value))
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
