# Test Framework

## Overview
This Test Framework provides a flexible solution for creating, managing, and tracking test cases in Python. 
It's designed to allow easy customization of test metrics, enabling users to capture and analyze diverse aspects of their tests.

## Key Features
- Customizable test metrics through `TestCaseProperties`
- Built-in and user-defined test attributes
- Flexible test case creation and management
- Support for test result tracking and reporting

## Main Components

### TestCase Class
The `TestCase` class serves as the foundation for creating specific tests. It manages both built-in and user-defined test metrics.

#### Built-in Metrics
- `test_name`: Name of the test case
- `test_description`: Description of the test case
- `result`: Boolean indicating test pass/fail status
- `start_time` and `end_time`: Timestamps for test execution
- `duration`: Test execution duration

### TestCaseProperties
The `TestCaseProperties` class is an enumeration that defines the available test metrics (both required or optional) 
for your test cases. It works in conjunction with the `TestCase` class to provide a flexible way of defining 
and using custom test metrics.

#### Default Properties
```python
class TestCaseProperties(Enum):
    SCOPE = PropertyInfo(name="SCOPE", type=str, required=True)
    COMPONENT = PropertyInfo(name="COMPONENT", type=str, required=True)
    REQUEST_TYPE = PropertyInfo(name="REQUEST_TYPE", type=str, required=False)
    INTERFACE = PropertyInfo(name="INTERFACE", type=str, required=False)
```

## Using TestCaseProperties with TestCase

### Defining Custom Metrics
To define custom metrics for your tests, modify the `TestCaseProperties` enum:

```python
from enum import Enum
from pydantic import BaseModel

class PropertyInfo(BaseModel):
    name: str
    type: type
    required: bool

class TestCaseProperties(Enum):
    SCOPE = PropertyInfo(name="SCOPE", type=str, required=True)
    COMPONENT = PropertyInfo(name="COMPONENT", type=str, required=True)
    REQUEST_TYPE = PropertyInfo(name="REQUEST_TYPE", type=str, required=False)
    INTERFACE = PropertyInfo(name="INTERFACE", type=str, required=False)
    PERFORMANCE_THRESHOLD = PropertyInfo(name="PERFORMANCE_THRESHOLD", type=float, required=False)
    DATA_SIZE = PropertyInfo(name="DATA_SIZE", type=int, required=False)
```

### Creating a Test Case with Custom Metrics

```python
from core.test_case import TestCase

class MyPerformanceTest(TestCase):
    @property
    def test_suite(self) -> str:
        return "Performance Test Suite"

# Initialize the test case with custom metrics
test = MyPerformanceTest(
    name="Database Query Performance",
    description="Verify query execution time for large datasets",
    scope="Performance",
    component="DatabaseService",
    performance_threshold=0.5,
    data_size=1000000
)


### Validating Required Properties
The `TestCase` class automatically validates that all required properties (as defined in `TestCaseProperties`) 
are set during initialization. If a required property is missing, a `TestCasePropertyError` will be raised:

```python
try:
    invalid_test = MyPerformanceTest(name="Invalid Test", scope="Performance")  # Missing required 'component'
except TestCasePropertyError as e:
    print(f"Error: {e}")  # Output: Error: Required property 'COMPONENT' is not set
```

### Modifying Metrics at Runtime
You can modify test metrics after the test case is created:

```python
test.request_type = "POST"
test.performance_threshold = 0.75

print(f"Updated Request Type: {test.request_type}")
print(f"Updated Performance Threshold: {test.performance_threshold}")
```

## Best Practices
1. Define all possible test metrics in `TestCaseProperties`, even if they're not always used.
2. Use descriptive names for custom metrics to enhance readability and maintainability.
3. Consider which metrics should be required vs. optional based on your testing needs.
