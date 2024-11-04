# Test Framework

## Overview


This Test Framework provides a flexible solution for creating, managing, and tracking test cases in Python.
It implements a clear separation between test case definitions and their executions, enabling comprehensive testing 
analysis across time. The framework supports customizable properties and metrics, allowing teams to capture and analyze 
various aspects of their test executions.

## Key Features

* Clear separation between test cases and their execution records
* Customizable test properties through `TestCaseProperties`
* Dynamic metric collection during test execution
* Flexible test case creation and management
* Support for test result tracking and reporting
* Database persistence with support for multiple database dialects
* Automatic test case serialization and deserialization
* Comprehensive logging system with step tracking
* Support multiple pytest instances for running multiple tests at the same time (xdist)

## Main Components

The `TestCase` class defines the test case structure and its metadata. It provides the foundation for test implementation
and property management.

#### Core Properties

* `id`: Unique database identifier
* `test_id`: Unique test identifier (module::function)
* `name`: Test case name
* `description`: Test case description
* `test_suite`: Test suite name

Example:

```python
class LoginTest(TestCase):
    def __init__(self):
        super().__init__(
            name="User Authentication Flow",
            description="Verify user login with 2FA",
            test_suite="Authentication"
        )
```

#### Custom Properties

Test properties are fully customizable through the `TestCaseProperties` enum. Users can define their own set of required 
and optional properties based on their testing needs.

Example property configuration:

```python
class PropertyInfo(BaseModel):
    name: str
    type: type
    required: bool

class TestCaseProperties(Enum):
    """
    Custom test case properties configuration.
    Define your own properties here with their types and requirements.
    """
    SCOPE = PropertyInfo(name="SCOPE", type=str, required=True)
    COMPONENT = PropertyInfo(name="COMPONENT", type=str, required=True)
    PRIORITY = PropertyInfo(name="PRIORITY", type=int, required=False)
    PLATFORM = PropertyInfo(name="PLATFORM", type=str, required=False)
    TEST_LEVEL = PropertyInfo(name="TEST_LEVEL", type=str, required=False)
```

Example usage with custom properties:

```python
class PaymentTest(TestCase):
    def __init__(self):
        super().__init__(
            name="Credit Card Payment",
            description="Validate credit card payment flow",
            test_suite="Payments",
            # Custom properties
            scope="E2E",
            component="Payment Gateway",
            priority=1,
            platform="Web",
            test_level="Integration"
        )
```

Alternative property configuration:

```python
class TestCaseProperties(Enum):
    AREA = PropertyInfo(name="AREA", type=str, required=True)
    MODULE = PropertyInfo(name="MODULE", type=str, required=True)
    COMPLEXITY = PropertyInfo(name="COMPLEXITY", type=int, required=True)
    TAGS = PropertyInfo(name="TAGS", type=list, required=False)

class SecurityTest(TestCase):
    def __init__(self):
        super().__init__(
            name="Authentication Token Validation",
            description="Verify JWT token validation",
            test_suite="Security",
            area="Authentication",
            module="TokenService",
            complexity=3,
            tags=["security", "tokens", "validation"]
        )
```

#### Property Validation

Properties are validated during test case creation:

```python
# Missing required property
test = TestCase(
    name="Test",
    area="Financial"  # Missing required 'MODULE' property
)  # Raises RequiredPropertyError

# Invalid property type
test = TestCase(
    name="Test",
    area="Financial",
    module="Payments",
    complexity="High"  # Should be int
)  # Raises PropertyValidationError
```

### TestExecutionRecord

The `TestExecutionRecord` class represents a single execution of a test case and tracks various execution details.

#### Core Fields

* `id`: Unique execution ID
* `test_case_id`: Reference to TestCase
* `test_run_id`: Test run identifier
* `result`: Boolean execution result
* `start_time`: Execution start timestamp
* `end_time`: Execution end timestamp
* `duration`: Test execution duration
* `failure`: Failure description (if failed)
* `failure_type`: Type of failure (if failed)
* `environment`: Test environment identifier

Example test execution:

