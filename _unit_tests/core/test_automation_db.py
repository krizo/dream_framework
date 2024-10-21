import pytest
from sqlalchemy import inspect

from core.automation_database import AutomationDatabase
from models.test_case_model import TestCaseModel
from models.custom_metric_model import CustomMetricModel


@pytest.fixture(scope="module")
def db():
    """
    Fixture to create a test database.

    @return: AutomationDatabase instance
    """
    test_db = AutomationDatabase('sqlite:///:memory:')
    test_db.create_tables()
    return test_db


def test_database_initialization(db):
    """
    Test if the database is properly initialized.
    """
    assert db.engine is not None
    assert db.Session is not None


def test_create_tables(db):
    """
    Test if tables are created correctly.
    """
    inspector = inspect(db.engine)
    assert 'test_cases' in inspector.get_table_names()
    assert 'custom_metrics' in inspector.get_table_names()


def test_insert_and_query(db):
    """
    Test inserting a record and querying it.
    """
    test_case = TestCaseModel(test_name="Test 1", result=True)
    db.insert(test_case)

    queried_test = db.query(TestCaseModel).filter_by(test_name="Test 1").first()
    assert queried_test is not None
    assert queried_test.test_name == "Test 1"
    assert queried_test.result is True


def test_update(db):
    """
    Test updating a record.
    """
    test_case = db.query(TestCaseModel).filter_by(test_name="Test 1").first()
    test_case.result = False
    db.update(test_case)

    updated_test = db.query(TestCaseModel).filter_by(test_name="Test 1").first()
    assert updated_test.result is False


def test_delete(db):
    """
    Test deleting a record.
    """
    test_case = db.query(TestCaseModel).filter_by(test_name="Test 1").first()
    db.delete(test_case)

    deleted_test = db.query(TestCaseModel).filter_by(test_name="Test 1").first()
    assert deleted_test is None


def test_custom_metric(db):
    """
    Test creating a test case with a custom metric.
    """
    test_case = TestCaseModel(test_name="Test with Metric")
    metric = CustomMetricModel(name="Performance", value={"speed": 100})
    test_case.custom_metrics.append(metric)
    db.insert(test_case)

    # Query the test case and check if the metric was saved
    queried_test = db.query(TestCaseModel).filter_by(test_name="Test with Metric").first()

    assert queried_test is not None, "Test case was not saved"
    assert len(queried_test.custom_metrics) == 1, "Custom metric was not saved"
    assert queried_test.custom_metrics[0].name == "Performance", "Custom metric name is incorrect"
    assert queried_test.custom_metrics[0].value == {"speed": 100}, "Custom metric value is incorrect"

    # Query the custom metric directly
    queried_metric = db.query(CustomMetricModel).filter_by(name="Performance").first()
    assert queried_metric is not None, "Custom metric was not saved independently"
    assert queried_metric.test_case_id == queried_test.id, "Custom metric is not properly associated with test case"


def test_session_scope(db):
    """
    Test if session_scope properly manages transactions.
    """
    with pytest.raises(Exception):
        with db.session_scope() as session:
            test_case = TestCaseModel(test_name="Transaction Test")
            session.add(test_case)
            raise Exception("Simulated error")

    # The test case should not be in the database due to rollback
    assert db.query(TestCaseModel).filter_by(test_name="Transaction Test").first() is None

    # Test successful transaction
    with db.session_scope() as session:
        test_case = TestCaseModel(test_name="Successful Transaction")
        session.add(test_case)

    assert db.query(TestCaseModel).filter_by(test_name="Successful Transaction").first() is not None
