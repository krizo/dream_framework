import pytest
from datetime import datetime

from core.test_case import TestCase, TestCasePropertyError


class ConcreteTestCase(TestCase):
    @property
    def test_suite(self) -> str:
        return "Concrete Test Suite"


@pytest.fixture
def test_case():
    return ConcreteTestCase(scope="Backend", component="API")


def test_test_case_initialization(test_case):
    assert test_case.test_suite == "Concrete Test Suite"
    assert test_case.scope == "Backend"
    assert test_case.component == "API"


def test_only_required_properties_positive():
    test_case = ConcreteTestCase(scope="Backend", component="API")
    assert test_case, "Failed to initialize ConcreteTestCase with only required fields"


def test_required_properties_negative():
    with pytest.raises(TestCasePropertyError):
        ConcreteTestCase(scope="Backend")  # Missing 'component'


def test_not_specified_properties_negative():
    with pytest.raises(TestCasePropertyError):
        ConcreteTestCase(scope="Backend", component="API", invalid_property='foo')


def test_optional_properties():
    test_case = ConcreteTestCase(scope="Unit", component="API", request_type="GET", interface="REST")
    assert test_case.scope == "Unit"
    assert test_case.interface == "REST"


def test_property_type_checking_negative():
    with pytest.raises(TypeError):
        ConcreteTestCase(scope=123, component="API")


def test_to_dict():
    test_case = ConcreteTestCase(name="Test Name", description="Test Description", scope="Unit", component="API",
                                 request_type="GET", interface="REST")
    test_case.start_time = datetime(2023, 1, 1, 12, 0, 0)
    test_case.end_time = datetime(2023, 1, 1, 12, 0, 10)
    test_case.duration = 10.0

    test_dict = test_case.to_dict()

    assert test_dict['test_name'] == "Test Name"
    assert test_dict['test_description'] == "Test Description"
    assert test_dict['test_suite'] == "Concrete Test Suite"
    assert test_dict['request_type'] == "GET"
    assert test_dict['component'] == "API"
    assert test_dict['scope'] == "Unit"
    assert test_dict['start_time'] == "2023-01-01T12:00:00"
    assert test_dict['end_time'] == "2023-01-01T12:00:10"
    assert test_dict['duration'] == 10.0


def test_set_result_and_callbacks_success(test_case):
    success_called = False

    def on_success():
        """ Function to be called after test is successful """
        nonlocal success_called
        success_called = True

    test_case.add_on_success_callback(on_success)
    test_case.set_result(True)  # test passed

    assert success_called, "on_success() wasn't called after test passed successfully "


def test_set_result_and_callbacks_failure(test_case):
    failure_called = False

    def on_failure():
        nonlocal failure_called
        failure_called = True

    test_case.add_on_failure_callback(on_failure)

    assert not failure_called, "on_failure() wasn't called after test failed"
    test_case.set_result(False)  # Test failed
    assert failure_called


def test_extend_test_name_with_test_function_param(test_case):
    assert not test_case.extend_test_name_with_test_function_param


def test_user_stories_none(test_case):
    assert test_case.user_stories is None


def test_user_stories_true(test_case):
    test_case = ConcreteTestCase(name="Test with Stories", description="Test Description", component="API",
                                 scope='Backend', user_stories=[12345, 'https://example.com/123'])
    assert test_case.user_stories == [12345, 'https://example.com/123']
