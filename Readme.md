# Test Framework

## Overview

This Test Framework provides a flexible solution for creating, managing, and tracking test cases in Python.
It's designed to allow easy customization of test metrics, enabling users to capture and analyze diverse aspects of
their tests.
The framework also supports persistent storage of test cases in various database systems.

## Key Features

- Customizable test metrics through `TestCaseProperties`
- Built-in and user-defined test attributes
- Flexible test case creation and management
- Support for test result tracking and reporting
- Database persistence with support for multiple database dialects
- Automatic test case serialization and deserialization

## Main Components

### TestCase Class

The `TestCase` class serves as the foundation for creating specific tests. It manages both built-in and user-defined
test metrics.

#### Built-in Metrics

- `test_name`: Name of the test case
- `test_description`: Description of the test case
- `result`: Boolean indicating test pass/fail status
- `start_time` and `end_time`: Timestamps for test execution
- `duration`: Test execution duration
- `custom_metrics`: List of custom metrics for flexible data storage

### TestCaseProperties

The `TestCaseProperties` class is an enumeration that defines the available test metrics (both required or optional)
for your test cases. It works in conjunction with the `TestCase` class to provide a flexible way of defining
and using custom test metrics.

```yaml
automation_db:
  url: "sqlite:///automation.db"
  dialect: null

# Example configurations for different environments
dev:
  url: "mssql+pyodbc://user:pass@server/database"
  dialect: "mssql"

test:
  url: "sqlite:///:memory:"
  dialect: null
```

### AutomationDatabaseManager

The framework provides a singleton database manager for centralized database access:

```python
from core.automation_database_manager import AutomationDatabaseManager

# Initialize with direct connection string
AutomationDatabaseManager.initialize('sqlite:///test.db')

# Initialize with configuration file
AutomationDatabaseManager.initialize(config_path='config/database.yaml')

# Get database instance
db = AutomationDatabaseManager.get_database()

# Check initialization status
if AutomationDatabaseManager.is_initialized():
    config = AutomationDatabaseManager.get_config()
```

## Pytest Integration

### Automatic Test Case Persistence

The framework includes a pytest plugin that automatically handles test case persistence:

```python
class MyTest(TestCase):
    def __init__(self):
        super().__init__(
            name="Test Name",
            description="Test Description",
            test_suite="MySuite",
            component="MyComponent",
            scope="Integration"
        )


def test_example(my_test_fixture):
    # Test case is automatically persisted before test execution
    my_test_fixture.add_custom_metric("metric_name", "value")

    # Test execution...

    # Test results and metrics are automatically updated after test completion
```

```

### Supported Database Dialects
The framework supports multiple database dialects through ODBC connections:
- Microsoft SQL Server
- Oracle
- MySQL
- PostgreSQL

Example of using different dialects:
```python
# MSSQL
db_mssql = AutomationDatabase('mssql+pyodbc://user:pass@server/database', dialect='mssql')

# Oracle
db_oracle = AutomationDatabase('oracle+cx_oracle://user:pass@server/database', dialect='oracle')

# MySQL
db_mysql = AutomationDatabase('mysql+pymysql://user:pass@server/database', dialect='mysql')

# PostgreSQL
db_postgres = AutomationDatabase('postgresql+psycopg2://user:pass@server/database', dialect='postgresql')
```

### Data Persistence

All test case data, including custom metrics and properties, is automatically persisted to the database. The framework
handles:

- Serialization of complex data types
- Automatic type conversion for different database dialects
- Relationship management between test cases and their custom metrics

## Logging System

The framework includes a flexible logging system that supports various log levels and formatting options.

### Log Levels

- `EMPTY`: For clean separators without timestamps
- `DEBUG`: Detailed debugging information
- `CONSOLE`: Console-only output
- `INFO`: General information
- `STEP`: Test step information (high visibility)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

### Basic Usage

```python
from core.logger import Log

# Basic logging
Log.info("General information message")
Log.step("Important test step")
Log.error("Error occurred")

# Visual separators (without timestamps)
Log.separator()  # Default: ----------------
Log.separator('=')  # Custom: ================
Log.separator('*', 50)  # With length: **************************************************


# Test steps tracking
def test_example():
    Log.step("Preparing test data")  # Step 1: Preparing test data
    Log.step("Executing main test")  # Step 2: Executing main test
    Log.step("Validating results")  # Step 3: Validating results
```

### Output Examples

```
--------------------------------------------------------------------------------
2024-10-24 15:49:42 | STEP     | Step 1: Preparing test data
2024-10-24 15:49:42 | INFO     | Test data initialized
================================================================================
2024-10-24 15:49:43 | STEP     | Step 2: Executing main test
2024-10-24 15:49:44 | ERROR    | Test duration: 1m 30s 200ms
```

### Configuration

The logging system uses a configuration file (`config/logger.ini`) that can be customized to adjust:

- Log file locations and naming patterns
- Output formatting
- Log levels visibility
- Console and file output settings

## Best Practices

1. Define all possible test metrics in `TestCaseProperties`, even if they're not always used.
2. Use descriptive names for custom metrics to enhance readability and maintainability.
3. Consider which metrics should be required vs. optional based on your testing needs.
4. Use appropriate database dialect for your environment.
5. Implement proper error handling for database operations.
6. Regularly clean up old test data to maintain database performance.