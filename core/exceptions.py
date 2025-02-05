# exceptions.py
from typing import Optional


class TestCaseError(Exception):
    """Base exception class for all test case related errors."""
    pass


class TestCasePropertyError(TestCaseError):
    """
    Exception raised when there's an error with test case properties.

    @param message: Error message
    @param property_name: Name of the property that caused the error
    @param details: Additional error details
    """

    def __init__(self, message: str, property_name: Optional[str] = None, details: Optional[dict] = None):
        self.property_name = property_name
        self.details = details or {}
        super().__init__(message)


class PropertyValidationError(TestCasePropertyError):
    """
    Exception raised when property validation fails.

    @param property_name: Name of the invalid property
    @param expected_type: Expected property type
    @param actual_type: Actual property type
    @param value: The invalid value
    """

    def __init__(self, property_name: str, expected_type: type, actual_type: type, value: any):
        message = (f"Invalid type for property '{property_name}'. "
                   f"Expected {expected_type.__name__}, got {actual_type.__name__}")
        details = {
            'expected_type': expected_type.__name__,
            'actual_type': actual_type.__name__,
            'value': str(value)
        }
        super().__init__(message, property_name, details)


class RequiredPropertyError(TestCasePropertyError):
    """
    Exception raised when a required property is missing.

    @param property_name: Name of the missing property
    """

    def __init__(self, property_name: str):
        message = f"Required property '{property_name}' is not set"
        super().__init__(message, property_name)


class InvalidPropertyError(TestCasePropertyError):
    """
    Exception raised when an invalid property is provided.

    @param property_name: Name of the invalid property
    @param valid_properties: List of valid property names
    """

    def __init__(self, property_name: str, valid_properties: list[str]):
        message = f"Invalid property '{property_name}'. Valid properties are: {', '.join(valid_properties)}"
        details = {'valid_properties': valid_properties}
        super().__init__(message, property_name, details)


class InvalidScopeError(TestCaseError):
    """
    Exception raised when an invalid scope is provided.

    @param scope_name: Name of the invalid property
    @param valid_scopes: List of valid property names
    """

    def __init__(self, scope_name: str, valid_scopes: set[str]):
        message = "Invalid scope."
        details = f"Valid scopes are: {', '.join(valid_scopes)}"
        super().__init__(message, scope_name, details)