```python
def test_payment_processing(payment_test):
    execution = TestExecutionRecord(payment_test)
    execution.start()
    
    try:
        # Test implementation
        execution.add_custom_metric("transaction_id", "tx_123")
        execution.add_custom_metric("amount", 99.99)
        execution.add_custom_metric("processing_time_ms", 234)
        
        execution.end(True)  # Success
        
    except Exception as e:
        execution.set_failure(str(e), type(e).__name__)
        execution.end(False)  # Failure
```

#### Custom Metrics

TestExecutionRecord supports various types of metrics:

```python
# Performance metrics
execution.add_custom_metric("response_time_ms", 120)
execution.add_custom_metric("memory_usage_mb", 256)

# Business metrics
execution.add_custom_metric("order_value", 129.99)
execution.add_custom_metric("items_count", 5)

# Complex data structures
execution.add_custom_metric("api_response", {
    "status_code": 200,
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    "body": {
        "order_id": "ord_789",
        "status": "completed"
    }
})

execution.add_custom_metric("validation_steps", [
    {"step": "input_validation", "status": "passed"},
    {"step": "card_verification", "status": "passed"},
    {"step": "fraud_check", "status": "passed"}
])
```

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

### Test Results
The framework supports all pytest test outcomes (besides "started") through the `TestResult` enum which are being set automatically on 
starting the test (pytest `pytest_runtest_call` hook) and when it's finished (`pytest_runtest_makereport`)
```python
class TestResult(Enum):
    STARTED = "started"     # Test just started 
    PASSED = "passed"       # Test passed successfully
    FAILED = "failed"       # Test failed
    SKIPPED = "skipped"     # Test was skipped
    XFAILED = "xfailed"     # Expected failure
    XPASSED = "xpassed"     # Unexpected pass
    ERROR = "error"         # Setup/teardown error
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

## Writing Tests

### Test Case Fixtures

Each test must be provided with a TestCase fixture to enable proper test tracking and metric collection. Without a TestCase fixture, the framework cannot track test execution or collect metrics.

### Basic Test Structure

```python
import pytest
from core.test_case import TestCase

class MyTestCase(TestCase):
    def __init__(self):
        super().__init__(
            name="Example Test",
            description="Verify example functionality",
            test_suite="Example Suite",
            scope="Integration",
            component="ExampleService"
        )

@pytest.fixture
def example_test():
    return MyTestCase()

def test_example_functionality(example_test):
    # Test implementation using example_test fixture
    example_test.add_custom_metric("start_timestamp", datetime.now().isoformat())
    # ... test implementation
```

### Missing TestCase Fixture

If a test is executed without a TestCase fixture, the framework will raise `TestNotFoundException`:

```python
def test_without_fixture():  # This will fail
    # Test implementation
    pass

# Error: TestNotFoundException: No TestCase fixture found. 
# Each test must have a TestCase fixture provided.
```

### Using Dummy Test Case

For non-production tests (e.g., framework tests, examples), you can use the provided `dummy_test_case` fixture:

```python
def test_example(dummy_test_case):
    # Test using dummy test case
    dummy_test_case.add_custom_metric("example", "value")
    assert True
```

### Custom Test Case with Specific Properties

For tests requiring specific properties, create a dedicated TestCase class:

```python
class APITestCase(TestCase):
    def __init__(self, endpoint: str):
        super().__init__(
            name=f"API Test - {endpoint}",
            description=f"Verify {endpoint} endpoint",
            test_suite="API Tests",
            scope="Integration",
            component="API",
            platform="REST",
            test_level="Integration",
            tags=["api", "endpoints"]
        )
        self.endpoint = endpoint

@pytest.fixture
def api_test():
    return APITestCase("/users")

def test_api_endpoint(api_test):
    # Test implementation
    response = requests.get(api_test.endpoint)
    api_test.add_custom_metric("status_code", response.status_code)
    api_test.add_custom_metric("response_time", response.elapsed.total_seconds())
```

### Test Case Inheritance

You can create base test cases for common scenarios:

```python
class BaseAPITest(TestCase):
    def __init__(self, name: str, endpoint: str):
        super().__init__(
            name=name,
            description=f"API test for {endpoint}",
            test_suite="API Tests",
            scope="Integration",
            component="API"
        )
        self.endpoint = endpoint

class UserAPITest(BaseAPITest):
    def __init__(self):
        super().__init__(
            name="User API Test",
            endpoint="/users"
        )

@pytest.fixture
def user_api_test():
    return UserAPITest()
