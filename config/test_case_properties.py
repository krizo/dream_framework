from pydantic import BaseModel
from enum import Enum


class PropertyInfo(BaseModel):
    """
    Represents information about a property in a test case.

    This class holds metadata about a property, including its name, type, and whether it's required.

    @param name: The name of the property.
    @param type: The expected type of the property value.
    @param required: Indicates whether the property is required.
    """
    name: str
    type: type
    required: bool


class TestCaseProperties(Enum):
    """
    Enumeration of test case properties.

    This enum defines the properties that can be set for a test case, including
    their names, types, and whether they are required.
    """
    SCOPE = PropertyInfo(name="SCOPE", type=str, required=True)
    COMPONENT = PropertyInfo(name="COMPONENT", type=str, required=True)
    REQUEST_TYPE = PropertyInfo(name="REQUEST_TYPE", type=str, required=False)
    INTERFACE = PropertyInfo(name="INTERFACE", type=str, required=False)

    @property
    def type(self) -> type:
        """
        Get the type of the property.

        @returns: The type of the property.
        """
        return self.value.type

    @property
    def required(self) -> bool:
        """
        Check if the property is required.

        @returns: True if the property is required, False otherwise.
        """
        return self.value.required
