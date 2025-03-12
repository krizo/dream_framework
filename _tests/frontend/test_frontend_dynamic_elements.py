"""Tests for dynamic elements implementations."""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.frontend.elements.dynamic.loading_indicator import LoadingIndicator
from core.frontend.elements.dynamic.delayed_indicator import DelayedElement


@pytest.fixture
def delayed_button(page):
    """Get delayed content button."""
    button = WebDriverWait(page, 10).until(
        EC.element_to_be_clickable((By.ID, "delayed-btn"))
    )

    # Ensure button is in view
    page.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    time.sleep(0.5)  # Allow scroll to complete

    return button


def test_dynamic_elements(page, delayed_button):
    """Test dynamic elements behavior including loading and delayed content."""
    # Initialize elements
    loading = LoadingIndicator(
        name="Loading indicator",
        id="loading-indicator"
    )

    delayed_content = DelayedElement(
        name="Delayed content",
        id="delayed-content"
    )

    # Verify initial state
    assert not loading.is_loading()
    assert not delayed_content.is_visible()

    # Trigger content load
    page.execute_script("arguments[0].click();", delayed_button)

    # Verify loading sequence
    loading.wait_until_loading()
    assert loading.is_loading()

    # Wait for content to appear
    loading.wait_until_not_loading()
    delayed_content.wait_until_visible()

    # Verify final state
    assert not loading.is_loading()
    assert delayed_content.is_visible()
    assert "This content appears after a delay!" in delayed_content.find().text


def test_loading_indicator(page):
    """Test loading indicator behavior."""
    loading = LoadingIndicator(
        name="Loading indicator",
        id="loading-indicator"
    )

    # Print initial state
    print(f"\nInitial loading state: {loading.is_loading()}")

    # Find and prepare button
    button = WebDriverWait(page, 10).until(
        EC.element_to_be_clickable((By.ID, "delayed-btn"))
    )

    # Scroll with offset
    page.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    time.sleep(1)  # give time for scroll to complete

    print(f"Button is displayed: {button.is_displayed()}")
    print(f"Button location: {button.location}")
    print(f"Button size: {button.size}")

    # Try to click with JavaScript
    page.execute_script("arguments[0].click();", button)

    # Verify loading state
    print(f"Loading state after click: {loading.is_loading()}")
    # Should show loading
    loading.wait_until_loading()
    assert loading.is_loading()

    # Should hide after delay
    loading.wait_until_not_loading()
    assert not loading.is_loading()
