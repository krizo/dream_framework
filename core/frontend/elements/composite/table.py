"""Table element implementations."""
from typing import List, Optional

from core.frontend.elements.base_element import BaseElement


class TableCell(BaseElement):
    """Table cell (td/th) element implementation."""

    def __init__(self, name: str, is_header: bool = False, **kwargs):
        """
        Initialize table cell.

        @param name: Cell name
        @param is_header: True if cell is header (th), False for standard cell (td)
        @param kwargs: Additional locator arguments
        """
        expected_tag = "th" if is_header else "td"
        super().__init__(name=name, expected_tag=expected_tag, **kwargs)


class TableRow(BaseElement):
    """Table row element implementation."""

    def __init__(self, name: str, cells: Optional[List[TableCell]] = None, **kwargs):
        """
        Initialize table row.

        @param name: Row name
        @param cells: List of cells in row
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, expected_tag="tr", **kwargs)
        self.cells = cells or []


class Table(BaseElement):
    """Table element implementation."""

    def __init__(self,
                 name: str,
                 has_header: bool = True,
                 **kwargs):
        """
        Initialize table element.

        @param name: Table name
        @param has_header: Whether table has header row
        @param kwargs: Additional locator arguments
        """
        super().__init__(name=name, expected_tag="table", **kwargs)
        self.has_header = has_header

        # Define header and body locators
        if self.has_header:
            self.header = TableRow(
                name=f"{name} header",
                xpath=".//thead/tr",
                parent=self
            )

        self.body = BaseElement(
            name=f"{name} body",
            xpath=".//tbody",
            expected_tag="tbody",
            parent=self
        )