```

### Test Case Best Practices

1. Always provide a TestCase fixture for each test
2. Use meaningful names and descriptions
3. Set appropriate properties based on test type
4. Create base test cases for common scenarios
5. Use dummy_test_case only for non-production tests
6. Document custom properties and their purpose

### Test Case Reuse

For similar tests, you can reuse the TestCase class with different parameters:

```python
class ParameterizedTest(TestCase):
    def __init__(self, test_name: str, parameter: str):
        super().__init__(
            name=f"{test_name} - {parameter}",
            description=f"Test with parameter: {parameter}",
            test_suite="Parameterized Tests",
            scope="Unit",
            component="ParameterizedComponent"
        )
        self.parameter = parameter

@pytest.fixture(params=["param1", "param2", "param3"])
def param_test(request):
    return ParameterizedTest("Parameterized Test", request.param)

def test_with_parameters(param_test):
    # Test implementation using param_test.parameter
    param_test.add_custom_metric("parameter", param_test.parameter)
```


## Logging System

The framework includes a flexible logging system that supports various log levels and formatting options.

### Configuration

The logging system uses a configuration file (`config/logger.ini`) that can be customized to adjust:

- Log file locations and naming patterns
- Output formatting
- Log levels visibility
- Console and file output settings

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

### Data Persistence

All test case data, including custom metrics and properties, is automatically persisted to the database. The framework
handles:

- Serialization of complex data types
- Automatic type conversion for different database dialects
- Relationship management between test cases and their custom metrics

## Configuration & Setup

### AutomationDatabaseManager

The framework provides a singleton database manager:

```python
# Initialize with configuration
AutomationDatabaseManager.initialize(config_path='config/database.yaml')

# Get database instance
db = AutomationDatabaseManager.get_database()
```

Configuration example (`database_config.yaml`):

```yaml
automation_db:
  url: "postgresql://user:pass@localhost/testdb"
  dialect: "postgresql"

dev:
  url: "sqlite:///dev.db"
  dialect: null
```

### Database Dialects Support

The framework supports multiple database systems:

```python
# PostgreSQL
db_postgres = AutomationDatabase(
    'postgresql+psycopg2://user:pass@localhost/testdb',
    dialect='postgresql'
)

# MSSQL
db_mssql = AutomationDatabase(
    'mssql+pyodbc://user:pass@server/database',
    dialect='mssql'
)

# SQLite
db_sqlite = AutomationDatabase('sqlite:///local.db')
```

## Best Practices

1. Separate test case definition from test execution logic.
2. Define meaningful custom properties in TestCaseProperties.
3. Use descriptive names for custom metrics.
4. Add metrics that provide business value and help with debugging.
5. Structure test suites logically by functionality.
6. Implement proper error handling and logging.
7. Monitor test execution trends over time.
8. Clean up old test data regularly.
9. Document custom properties and metrics.
10. Set up automated reporting based on collected metrics. See more in Appendix 1.


## Appendix 1: Deep Test History Analysis

This section provides examples of analyzing test execution data using both SQL queries and Python code. 
The examples are based on real test data collected during test executions.
You can and feed your test database with some fake data by running tests in module
`_tests/test_analytics/test_data_generation_and_analysis.py` 

### SQL Analysis Examples

#### Test Execution Statistics
```sql
-- Overall test execution statistics by test case
SELECT 
    tc.name as test_name,
    tc.test_suite,
    COUNT(*) as total_executions,
    SUM(CASE WHEN ter.result = 1 THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN ter.result = 0 THEN 1 ELSE 0 END) as failed,
    AVG(ter.duration) as avg_duration,
    MIN(ter.duration) as min_duration,
    MAX(ter.duration) as max_duration
FROM test_cases tc
JOIN test_execution_records ter ON tc.id = ter.test_case_id
GROUP BY tc.id, tc.name, tc.test_suite
ORDER BY total_executions DESC;

-- Test stability by environment
SELECT 
    tc.name,
    ter.environment,
    COUNT(*) as total_runs,
    ROUND(AVG(CASE WHEN ter.result = 1 THEN 100.0 ELSE 0 END), 2) as success_rate,
    AVG(ter.duration) as avg_duration
