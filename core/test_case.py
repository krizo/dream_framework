import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Callable, Optional, Any, Dict

from config.test_case_properties import TestCaseProperties


class TestCasePropertyError(Exception):
    """Exception raised when there's an error with test case properties."""


class TestCase(ABC):
    """
    Abstract base class for test cases.

    This class provides a framework for creating test cases with customizable properties,
    result tracking, and callback functionality.
    """

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None, **properties):
        """
        Initialize a new TestCase instance.

        @param name: Name of the test case.
        @param description: Description of the test case.
        @param properties: Additional properties for the test case, usually test metrics to be tracked.
        @raises TestCasePropertyError: If an invalid property is provided or a required property is missing.
        """
        self.id: Optional[str] = None
        self.test_run_id: Optional[str] = None
        self.test_name: str = name or ""
        self.test_description: str = description or ""
        self.failure: str = ""
        self.failure_type: str = ""
        self.result: Optional[bool] = None
        self.duration: Optional[float] = None
        self.test_function: Optional[str] = self._get_test_function()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.environment: Optional[str] = None
        self.test_type: Optional[str] = None
        self.on_success_callbacks: List[Callable[[], None]] = []
        self.on_failure_callbacks: List[Callable[[], None]] = []
        self._user_stories = None
        if properties.get('user_stories'):
            self._user_stories: Optional[List[str]] = properties.pop('user_stories')
        self._properties: Dict[str, Any] = {}
        self._initialize_properties(properties)

        for prop_name, prop_value in properties.items():
            setattr(self, prop_name.lower(), prop_value)

    @staticmethod
    def _get_test_function() -> Optional[str]:
        """
        Get the name of the current test function from the environment.

        @returns: The name of the current test function.
        """
        pytest_current_test = os.environ.get('PYTEST_CURRENT_TEST')
        if pytest_current_test:
            return pytest_current_test.split(':')[-1].split(' ')[0].split('@')[0]
        return None

    def _initialize_properties(self, properties: Dict[str, Any]):
        """
        Initialize dynamic properties based on TestCaseProperties and validate provided properties.

        @param properties: Dictionary of properties provided during initialization.
        @raises TestCasePropertyError: If an invalid property is provided or a required property is missing.
        """
        for prop in TestCaseProperties:
            prop_name = prop.name.lower()
            setattr(self.__class__, prop_name, property(
                fget=lambda self, _name=prop.name: self._get_property(_name),
                fset=lambda self, value, _name=prop.name: self._set_property(_name, value),
                doc=f"Property '{prop.name}' of type {prop.value.type.__name__}"
            ))

            if prop_name in properties:
                setattr(self, prop_name, properties[prop_name])
            elif prop.value.required:
                raise TestCasePropertyError(f"Required property '{prop.name}' is not set")

        # Check for invalid properties (not specified in TestCaseProperties)
        invalid_props = set(properties.keys()) - set(prop.name.lower() for prop in TestCaseProperties)
        if invalid_props:
            raise TestCasePropertyError(f"Invalid properties: {', '.join(invalid_props)}")

    def _get_property(self, name: str) -> Any:
        """
        Get the value of a test case property.

        @param name: The name of the property.
        @returns: The value of the property.
        """
        return self._properties.get(name)

    def _set_property(self, name: str, value: Any):
        """
        Set the value of a test case property.

        @param name: The name of the property.
        @param value: The value to set.x
        @raises TypeError: If the value is not of the expected type.
        """
        prop_info = TestCaseProperties[name].value
        if not isinstance(value, prop_info.type):
            raise TypeError(f"Property '{name}' must be of type {prop_info.type.__name__}")
        self._properties[name] = value

    @property
    @abstractmethod
    def test_suite(self) -> str:
        """
        Get the test suite name.

        @returns: The name of the test suite.
        """
        pass

    @property
    def user_stories(self) -> Optional[List[str]]:
        """
        Get the list of user stories covered by this test case.

        @returns: The list of user stories, or None if not set.
        """
        return self._user_stories

    @property
    def extend_test_name_with_test_function_param(self) -> bool:
        """
        Check if the test name should be extended with the test function parameter.

        @returns: True if the test name should be extended, False otherwise.
        """
        return False

    def set_result(self, result: bool) -> None:
        """
        Set the result of the test case and trigger appropriate callbacks.

        @param result: The result of the test case (True for pass, False for fail).
        """
        self.result = result
        if result:
            for callback in self.on_success_callbacks:
                callback()
        else:
            for callback in self.on_failure_callbacks:
                callback()

    def on_test_case_end_callback(self, callback: Callable[[], None]) -> None:
        """
        Add a callback to be executed when the test ends.

        @param callback: The callback function to add.
        """
        self.on_success_callbacks.append(callback)

    def to_dict(self) -> dict:
        """
        Convert the TestCase instance to a dictionary.

        @returns: A dictionary representation of the TestCase instance.
        """
        result = {
            "id": self.id,
            "test_run_id": self.test_run_id,
            "test_name": self.test_name,
            "test_description": self.test_description,
            "failure": self.failure,
            "failure_type": self.failure_type,
            "result": self.result,
            "duration": self.duration,
            "test_function": self.test_function,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "environment": self.environment,
            "test_type": self.test_type,
            "test_suite": self.test_suite,
            "user_stories": self.user_stories,
        }

        # Add dynamic properties to the dictionary
        for prop in TestCaseProperties:
            result[prop.name.lower()] = self._properties.get(prop.name)

        return result
