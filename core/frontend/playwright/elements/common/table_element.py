from typing import List

from playwright.sync_api import Locator

from core.frontend.playwright.elements.ui_element import UIElement


class TableElement(UIElement):
    """Table element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize table element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="table", **kwargs)

    def click_row(self, row: int):
        """
        Clicks a row element.
        """
        return self.get_locator().locator("tbody tr").nth(row).click()

    def get_row_count(self) -> int:
        """
        Get number of rows in the table.

        @return: Number of rows
        """
        return self.get_locator().locator("tbody tr").count()

    def get_cell_text(self, row: int, col: int) -> str:
        """
        Get text from specific cell.

        @param row: Row index (0-based)
        @param col: Column index (0-based)
        @return: Cell text
        """
        # Select row then column
        return self.get_locator().locator("tbody tr").nth(row).locator("td").nth(col).text_content() or ""

    def get_header_text(self, col: int) -> str:
        """
        Get text from specific header cell.

        @param col: Column index (0-based)
        @return: Header cell text
        """
        return self.get_locator().locator("thead th").nth(col).text_content() or ""

    def get_row_data(self, row: int) -> List[str]:
        """
        Get all cell data from a row.

        @return: List of cell texts
        """
        row_locator = self.get_locator().locator("tbody tr").nth(row)
        cell_count = row_locator.locator("td").count()

        return [row_locator.locator("td").nth(i).text_content() or "" for i in range(cell_count)]

    def get_table_data(self) -> List[List[str]]:
        """
        Get all data from the table as a 2D array.

        @return: 2D array of cell texts
        """
        rows = self.get_row_count()
        data = []

        for row_idx in range(rows):
            data.append(self.get_row_data(row_idx))

        return data