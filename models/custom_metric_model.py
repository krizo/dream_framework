from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from models.base_model import Base


class CustomMetricModel(Base):
    """
    Model representing a custom metric for a test case.

    @param id: Unique identifier of the metric
    @param test_case_id: Identifier of the associated test case
    @param name: Name of the metric
    @param value: Value of the metric (stored as JSON for type flexibility)
    @param test_case: Associated test case
    """

    __tablename__ = 'custom_metrics'

    id = Column(Integer, primary_key=True)
    test_case_id = Column(Integer, ForeignKey('test_cases.id'))
    name = Column(String)
    value = Column(JSON)

    test_case = relationship("TestCaseModel", back_populates="custom_metrics")