FROM test_cases tc
JOIN test_execution_records ter ON tc.id = ter.test_case_id
GROUP BY tc.name, ter.environment
ORDER BY success_rate DESC;
```

#### Performance Analysis
```sql
-- Performance trends over time with custom metrics
WITH performance_metrics AS (
    SELECT 
        ter.test_case_id,
        ter.start_time::date as test_date,
        ter.environment,
        AVG(CAST(cm.value->>'processing_time_ms' AS FLOAT)) as avg_response_time,
        AVG(CAST(cm.value->>'memory_usage_mb' AS FLOAT)) as avg_memory_usage
    FROM test_execution_records ter
    JOIN custom_metrics cm ON ter.id = cm.test_execution_id
    WHERE cm.name IN ('processing_time_ms', 'memory_usage_mb')
        AND ter.result = true  -- Only successful executions
    GROUP BY ter.test_case_id, test_date, ter.environment
)
SELECT 
    tc.name,
    pm.test_date,
    pm.environment,
    pm.avg_response_time,
    pm.avg_memory_usage
FROM performance_metrics pm
JOIN test_cases tc ON pm.test_case_id = tc.id
ORDER BY tc.name, pm.environment, pm.test_date;

-- Identify performance degradation
WITH daily_metrics AS (
    SELECT 
        ter.test_case_id,
        ter.environment,
        DATE_TRUNC('day', ter.start_time) as day,
        AVG(CAST(cm.value->>'processing_time_ms' AS FLOAT)) as avg_resp_time
    FROM test_execution_records ter
    JOIN custom_metrics cm ON ter.id = cm.test_execution_id
    WHERE cm.name = 'processing_time_ms'
        AND ter.result = true
    GROUP BY ter.test_case_id, ter.environment, DATE_TRUNC('day', ter.start_time)
)
SELECT 
    tc.name,
    dm.environment,
    dm.day,
    dm.avg_resp_time,
    LAG(dm.avg_resp_time) OVER (PARTITION BY tc.name, dm.environment ORDER BY dm.day) as prev_day_avg,
    ROUND(
        (dm.avg_resp_time - LAG(dm.avg_resp_time) OVER (PARTITION BY tc.name, dm.environment ORDER BY dm.day)) 
        / LAG(dm.avg_resp_time) OVER (PARTITION BY tc.name, dm.environment ORDER BY dm.day) * 100, 
        2
    ) as daily_change_percent
FROM daily_metrics dm
JOIN test_cases tc ON dm.test_case_id = tc.id
WHERE dm.avg_resp_time > LAG(dm.avg_resp_time) OVER (PARTITION BY tc.name, dm.environment ORDER BY dm.day) * 1.2  -- 20% degradation
ORDER BY tc.name, dm.environment, dm.day;
```

#### Failure Analysis
```sql
-- Common failure patterns
SELECT 
    tc.name,
    ter.environment,
    ter.failure_type,
    COUNT(*) as occurrence_count,
    MIN(ter.start_time) as first_seen,
    MAX(ter.start_time) as last_seen,
    array_agg(DISTINCT ter.failure) as error_messages
FROM test_execution_records ter
JOIN test_cases tc ON ter.test_case_id = tc.id
WHERE ter.result = false 
    AND ter.start_time > CURRENT_DATE - INTERVAL '30 days'
GROUP BY tc.name, ter.environment, ter.failure_type
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;

-- Failure correlation with custom metrics
SELECT 
    ter.failure_type,
    COUNT(*) as failures,
    AVG(CAST(cm_proc.value->>'processing_time_ms' AS FLOAT)) as avg_processing_time,
    AVG(CAST(cm_mem.value->>'memory_usage_mb' AS FLOAT)) as avg_memory_usage
FROM test_execution_records ter
JOIN custom_metrics cm_proc ON ter.id = cm_proc.test_execution_id
JOIN custom_metrics cm_mem ON ter.id = cm_mem.test_execution_id
WHERE ter.result = false
    AND cm_proc.name = 'processing_time_ms'
    AND cm_mem.name = 'memory_usage_mb'
