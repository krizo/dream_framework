from pathlib import Path
from typing import Union, List

from core.frontend.playwright.elements.ui_element import UIElement


class FileUploadElement(UIElement):
    """File upload element implementation."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize file upload element.

        @param name: Element name for logging
        @param kwargs: Locator arguments
        """
        super().__init__(name=name, expected_tag="input", **kwargs)

    def upload_files(self, files: Union[str, List[str], Path, List[Path]]) -> 'FileUploadElement':
        """
        Upload files to the input element.

        @param files: Path to file or list of paths
        @return: Self for method chaining
        """
        # Convert to list if a single file is provided
        if not isinstance(files, list):
            files = [files]

        # Convert all paths to strings
        file_paths = [str(f) for f in files]

        # Upload files
        self.get_locator().set_input_files(file_paths)

        return self