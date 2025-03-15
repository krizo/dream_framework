from enum import Enum


class DataFormat(Enum):
    """Standard formats for output data"""
    DEFAULT = "default"
    UPPER = "upper"
    LOWER = "lower"
    TITLE = "title"
    SNAKE_CASE = "snake_case"
    CAMEL_CASE = "camel_case"
    PASCAL_CASE = "pascal_case"
    KEBAB_CASE = "kebab_case"
