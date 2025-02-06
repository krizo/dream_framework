"""Tests for basic page elements implementations."""
import os
from typing import Any, Generator

import pytest
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

from core.frontend.browser_manager import BrowserManager
from core.frontend.elements.basic.button import SubmitButton, Button
from core.frontend.elements.basic.checkbox import Checkbox, CheckboxGroup
from core.frontend.elements.basic.input import TextField, EmailField, PasswordField, DateField, RangeField
from core.frontend.elements.basic.radio import RadioButton, RadioGroup
from core.frontend.elements.basic.select import Select
from core.frontend.elements.basic.textarea import TextArea


@pytest.fixture(scope="session")
def server_url() -> Generator[str, Any, None]:
    """Start local server with test page."""
    page_name = "example_html_page.html"
    test_page = Path(__file__).parent / page_name

    os.chdir(test_page.parent)

    server = HTTPServer(('localhost', 0), SimpleHTTPRequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://localhost:{server.server_port}/{page_name}"

    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def browser():
    """Initialize and clean up browser."""
    browser = BrowserManager.initialize()
    yield browser
    BrowserManager.close()


@pytest.fixture
def page(server_url, browser):
    """Load test page."""
    browser.get_driver().get(server_url)
    return browser.get_driver()


def test_text_field(page):
    """Test TextField element."""
    username = TextField(
        name="Username field",
        id="username"
    )

    assert username.is_displayed()

    element = username.find()
    assert element.get_attribute("type") == "text"
    assert element.get_attribute("required") == "true"
    assert element.get_attribute("placeholder") == "Enter username"


def test_email_field(page):
    """Test EmailField element."""
    email = EmailField(
        name="Email field",
        id="email"
    )

    # Sprawdzenie typu
    element = email.find()
    assert element.get_attribute("type") == "email"
    assert element.get_attribute("required") == "true"


def test_password_field(page):
    """Test PasswordField element."""
    password = PasswordField(
        name="Password field",
        id="password"
    )

    element = password.find()
    assert element.get_attribute("type") == "password"


def test_date_field(page):
    """Test DateField element."""
    date = DateField(
        name="Birth Date field",
        id="birthdate"
    )

    element = date.find()
    assert element.get_attribute("type") == "date"


def test_range_field(page):
    """Test RangeField element."""
    satisfaction = RangeField(
        name="Satisfaction level",
        id="satisfaction"
    )

    element = satisfaction.find()
    assert element.get_attribute("type") == "range"
    assert element.get_attribute("min") == "0"
    assert element.get_attribute("max") == "10"


def test_select(page):
    """Test Select element."""
    country = Select(
        name="Country selector",
        id="country"
    )

    # Sprawdzenie opcji
    select = country.get_selenium_select()
    options = [opt.get_attribute("value") for opt in select.options]
    assert "" in options  # pusta opcja
    assert "pl" in options
    assert "de" in options
    assert "fr" in options


def test_checkbox_group(page):
    """Test CheckboxGroup element."""
    interests = [
        Checkbox(name="Sports checkbox", id="sports"),
        Checkbox(name="Music checkbox", id="music"),
        Checkbox(name="Reading checkbox", id="reading")
    ]

    interest_group = CheckboxGroup(
        name="Interests group",
        checkboxes=interests
    )

    for checkbox in interest_group.checkboxes:
        assert checkbox.is_displayed()
        element = checkbox.find()
        assert element.get_attribute("type") == "checkbox"


def test_radio_group(page):
    """Test RadioGroup element."""
    genders = [
        RadioButton(name="Male radio", id="male"),
        RadioButton(name="Female radio", id="female"),
        RadioButton(name="Other radio", id="other")
    ]

    gender_group = RadioGroup(
        name="Gender group",
        buttons=genders
    )

    for radio in gender_group.buttons:
        assert radio.is_displayed()
        element = radio.find()
        assert element.get_attribute("type") == "radio"
        assert element.get_attribute("name") == "gender"


def test_textarea(page):
    """Test TextArea element."""
    comments = TextArea(
        name="Comments area",
        id="comments"
    )

    element = comments.find()
    assert element.tag_name == "textarea"
    assert element.get_attribute("rows") == "3"


def test_buttons(page):
    """Test Button elements."""
    submit = SubmitButton(
        name="Submit button",
        id="submit-btn"
    )

    cancel = Button(
        name="Cancel button",
        id="cancel-btn"
    )

    assert submit.is_displayed()
    assert cancel.is_displayed()

    submit_el = submit.find()
    assert submit_el.get_attribute("type") == "submit"

    cancel_el = cancel.find()
    assert cancel_el.get_attribute("type") == "button"
