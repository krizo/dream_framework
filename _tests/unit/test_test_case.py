import pytest

from core.exceptions import (
    RequiredPropertyError,
    InvalidPropertyError,
    PropertyValidationError,
    TestCaseError, InvalidScopeError
)
from core.test_case import TestCase


def test_test_case_initialization(base_test_case):
    """
    Test basic TestCase initialization with required properties.

    @param base_test_case: Basic TestCase fixture
    """
    assert base_test_case.name == "Sample Test"
    assert base_test_case.description == "Sample test description"
    assert base_test_case.test_suite == "Sample Suite"
    assert base_test_case.scope == "integration"
    assert base_test_case.component == "database"
    assert base_test_case.id is not None
    assert base_test_case.test_id is not None


def test_required_properties(base_test_case):
    """
    Test handling of required properties validation.

    @raises RequiredPropertyError: When required property is missing
    """
    # Test missing scope
    with pytest.raises(RequiredPropertyError) as exc_info:
        TestCase(
            name="Test",
            component="API"
        )
    assert exc_info.value.property_name == "SCOPE"

    # Test missing component
    with pytest.raises(RequiredPropertyError) as exc_info:
        TestCase(
            name="Test",
            scope="Unit"
        )
    assert exc_info.value.property_name == "COMPONENT"

    # Valid initialization should not raise
    TestCase(
        name="Test",
        scope="Unit",
        component="API"
    )


def test_invalid_property(base_test_case):
    """
    Test handling of invalid property names.

    @raises InvalidPropertyError: When invalid property name is provided
    """
    with pytest.raises(InvalidPropertyError) as exc_info:
        TestCase(
            name="Test",
            scope="Unit",
            component="API",
            invalid_property="Value"
        )
    assert exc_info.value.property_name == "invalid_property"
    assert "Valid properties are:" in str(exc_info.value)


def test_property_validation(base_test_case):
    """
    Test property type validation.

    @raises PropertyValidationError: When property value has invalid type
    """
    # Test invalid scope type
    with pytest.raises(InvalidScopeError) as exc_info:
        TestCase(
            name="Test",
            scope=123,  # Should be string
            component="API"
        )

    # Test invalid component type
    with pytest.raises(PropertyValidationError) as exc_info:
        TestCase(
            name="Test",
            scope="Unit",
            component=["API"]  # Should be string
        )


def test_optional_properties(base_test_case):
    """
    Test handling of optional properties.

    @param base_test_case: Basic TestCase fixture
    """
    test_case = TestCase(
        name="Test",
        scope="Unit",
        component="API",
        request_type="GET",
        interface="REST"
    )

    assert test_case.request_type == "GET"
    assert test_case.interface == "REST"

    # Optional properties should be None if not provided
    assert base_test_case.request_type is None
    assert base_test_case.interface is None


def test_test_location(base_test_case):
    """Test setting and getting test location information."""
    test_case = TestCase(
        name="Test",
        scope="Unit",
        component="API"
    )

    test_case.set_test_location("tests/test_api.py", "test_endpoint")

    assert test_case.test_module == "tests/test_api.py"
    assert test_case.test_function == "test_endpoint"
    assert test_case.test_id == "tests/test_api.py::test_endpoint"


def test_get_properties(base_test_case):
    """
    Test getting all test case properties.

    @param base_test_case: Basic TestCase fixture
    """
    base_test_case.set_test_location("module.py", "test_func")

    properties = base_test_case.get_properties()

    # Check required properties
    assert properties["name"] == "Sample Test"
    assert properties["scope"] == "integration"
    assert properties["component"] == "database"

    # Check test location properties
    assert properties["test_id"] == "module.py::test_func"
    assert properties["test_module"] == "module.py"
    assert properties["test_function"] == "test_func"

    # Optional properties should not be included if None
    assert "request_type" not in properties
    assert "interface" not in properties


def test_model_conversion(base_test_case):
    """
    Test conversion between TestCase and TestCaseModel.

    @param base_test_case: Basic TestCase fixture
    @raises TestCaseError: When converting to model without test_id
    """
    invalid_test_case = TestCase(
        name="Test",
        scope="Unit",
        component="API",
    )
    # Test conversion without test_id
    with pytest.raises(TestCaseError) as exc:
        invalid_test_case.to_model()

    # Set test location and try again
    base_test_case.set_test_location("module.py", "test_func")
    model = base_test_case.to_model()

    assert model.name == base_test_case.name
    assert model.test_id == base_test_case.test_id

    # Test conversion back to TestCase
    new_case = TestCase.from_model(model)
    assert new_case.name == base_test_case.name
    assert new_case.test_id == base_test_case.test_id


def test_user_stories(base_test_case):
    """Test handling of user stories property."""
    stories = ["US-123", "US-456"]
    test_case = TestCase(
        name="Test",
        scope="Unit",
        component="API",
        user_stories=stories
    )

    assert test_case.user_stories == stories
    assert "user_stories" in test_case.get_properties()
    assert test_case.get_properties()["user_stories"] == stories
