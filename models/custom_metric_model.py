from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from models.base_model import Base


class CustomMetricModel(Base):
    """
    Model representing a custom metric associated with a test execution.

    @param id: Unique identifier of the custom metric
    @param test_execution_id: ID of the associated test execution
    @param name: Name/identifier of the metric
    @param value: Value of the metric (stored as JSON to support various data types)
    @param test_execution: Reference to the associated test execution record

    The value parameter can store various types of data:
    - Simple types: numbers, strings, booleans
    - Complex types: lists, dictionaries
    - Custom data structures (serialized to JSON)
    """
    __tablename__ = 'custom_metrics'

    id = Column(Integer, primary_key=True)
    test_execution_id = Column(Integer, ForeignKey('test_execution_records.id'))
    name = Column(String)
    value = Column(JSON)

    test_execution = relationship("TestExecutionRecordModel", back_populates="custom_metrics")

