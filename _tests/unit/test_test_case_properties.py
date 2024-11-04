import pytest

from core.exceptions import RequiredPropertyError, InvalidPropertyError, PropertyValidationError
from core.test_case import TestCase


class SimpleTestCase(TestCase):
    """Simple test case class for testing properties."""

    @property
    def test_suite(self) -> str:
        return "Test Suite"


def test_required_properties_missing(base_test_case):
    """Test handling of missing required properties."""
    with pytest.raises(RequiredPropertyError) as exc:
        SimpleTestCase(component="API")  # Missing required 'scope'

    assert "Required property 'SCOPE' is not set" in str(exc.value)


def test_invalid_property_names(base_test_case):
    """Test handling of invalid property names."""
    with pytest.raises(InvalidPropertyError) as exc:
        SimpleTestCase(
            scope="Backend",
            component="API",
            invalid_prop="Value"  # Invalid property
        )

    assert exc.value.property_name == "invalid_prop"
    assert "Valid properties are:" in str(exc.value)
    assert "scope" in exc.value.details['valid_properties']
    assert "component" in exc.value.details['valid_properties']


def test_property_type_validation(base_test_case):
    """Test property type validation."""
    # Test invalid scope type
    with pytest.raises(PropertyValidationError) as exc:
        SimpleTestCase(scope=123, component="API")

    assert exc.value.property_name == "SCOPE"
    assert exc.value.details['expected_type'] == "str"
    assert exc.value.details['actual_type'] == "int"

    # Test invalid component type
    with pytest.raises(PropertyValidationError) as exc:
        SimpleTestCase(scope="Backend", component=['API'])

    assert exc.value.property_name == "COMPONENT"
    assert exc.value.details['expected_type'] == "str"
    assert exc.value.details['actual_type'] == "list"


def test_optional_properties(base_test_case):
    """Test handling of optional properties."""
    # Test with only required properties
    test_case = SimpleTestCase(scope="Backend", component="API")
    assert test_case.scope == "Backend"
    assert test_case.component == "API"
    assert test_case.request_type is None
    assert test_case.interface is None

    # Test with optional properties
    test_case = SimpleTestCase(
        scope="Backend",
        component="API",
        request_type="GET",
        interface="REST"
    )
    assert test_case.request_type == "GET"
    assert test_case.interface == "REST"


def test_property_type_combinations(base_test_case):
    """Test different combinations of property types."""
    # Test with all properties as strings
    test_case = SimpleTestCase(
        scope="Backend",
        component="API",
        request_type="GET",
        interface="REST"
    )

    # Verify all properties
    assert test_case.scope == "Backend"
    assert test_case.component == "API"
    assert test_case.request_type == "GET"
    assert test_case.interface == "REST"

    # Test with required properties and None optionals
    test_case = SimpleTestCase(
        scope="Backend",
        component="API",
        request_type=None,
        interface=None
    )

    assert test_case.scope == "Backend"
    assert test_case.component == "API"
    assert test_case.request_type is None
    assert test_case.interface is None


def test_property_value_immutability(base_test_case):
    """Test properties immutability after initialization."""
    test_case = SimpleTestCase(scope="Backend", component="API")

    with pytest.raises(AttributeError):
        test_case.scope = "Frontend"

    with pytest.raises(AttributeError):
        test_case.component = "Database"


def test_property_case_sensitivity(base_test_case):
    """Test case-insensitive property handling."""
    # Test upper case properties
    test_case = SimpleTestCase(
        SCOPE="Backend",
        component="API",
        REQUEST_TYPE="GET",
        Interface="REST"
    )

    assert test_case.scope == "Backend"
    assert test_case.component == "API"
    assert test_case.request_type == "GET"
    assert test_case.interface == "REST"

    # Test mixed case properties
    test_case = SimpleTestCase(
        ScOpE="Backend",
        CoMpOnEnT="API",
        ReQuEsT_TyPe="GET",
        InTeRfAcE="REST"
    )

    assert test_case.scope == "Backend"
    assert test_case.component == "API"
    assert test_case.request_type == "GET"
    assert test_case.interface == "REST"