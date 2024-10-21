from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from models.base_model import Base


class TestCaseModel(Base):
    """
    Model representing a test case in the database.

    @param id: Unique identifier of the test case
    @param test_run_id: Identifier of the test run
    @param test_name: Name of the test
    @param test_description: Description of the test
    @param failure: Description of the test failure, if any
    @param failure_type: Type of failure
    @param result: Test result (True - success, False - failure)
    @param duration: Duration of the test in seconds
    @param test_function: Name of the test function
    @param start_time: Test start time
    @param end_time: Test end time
    @param environment: Environment in which the test was conducted
    @param test_type: Type of the test
    @param test_suite: Name of the test suite
    @param scope: Scope of the test
    @param component: Tested component
    @param request_type: Type of request (if applicable)
    @param interface: Interface on which the test was conducted
    @param custom_metrics: List of associated custom metrics
    """

    __tablename__ = 'test_cases'

    id = Column(Integer, primary_key=True)
    test_run_id = Column(String)
    test_name = Column(String)
    test_description = Column(String)
    failure = Column(String)
    failure_type = Column(String)
    result = Column(Boolean)
    duration = Column(Float)
    test_function = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    environment = Column(String)
    test_type = Column(String)
    test_suite = Column(String)
    scope = Column(String)
    component = Column(String)
    request_type = Column(String)
    interface = Column(String)

    custom_metrics = relationship("CustomMetricModel", back_populates="test_case", lazy="select")
