from enum import Enum


class LocatorType(Enum):
    """Types of element locators."""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ID = "id"
    CLASS = "_class"
    NAME = "name"
    TAG = "tag"
    ROLE = "role"
    TEST_ID = "data-testid"