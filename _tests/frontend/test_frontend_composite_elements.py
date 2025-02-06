"""Tests for composite page elements implementations."""
import pytest

from core.frontend.elements.composite.table import Table, TableRow, TableCell
from core.frontend.elements.composite.modal import Modal


def test_table_structure(page):
    """Test table structure and elements hierarchy."""
    data_table = Table(
        name="Data table",
        id="data-table"
    )

    # Verify table exists
    assert data_table.is_displayed()

    # Verify header existence and structure
    header_cells = data_table.header.find().find_elements("xpath", ".//th")
    assert len(header_cells) == 4
    assert [cell.text for cell in header_cells] == ["ID", "Name", "Email", "Actions"]

    # Verify body existence and content
    rows = data_table.body.find().find_elements("xpath", ".//tr")
    assert len(rows) == 2  # Two data rows

    # Verify first row content
    first_row = TableRow(
        name="First row",
        xpath=".//tr[1]",
        parent=data_table.body
    )
    cells = first_row.find().find_elements("xpath", ".//td")
    assert len(cells) == 4
    assert cells[0].text == "1"
    assert cells[1].text == "John Doe"
    assert cells[2].text == "john@example.com"


def test_table_cells(page):
    """Test table cell elements."""
    # Test header cell
    header_cell = TableCell(
        name="ID Header",
        is_header=True,
        xpath="//table[@id='data-table']//th[1]"
    )
    assert header_cell.is_displayed()
    assert header_cell.find().text == "ID"

    # Test data cell
    data_cell = TableCell(
        name="First name",
        xpath="//table[@id='data-table']//tbody//tr[1]/td[2]"
    )
    assert data_cell.is_displayed()
    assert data_cell.find().text == "John Doe"


def test_modal_structure(page):
    """Test modal dialog structure and hierarchy."""
    modal = Modal(
        name="Test modal",
        id="testModal"
    )

    # Initial state - modal should be in DOM but not visible
    modal_element = modal.find()
    assert modal_element is not None
    assert not modal.is_open()

    # Open modal using Bootstrap API
    page.execute_script("""
        var modal = new bootstrap.Modal(document.getElementById('testModal'));
        modal.show();
    """)

    # Wait for modal to be fully visible
    modal.wait_until_open()
    assert modal.is_open()

    # Verify structure
    assert modal.dialog.is_displayed()
    assert modal.content.is_displayed()
    assert modal.header.is_displayed()
    assert modal.body.is_displayed()
    assert modal.footer.is_displayed()

    # Verify content
    assert modal.title.find().text == "Test Modal"
    assert "This is a test modal dialog." in modal.body.find().text

    # Close modal
    modal.close_button.find().click()
    modal.wait_until_closed()
    assert not modal.is_open()


@pytest.fixture
def open_modal(page):
    """Fixture to ensure modal is open."""
    modal = Modal(name="Test modal", id="testModal")

    page.execute_script("""
        var modal = new bootstrap.Modal(document.getElementById('testModal'));
        modal.show();
    """)
    modal.wait_until_open()

    yield modal

    if modal.is_open():
        page.execute_script("bootstrap.Modal.getInstance(document.getElementById('testModal')).hide()")
        modal.wait_until_closed()


def test_modal_buttons(open_modal):
    """Test modal buttons."""
    modal = open_modal

    # Get footer buttons
    footer_buttons = modal.footer.find().find_elements("xpath", ".//button")

    # Verify buttons
    assert len(footer_buttons) == 2
    assert footer_buttons[0].text.strip() == "Close"
    assert footer_buttons[1].text.strip() == "Save changes"

    # Click close button and verify modal closes
    footer_buttons[0].click()
    modal.wait_until_closed()
    assert not modal.is_open()
