from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from models.base_model import Base


class TestExecutionRecordModel(Base):
    """
    Model representing a single test execution record in the database.
    
    @param id: Unique identifier
    @param test_case_id: ID of associated test case
    @param test_run_id: ID of associated test run
    @param test_module: Test module name
    @param test_function: Test function name
    @param name: Test name
    @param description: Test description
    @param result: Test result 
    @param start_time: Start time
    @param end_time: End time
    @param duration: Duration in seconds
    @param failure: Failure message if test failed
    @param failure_type: Type of failure
    @param environment: Test environment
    """
    __tablename__ = 'test_execution_records'
    __table_args__ = (
        UniqueConstraint('test_case_id', 'test_run_id', 'test_function', name='uq_test_execution'),
    )

    id = Column(Integer, primary_key=True)
    test_case_id = Column(Integer, ForeignKey('test_cases.id'), nullable=False)
    test_run_id = Column(String(255), ForeignKey('test_runs.test_run_id'), nullable=False)
    test_module = Column(String(255), nullable=False)
    test_function = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    result = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)
    failure = Column(Text, default="")
    failure_type = Column(String(255), default="")
    environment = Column(String(255))

    # Relationships
    test_case = relationship("TestCaseModel", back_populates="executions")
    test_run = relationship("TestRunModel", back_populates="executions")
    custom_metrics = relationship("CustomMetricModel", back_populates="test_execution", cascade="all, delete-orphan")
    steps = relationship("StepModel", back_populates="execution_record", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestExecution {self.id} ({self.result})>"
