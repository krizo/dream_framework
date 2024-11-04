from typing import Optional, List, Dict, Any

from config.test_case_properties import TestCaseProperties
from core.exceptions import (
    InvalidPropertyError,
    RequiredPropertyError,
    PropertyValidationError,
    TestCaseError
)
from core.logger import Log
from models.test_case_model import TestCaseModel


class TestCase:
    """
    Represents a test case definition with its core properties and location information.
    Custom metrics are handled by TestExecutionRecord.
    """

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None,
                 test_suite: str = None, **properties):
        """
        Initialize TestCase with core properties.

        @param name: Test case name
        @param description: Test case description
        @param test_suite: Test suite name
        @param properties: Additional properties defined in TestCaseProperties
        @raises TestCasePropertyError: If required properties are missing or invalid
        @raises PropertyValidationError: If property values have invalid types
        """
        # Standard properties - built into framework
        self.id: Optional[int] = None

        # Test location properties
        self._test_module: Optional[str] = None
        self._test_function: Optional[str] = None
        self.name: str = name or ""
        self.description: str = description or ""
        self._test_suite = test_suite
        self._test_id: Optional[str] = None

        # Handle user stories separately
        self._user_stories: Optional[List[str]] = None
        if 'user_stories' in properties:
            self._user_stories = properties.pop('user_stories')

        # Validate and store properties
        self._validate_properties(properties)
        self._properties: Dict[str, Any] = {}
        self._validate_properties(properties)
        self._execution_record = None
        for prop_name, value in properties.items():
            self._set_property(prop_name.upper(), value)

    @staticmethod
    def _validate_properties(properties: Dict[str, Any]):
        """
        Validate all provided properties against TestCaseProperties definitions.

        @param properties: Dictionary of property names and values to validate
        @raises TestCasePropertyError: If required properties are missing or invalid
        @raises PropertyValidationError: If property values have invalid types
        """
        valid_props = {prop.name.lower() for prop in TestCaseProperties}
        invalid_props = set(k.lower() for k in properties.keys()) - valid_props
        if invalid_props:
            raise InvalidPropertyError(next(iter(invalid_props)), list(valid_props))

        for prop in TestCaseProperties:
            if prop.value.required and prop.name.lower() not in {k.lower() for k in properties.keys()}:
                raise RequiredPropertyError(prop.name)

    def _get_property(self, name: str) -> Any:
        """
        Get property value.

        @param name: Property name
        @return: Property value or None if not set
        """
        return self._properties.get(name)

    def _set_property(self, name: str, value: Any):
        """
        Set property value with type validation.

        @param name: Property name
        @param value: Property value
        @raises PropertyValidationError: If value type doesn't match property definition
        """
        prop_info = TestCaseProperties[name].value

        if value is None and not prop_info.required:
            self._properties[name] = None
            return

        if not isinstance(value, prop_info.type):
            raise PropertyValidationError(name, prop_info.type, type(value), value)
        self._properties[name] = value

    def get_properties(self) -> Dict[str, Any]:
        """
        Get all test case properties and metadata.

        @return: Dictionary of all properties and test case metadata
        """
        properties = {}

        # Add base test information
        if self.test_id:
            properties.update({
                'test_id': self.test_id,
                'test_module': self.test_module,
                'test_function': self.test_function,
            })

        # Add core properties
        core_props = {
            'name': self.name,
            'description': self.description,
            'test_suite': self.test_suite,
        }
        properties.update({k: v for k, v in core_props.items() if v is not None})

        # Add TestCaseProperties
        for prop in TestCaseProperties:
            prop_name = prop.name.lower()
            prop_value = self._get_property(prop.name)
            if prop_value is not None:
                properties[prop_name] = prop_value

        # Add user stories if present
        if self.user_stories:
            properties['user_stories'] = self.user_stories

        return properties

    @property
    def test_module(self) -> Optional[str]:
        """Get test module path."""
        return self._test_module

    @test_module.setter
    def test_module(self, value: str):
        """
        Set test module path and update test_id.
        
        @param value: Module path
        """
        self._test_module = value
        self._update_test_id()

    @property
    def test_function(self) -> Optional[str]:
        """Get test function name."""
        return self._test_function

    @test_function.setter
    def test_function(self, value: str):
        """
        Set test function name and update test_id.
        
        @param value: Function name
        """
        self._test_function = value
        self._update_test_id()

    @property
    def test_id(self) -> Optional[str]:
        """Get unique test identifier."""
        return self._test_id

    def _update_test_id(self):
        """Update test_id based on module and function names."""
        if self._test_module and self._test_function:
            self._test_id = f"{self._test_module}::{self._test_function}"

    def set_execution_record(self, record: 'TestExecutionRecord'):
        """
        Set current test execution record.
        Called by the plugin when test starts.

        @param record: Current test execution record
        """
        self._execution_record = record

    def set_test_location(self, module: str, function: str):
        """
        Set test location information.

        @param module: Test module path
        @param function: Test function name
        """
        self.test_module = module
        self.test_function = function
        Log.info(f"Test location: {self.test_id}")
        Log.info(f"Test name: {self.name}")
        Log.info(f"Test description: {self.description}")
        Log.info(f"Test suite: {self.test_suite}")

    def get_custom_properties(self) -> Dict[str, Any]:
        """
        Get only custom properties defined in TestCaseProperties.

        @return: Dictionary of custom property names and values
        """
        return self._properties.copy()

    def add_custom_metric(self, name: str, value: Any):
        """
        Add custom metric during test execution.

        @param name: Metric name
        @param value: Metric value
        """
        if not hasattr(self, '_execution_record') or not self._execution_record:
            Log.warning(f"No active test execution found when adding metric: {name}")
            return

        self._execution_record.add_custom_metric(name, value)

    @property
    def test_suite(self) -> str:
        """Get test suite name."""
        return self._test_suite

    @property
    def user_stories(self) -> Optional[List[str]]:
        """Get associated user stories."""
        return self._user_stories

    # Property getters for TestCaseProperties
    for prop in TestCaseProperties:
        prop_name = prop.name.lower()
        locals()[prop_name] = property(
            lambda self, _name=prop.name: self._get_property(_name),
            doc=f"Get {prop.name} property value"
        )

    def to_model(self) -> TestCaseModel:
        """
        Convert to database model.

        @return: TestCaseModel instance
        @raises TestCaseError: If test_id is not set
        """
        if not self.test_id:
            raise TestCaseError("Cannot create model without test_id (module and function must be set)")

        return TestCaseModel(
            id=self.id,
            test_id=self.test_id,
            test_module=self.test_module,
            test_function=self.test_function,
            name=self.name,
            description=self.description,
            test_suite=self.test_suite,
            properties=self._properties  # Wszystkie właściwości w jednym polu JSON
        )

    @classmethod
    def from_model(cls, model: TestCaseModel) -> Optional['TestCase']:
        """
        Create TestCase instance from database model.

        @param model: TestCaseModel instance
        @return: TestCase instance with properties mapped from model
        """
        if model is None:
            return None

        # Create instance with base properties
        test_case = cls(
            name=model.name,
            description=model.description,
            test_suite=model.test_suite,
            **model.properties  # Unpack custom properties from json
        )
        test_case.id = model.id
        test_case.set_test_location(model.test_module, model.test_function)

        return test_case
