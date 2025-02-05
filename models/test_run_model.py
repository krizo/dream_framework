from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship

from models.base_model import Base


class TestRunModel(Base):
    """
    Model representing a single test suite execution.

    @param id: Unique identifier
    @param test_run_id: Unique test run identifier (from xdist or generated)
    @param test_type: Execution type (single/xdist/CI) 
    @param status: Test run status
    @param owner: Person executing the tests
    @param environment: Environment where tests were executed
    @param start_time: Test run start time
    @param end_time: Test run end time
    @param duration: Total duration in seconds
    @param report: Link to test report
    @param branch: Branch from which tests were executed 
    @param app_under_test: Name of the application under test
    @param app_version: Version of the tested application
    @param build_id: Build identifier (for CI)
    """
    __tablename__ = 'test_runs'

    id = Column(Integer, primary_key=True)
    test_run_id = Column(String(255), unique=True, nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # CI or SINGLE
    status = Column(String(50), nullable=False)  # STARTED, COMPLETED, CANCELLED, ERROR
    owner = Column(String(255), nullable=False)
    environment = Column(String(255))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)
    report = Column(String(1024))
    branch = Column(String(255))
    app_under_test = Column(String(255))
    app_version = Column(String(50))
    build_id = Column(String(255))

    # Relationships
    executions = relationship("TestExecutionRecordModel", back_populates="test_run")

    def __repr__(self) -> str:
        return f"<TestRun {self.test_run_id} ({self.status})>"
