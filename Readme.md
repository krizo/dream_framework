# Test Framework

## Overview
This Test Framework provides a flexible solution for creating, managing, and tracking test cases in Python. 
It's designed to allow easy customization of test metrics, enabling users to capture and analyze diverse aspects of their tests.
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
The `TestCase` class serves as the foundation for creating specific tests. It manages both built-in and user-defined test metrics.

#### Built-in Metrics
- `test_name`: Name of the test case
- `test_description`: Description of the test case
- `result`: Boolean indicating test pass/fail status
- `start_time` and `end_time`: Timestamps for test execution
- `duration`: Test execution duration
- `custom_metrics`: List of custom metrics for flexible data storage

### TestCaseProperties
[Previous TestCaseProperties content remains unchanged]

## Database Integration

### AutomationDatabase Class
The framework provides database integration through the `AutomationDatabase` class, which supports various database dialects.

```python
from core.automation_database import AutomationDatabase

# Initialize with SQLite
db = AutomationDatabase('sqlite:///tests.db')

# Initialize with ODBC connection
db = AutomationDatabase('connection_string', dialect='mssql')
```

### Supported Database Operations

#### Inserting Test Cases
```python
test_case = MyPerformanceTest(
    name="Database Query Performance",
    description="Verify query execution time",
    scope="Performance",
    component="DatabaseService"
)

# Insert test case and get its ID
test_case_id = db.insert_test_case(test_case)
```

#### Fetching Test Cases
```python
# Retrieve a test case by ID
retrieved_test_case = db.fetch_test_case(test_case_id)
```

#### Updating Test Cases
```python
test_case.result = True
update_success = db.update_test_case(test_case)
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
All test case data, including custom metrics and properties, is automatically persisted to the database. The framework handles:
- Serialization of complex data types
- Automatic type conversion for different database dialects
- Relationship management between test cases and their metrics

## Custom Metrics Persistence
Custom metrics defined in `TestCaseProperties` are automatically persisted as part of the test case:

```python
# Create a test case with custom metrics
test_case = MyPerformanceTest(
    name="Performance Test",
    scope="Performance",
    component="API",
    performance_threshold=0.5
)

# Add runtime metrics
test_case.add_custom_metric("response_time", 0.43)
test_case.add_custom_metric("error_rate", 0.02)

# Save to database
db.insert_test_case(test_case)
```

## Best Practices
1. Define all possible test metrics in `TestCaseProperties`, even if they're not always used.
2. Use descriptive names for custom metrics to enhance readability and maintainability.
3. Consider which metrics should be required vs. optional based on your testing needs.
4. Use appropriate database dialect for your environment.
5. Implement proper error handling for database operations.
6. Regularly clean up old test data to maintain database performance.