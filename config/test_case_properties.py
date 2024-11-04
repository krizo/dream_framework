from enum import Enum

from pydantic import BaseModel


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
    Custom test case properties configuration.

    This enum defines the properties that can be set for a test case, including
    their names, types, and whether they are required.
    Framework users can define their own properties here.
    """
    SCOPE = PropertyInfo(name="SCOPE", type=str, required=True)
    COMPONENT = PropertyInfo(name="COMPONENT", type=str, required=True)
    REQUEST_TYPE = PropertyInfo(name="REQUEST_TYPE", type=str, required=False)
    INTERFACE = PropertyInfo(name="INTERFACE", type=str, required=False)
