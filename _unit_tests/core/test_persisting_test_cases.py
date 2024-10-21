import pytest
from datetime import datetime, timedelta
from typing import Generator

from config.test_case_properties import TestCaseProperties
from core.automation_database import AutomationDatabase
from core.test_case import TestCase
from models.custom_metric_model import CustomMetricModel
from models.test_case_model import TestCaseModel


@pytest.fixture(scope="module")
def sqlite_db() -> AutomationDatabase:
    """
    Fixture that creates an in-memory SQLite database for testing.

    @return: An instance of AutomationDatabase using SQLite.
    """
    test_db = AutomationDatabase('sqlite:///:memory:')
    test_db.create_tables()
    return test_db


@pytest.fixture(scope="module", params=['mssql', 'oracle', 'mysql'])
def emulated_odbc_db(request: pytest.FixtureRequest) -> AutomationDatabase:
    """
    Fixture that creates an in-memory SQLite database emulating different ODBC dialects.

    @param request: Pytest request object containing the database dialect parameter.
    @return: An instance of AutomationDatabase emulating the specified ODBC dialect.
    """
    test_db = AutomationDatabase('sqlite:///:memory:', dialect=request.param)
    test_db.create_tables()
    return test_db


@pytest.fixture
def test_case() -> TestCase:
    """
    Fixture that creates a sample TestCase instance for testing.

    @return: An instance of TestCase with predefined properties.
    """
    return TestCase(name="Sample Test", description="This is a sample test", test_suite="Integration",
                    scope="core", component="database")


def test_test_case_creation(test_case: TestCase):
    """
    Test the creation of a TestCase instance and verify its initial state.
    """
    assert test_case.test_name == "Sample Test"
    assert test_case.test_description == "This is a sample test"
    assert test_case.result is None
    assert test_case.start_time is None
    assert test_case.end_time is None
    assert len(test_case.custom_metrics) == 2
    assert test_case.scope == "core"
    assert test_case.component == "database"


def test_custom_metrics(test_case: TestCase):
    """
    Test the addition and retrieval of custom metrics in a TestCase.
    """
    initial_metrics_count = len(test_case.custom_metrics)
    test_case.add_custom_metric("performance", 100)
    test_case.add_custom_metric("coverage", 0.85)

    assert len(test_case.custom_metrics) == initial_metrics_count + 2
    assert {"name": "scope", "value": "core"} in test_case.custom_metrics
    assert {"name": "component", "value": "database"} in test_case.custom_metrics
    assert {"name": "performance", "value": 100} in test_case.custom_metrics
    assert {"name": "coverage", "value": 0.85} in test_case.custom_metrics


def test_to_model(test_case: TestCase):
    """
    Test the conversion of a TestCase instance to a TestCaseModel.
    """
    test_case.start()
    test_case.add_custom_metric("metric1", "value1")
    test_case.end(False)

    model = test_case.to_model()
    assert isinstance(model, TestCaseModel)
    assert model.test_name == test_case.test_name
    assert model.test_description == test_case.test_description
    assert model.result is False

    expected_metrics_count = len(TestCaseProperties) + 1  # +1 for the additional custom metric
    assert len(model.custom_metrics) == expected_metrics_count

    metric_dict = {m.name: m.value for m in model.custom_metrics}
    assert metric_dict["scope"] == "core"
    assert metric_dict["component"] == "database"
    assert metric_dict["metric1"] == "value1"


def test_from_model(test_case: TestCase):
    """
    Test the creation of a TestCase instance from a TestCaseModel.
    """
    model = TestCaseModel(
        test_name=test_case.test_name,
        test_description=test_case.test_description,
        test_suite=test_case.test_suite,
        result=True,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(seconds=10)
    )

    for prop in TestCaseProperties:
        prop_name = prop.name.lower()
        prop_value = getattr(test_case, prop_name, None)
        if prop_value is not None:
            model.custom_metrics.append(CustomMetricModel(name=prop_name, value=prop_value))

    model.custom_metrics.append(CustomMetricModel(name="additional_metric", value="test_value"))

    test_case_from_model = TestCase.from_model(model)
    assert isinstance(test_case_from_model, TestCase)
    assert test_case_from_model.test_name == test_case.test_name
    assert test_case_from_model.test_description == test_case.test_description
    assert test_case_from_model.test_suite == test_case.test_suite
    assert test_case_from_model.result is True

    for prop in TestCaseProperties:
        prop_name = prop.name.lower()
        assert getattr(test_case_from_model, prop_name) == getattr(test_case, prop_name)

    assert any(metric["name"] == "additional_metric" and metric["value"] == "test_value"
               for metric in test_case_from_model.custom_metrics)


def test_sqlite_database_integration(sqlite_db: AutomationDatabase, test_case: TestCase):
    """
    Test the integration of TestCase with a SQLite database.

    @param sqlite_db: The SQLite database fixture.
    @param test_case: The TestCase fixture.
    """
    _test_database_integration(sqlite_db, test_case)


def test_emulated_odbc_database_integration(emulated_odbc_db: AutomationDatabase, test_case: TestCase):
    """
    Test the integration of TestCase with emulated ODBC databases.

    @param emulated_odbc_db: The emulated ODBC database fixture.
    @param test_case: The TestCase fixture.
    """
    _test_database_integration(emulated_odbc_db, test_case)


def _test_database_integration(db: AutomationDatabase, test_case: TestCase):
    """
    Helper function to test database integration for both SQLite and emulated ODBC databases.

    @param db: The database fixture (either SQLite or emulated ODBC).
    @param test_case: The TestCase fixture.
    """
    test_case.start()
    test_case.add_custom_metric("db_metric", "db_value")
    test_case.end(True)

    model = test_case.to_model()
    db.insert(model)

    # Retrieve the TestCase from the database
    retrieved_model = db.query(TestCaseModel).filter_by(test_name=test_case.test_name).first()
    retrieved_test_case = TestCase.from_model(retrieved_model)

    assert retrieved_test_case.test_name == test_case.test_name
    assert retrieved_test_case.test_description == test_case.test_description
    assert retrieved_test_case.result is True

    # Check TestCaseProperties
    for prop in TestCaseProperties:
        prop_name = prop.name.lower()
        assert getattr(retrieved_test_case, prop_name) == getattr(test_case, prop_name)

    # Check custom metric
    assert any(metric["name"] == "db_metric" and metric["value"] == "db_value"
               for metric in retrieved_test_case.custom_metrics)