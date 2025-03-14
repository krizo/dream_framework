from typing import Union, List

from core.frontend.playwright.elements.input.input_element import InputElement


class FileInputElement(InputElement):
    """File input element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize file input element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, **kwargs)

    def set_input_files(self, files: Union[str, List[str]]) -> 'FileInputElement':
        """
        Set files to upload.

        @param files: Path to file or list of paths
        @return: Self for method chaining
        """
        self.get_locator().set_input_files(files)
        return self