from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from models.base_model import Base


class TestCaseModel(Base):
    """
    Model representing a test case in the database.

    @param id: Unique identifier of the test case
    @param test_id: Unique identifier based on module and function name
    @param test_module: Test module path
    @param test_function: Test function name
    @param name: Name of the test case
    @param description: Description of the test case
    @param test_suite: Name of the test suite
    @param executions: List of test execution records
    """
    __tablename__ = 'test_cases'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    test_id = Column(String(500), unique=True, nullable=False, index=True)
    test_module = Column(String(255), nullable=False)
    test_function = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_suite = Column(String(255))
    properties = Column(JSON)

    executions = relationship("TestExecutionRecordModel", back_populates="test_case",
                              cascade="all, delete-orphan")
