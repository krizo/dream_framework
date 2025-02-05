from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from models.base_model import Base


class StepModel(Base):
    """
    Model representing a test step in the database.
    Steps can be nested (parent-child relationship) and are associated with test executions.

    @param id: Unique identifier of the step
    @param step_id: Unique step identifier based on timestamp
    @param sequence_number: Order number of the step in test execution
    @param parent_step_id: ID of the parent step (None for root steps)
    @param step_function: Name of the step function
    @param content: Step description/content
    @param execution_record_id: ID of the associated test execution
    @param test_function: Name of the test function that initiated the step
    @param completed: Indicates if step was completed successfully
    @param start_time: Timestamp when the step was started
    """
    __tablename__ = 'steps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_id = Column(String(50), nullable=False, unique=True)
    sequence_number = Column(Integer, nullable=False)
    hierarchical_number = Column(String(50), nullable=False)  # e.g., "1.2.3"
    indent_level = Column(Integer, nullable=False)  # Nesting depth
    parent_step_id = Column(Integer, ForeignKey('steps.id'), nullable=True)
    step_function = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    execution_record_id = Column(Integer, ForeignKey('test_execution_records.id'), nullable=False)
    test_function = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=False)


    # Relationships
    parent_step = relationship("StepModel", remote_side=[id], backref="child_steps")
    execution_record = relationship("TestExecutionRecordModel", back_populates="steps")

    def __repr__(self):
        return f"<Step {self.step_id}: {self.step_function}>"