GROUP BY ter.failure_type
ORDER BY failures DESC;
```

### Python Analysis Examples

#### Test Stability Analysis
```python
def analyze_test_stability(test_case_id: int, period_days: int = 30):
    """Analyze test stability across environments."""
    db = AutomationDatabaseManager.get_database()
    
    with db.session_scope() as session:
        executions = session.query(TestExecutionRecordModel)\
            .filter(
                TestExecutionRecordModel.test_case_id == test_case_id,
                TestExecutionRecordModel.start_time >= datetime.now() - timedelta(days=period_days)
            ).all()
        
        # Group by environment
        env_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
        perf_stats = defaultdict(list)
        
        for execution in executions:
            env = execution.environment
            env_stats[env]["total"] += 1
            env_stats[env]["passed" if execution.result else "failed"] += 1
            
            if execution.result:
                # Collect performance metrics for successful runs
                processing_time = next(
                    (m.value for m in execution.custom_metrics 
                     if m.name == 'processing_time_ms'),
                    None
                )
                if processing_time:
                    perf_stats[env].append(float(processing_time))
        
        # Calculate statistics
        for env, stats in env_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            perf_data = perf_stats[env]
            
            yield {
                "environment": env,
                "total_executions": stats["total"],
                "success_rate": success_rate,
                "avg_processing_time": np.mean(perf_data) if perf_data else None,
                "p95_processing_time": np.percentile(perf_data, 95) if perf_data else None
            }

# Usage example:
stability_data = list(analyze_test_stability(test_case_id=123))
```

#### Performance Trend Analysis
```python
def analyze_performance_trends(test_case_id: int, metric_name: str = 'processing_time_ms'):
    """Analyze performance trends over time."""
    db = AutomationDatabaseManager.get_database()
    
    with db.session_scope() as session:
        # Get execution records with metrics
        executions = session.query(
            TestExecutionRecordModel,
            CustomMetricModel
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.test_case_id == test_case_id,
            TestExecutionRecordModel.result == True,
            CustomMetricModel.name == metric_name
        ).order_by(
            TestExecutionRecordModel.start_time
        ).all()
        
        # Group by environment and calculate trends
        env_data = defaultdict(list)
        for execution, metric in executions:
            env_data[execution.environment].append({
                'timestamp': execution.start_time,
                'value': float(metric.value)
            })
        
        # Calculate trends
        trends = {}
        for env, data in env_data.items():
            values = [d['value'] for d in data]
            trends[env] = {
                'mean': np.mean(values),
                'median': np.median(values),
                'p95': np.percentile(values, 95),
                'trend_slope': np.polyfit(range(len(values)), values, 1)[0],
                'samples': len(values)
            }
        
        return trends

# Usage example:
performance_trends = analyze_performance_trends(test_case_id=123)
```

#### Failure Pattern Analysis
```python
def analyze_failure_patterns(period_days: int = 30):
    """Analyze failure patterns and correlations."""
    db = AutomationDatabaseManager.get_database()
    
    with db.session_scope() as session:
        # Get failed executions with their metrics
        failed_executions = session.query(
            TestExecutionRecordModel,
            CustomMetricModel
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.result == False,
            TestExecutionRecordModel.start_time >= datetime.now() - timedelta(days=period_days)
        ).all()
        
        # Analyze patterns
        failure_patterns = defaultdict(lambda: {
            'count': 0,
            'environments': defaultdict(int),
            'metrics': defaultdict(list)
        })
        
        for execution, metric in failed_executions:
            pattern = failure_patterns[execution.failure_type]
            pattern['count'] += 1
            pattern['environments'][execution.environment] += 1
            pattern['metrics'][metric.name].append(metric.value)
        
        # Calculate correlations
        for failure_type, pattern in failure_patterns.items():
            metrics = pattern['metrics']
            if 'processing_time_ms' in metrics and 'memory_usage_mb' in metrics:
                proc_times = [float(v) for v in metrics['processing_time_ms']]
                mem_usage = [float(v) for v in metrics['memory_usage_mb']]
                pattern['metric_correlation'] = np.corrcoef(proc_times, mem_usage)[0, 1]
        
        return dict(failure_patterns)

# Usage example:
failure_analysis = analyze_failure_patterns()
```

These analysis tools help in:
- Identifying test stability issues
- Tracking performance degradation
- Understanding failure patterns
- Comparing environments
- Setting performance baselines
- Capacity planning
- Test suite optimization

The combination of SQL and Python analysis provides flexibility in:
- Real-time monitoring
- Historical analysis
- Trend detection
- Pattern recognition
- Custom reporting