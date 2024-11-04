# test_execution_record_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base_model import Base


class TestExecutionRecordModel(Base):
    """
    Model representing a single test execution record in the database.

    @param id: Unique identifier of the test execution
    @param test_case_id: ID of the associated test case
    @param test_run_id: Identifier for the test run session
    @param result: Execution result (True - success, False - failure)
    @param start_time: Time when the test execution started
    @param end_time: Time when the test execution ended
    @param failure: Description of the failure if the test failed
    @param failure_type: Type/classification of the failure
    @param duration: Test execution duration in seconds
    @param test_function: Name of the test function that was executed
    @param test_module: Name of the test module containing the test
    @param environment: Environment in which the test was executed
    @param test_case: Reference to the associated test case
    @param custom_metrics: List of custom metrics recorded during execution
    """
    __tablename__ = 'test_execution_records'

    id = Column(Integer, primary_key=True)
    test_case_id = Column(Integer, ForeignKey('test_cases.id'))
    test_run_id = Column(String)
    test_module = Column(String)
    test_function = Column(String)
    name = Column(Text)
    description = Column(Text)
    result = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)
    failure = Column(String)
    failure_type = Column(String)
    environment = Column(String)

    test_case = relationship("TestCaseModel", back_populates="executions")
    custom_metrics = relationship("CustomMetricModel", back_populates="test_execution",
                                  cascade="all, delete-orphan")
